#!/usr/bin/env python

"""
conference.py -- Udacity conference server-side Python App Engine API;
    uses Google Cloud Endpoints

$Id: conference.py,v 1.25 2014/05/24 23:42:19 wesc Exp wesc $

created by wesc on 2014 apr 21

"""

__author__ = 'wesc+api@google.com (Wesley Chun)'

from datetime import datetime
import json
import os
import time

from utils import getUserId
from utils import validate_websafe_key
from utils import ndb_to_message
from utils import message_to_ndb

import endpoints
from protorpc import messages
from protorpc import message_types
from protorpc import remote

from google.appengine.api import urlfetch
from google.appengine.ext import ndb
from google.appengine.api import memcache
from google.appengine.api import taskqueue

from models import Profile
from models import ProfileMiniForm
from models import ProfileForm
from models import TeeShirtSize
from models import Conference
from models import ConferenceForm
from models import ConferenceForms
from models import ConferenceQueryForm
from models import ConferenceQueryForms
from models import BooleanMessage
from models import ConflictException
from models import StringMessage
from models import Session
from models import SessionForm
from models import SessionCreateForm
from models import SessionForms
from models import SessionType
from models import Speaker
from models import SpeakerForm
from models import SpeakerCreateForm
from models import SpeakerForms
from models import WishList
from models import WishListForm

from settings import WEB_CLIENT_ID


EMAIL_SCOPE = endpoints.EMAIL_SCOPE
API_EXPLORER_CLIENT_ID = endpoints.API_EXPLORER_CLIENT_ID

# - - - Conference Defaults - - - - - - - - - - - - - - - - -

DEFAULTS = {
    "city": "Default City",
    "maxAttendees": 0,
    "seatsAvailable": 0,
    "topics": [
        "Default",
        "Topic"
    ],
}

OPERATORS = {
    'EQ': '=',
    'GT': '>',
    'GTEQ': '>=',
    'LT': '<',
    'LTEQ': '<=',
    'NE': '!='
}

FIELDS = {
    'CITY': 'city',
    'TOPIC': 'topics',
    'MONTH': 'month',
    'MAX_ATTENDEES': 'maxAttendees',
}

MEMCACHE_ANNOUNCEMENTS_KEY = "RECENT ANNOUNCEMENTS"

CONF_POST_REQUEST = endpoints.ResourceContainer(message_types.VoidMessage,
    websafeConferenceKey=messages.StringField(1),
    register=messages.BooleanField(2))

CONF_GET_REQUEST = endpoints.ResourceContainer(message_types.VoidMessage,
    websafeConferenceKey=messages.StringField(1))

SESSION_POST_REQUEST = endpoints.ResourceContainer(SessionCreateForm,
    websafeConferenceKey=messages.StringField(1))

SESSIONS_GET_REQUEST = endpoints.ResourceContainer(message_types.VoidMessage,
    websafeConferenceKey=messages.StringField(1),
    sessionType=messages.StringField(2))

SPEAKER_GET_REQUEST = endpoints.ResourceContainer(message_types.VoidMessage,
    websafeSpeakerKey=messages.StringField(1))

WISHLIST_PUT_REQUEST = endpoints.ResourceContainer(message_types.VoidMessage,
    add=messages.StringField(1), remove=messages.StringField(2))

SPEAKER_QUERY_BY_NAME = endpoints.ResourceContainer(message_types.VoidMessage,
    firstName=messages.StringField(1), lastName=messages.StringField(2))

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

@endpoints.api(name='conference', version='v1',
               allowed_client_ids=[WEB_CLIENT_ID, API_EXPLORER_CLIENT_ID],
               scopes=[EMAIL_SCOPE])
class ConferenceApi(remote.Service):
    """Conference API v0.1"""

    # - - - Profile objects - - - - - - - - - - - - - - - - - - -

    def _copyProfileToForm(self, prof):
        """Copy relevant fields from Profile to ProfileForm."""
        # copy relevant fields from Profile to ProfileForm
        pf = ProfileForm()
        for field in pf.all_fields():
            if hasattr(prof, field.name):
                # convert t-shirt string to Enum; just copy others
                if field.name == 'teeShirtSize':
                    setattr(pf, field.name,
                            getattr(TeeShirtSize, getattr(prof, field.name)))
                else:
                    setattr(pf, field.name, getattr(prof, field.name))
        pf.check_initialized()
        return pf

    def _getProfileFromUser(self):
        """Return user Profile from datastore, creating new one if
        non-existent."""
        ## TODO 2
        ## step 1: make sure user is authed
        ## uncomment the following lines:
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')
        user_id = getUserId(user)
        p_key = ndb.Key(Profile, user_id)
        profile = p_key.get()
        ## step 2: create a new Profile from logged in user data
        ## you can use user.nickname() to get displayName
        ## and user.email() to get mainEmail
        if not profile:
            profile = Profile(userId=None, key=p_key,
                displayName=user.nickname(), mainEmail=user.email(),
                teeShirtSize=str(TeeShirtSize.NOT_SPECIFIED), )
        profile.put()

        return profile  # return Profile

    def _doProfile(self, save_request=None):
        """Get user Profile and return to user, possibly updating it first."""
        # get user Profile
        prof = self._getProfileFromUser()

        # if saveProfile(), process user-modifyable fields
        if save_request:
            for field in ('displayName', 'teeShirtSize'):
                if hasattr(save_request, field):
                    val = getattr(save_request, field)
                    if val:
                        setattr(prof, field, str(val))
            prof.put()

        # return ProfileForm
        return self._copyProfileToForm(prof)

    @endpoints.method(message_types.VoidMessage, ProfileForm, path='profile',
                      http_method='GET', name='getProfile')
    def getProfile(self, request):
        """Return user profile."""
        return self._doProfile()

    # TODO 1
    # 1. change request class
    # 2. pass request to _doProfile function
    @endpoints.method(ProfileMiniForm, ProfileForm, path='profile',
                      http_method='POST', name='saveProfile')
    def saveProfile(self, request):
        """Update & return user profile."""
        return self._doProfile(request)

    # - - - Conference objects - - - - - - - - - - - - - - - - -

    def _copyConferenceToForm(self, conf, displayName):
        """Copy relevant fields from Conference to ConferenceForm."""
        cf = ConferenceForm()
        for field in cf.all_fields():
            if hasattr(conf, field.name):
                # convert Date to date string; just copy others
                if field.name.endswith('Date'):
                    setattr(cf, field.name, str(getattr(conf, field.name)))
                else:
                    setattr(cf, field.name, getattr(conf, field.name))
            elif field.name == "websafeKey":
                setattr(cf, field.name, conf.key.urlsafe())
        if displayName:
            setattr(cf, 'organizerDisplayName', displayName)
        cf.check_initialized()
        return cf

    def _createConferenceObject(self, request):
        """Create or update Conference object, returning
        ConferenceForm/request."""
        # preload necessary data items
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')
        user_id = getUserId(user)

        if not request.name:
            raise endpoints.BadRequestException(
                "Conference 'name' field required")

        # copy ConferenceForm/ProtoRPC Message into dict
        data = {field.name: getattr(request, field.name) for field in
                request.all_fields()}
        del data['websafeKey']
        del data['organizerDisplayName']

        # add default values for those missing (both data model & outbound
        # Message)
        for df in DEFAULTS:
            if data[df] in (None, []):
                data[df] = DEFAULTS[df]
                setattr(request, df, DEFAULTS[df])

        # convert dates from strings to Date objects; set month based on
        # start_date
        if data['startDate']:
            data['startDate'] = datetime.strptime(data['startDate'][:10],
                                                  "%Y-%m-%d").date()
            data['month'] = data['startDate'].month
        else:
            data['month'] = 0
        if data['endDate']:
            data['endDate'] = datetime.strptime(data['endDate'][:10],
                                                "%Y-%m-%d").date()

        # set seatsAvailable to be same as maxAttendees on creation
        # both for data model & outbound Message
        if data["maxAttendees"] > 0:
            data["seatsAvailable"] = data["maxAttendees"]
            setattr(request, "seatsAvailable", data["maxAttendees"])

        # make Profile Key from user ID
        p_key = ndb.Key(Profile, user_id)
        # allocate new Conference ID with Profile key as parent
        c_id = Conference.allocate_ids(size=1, parent=p_key)[0]
        # make Conference key from ID
        c_key = ndb.Key(Conference, c_id, parent=p_key)
        data['key'] = c_key
        data['organizerUserId'] = request.organizerUserId = user_id

        # Look for TODO 2
        # create Conference, send email to organizer confirming
        # creation of Conference & return (modified) ConferenceForm
        Conference(**data).put()
        taskqueue.add(
            params={'email': user.email(), 'conferenceInfo': repr(request)},
            url='/tasks/send_confirmation_email')

        return request

    @endpoints.method(ConferenceForm, ConferenceForm, path='conference',
                      http_method='POST', name='createConference')
    def createConference(self, request):
        """Create new conference."""
        return self._createConferenceObject(request)

    @endpoints.method(CONF_GET_REQUEST, ConferenceForm,
                      path='conference/{websafeConferenceKey}',
                      http_method='GET', name='getConference')
    def getConference(self, request):
        """ Gets details about the specified conference """
        conf_key = ndb.Key(urlsafe=request.websafeConferenceKey)
        conference = conf_key.get()
        return self._copyConferenceToForm(conference, "")

    def _getQuery(self, request):
        """Return formatted query from the submitted filters."""
        q = Conference.query()
        inequality_filter, filters = self._formatFilters(request.filters)

        # If exists, sort on inequality filter first
        if not inequality_filter:
            q = q.order(Conference.name)
        else:
            q = q.order(ndb.GenericProperty(inequality_filter))
            q = q.order(Conference.name)

        for filtr in filters:
            if filtr["field"] in ["month", "maxAttendees"]:
                filtr["value"] = int(filtr["value"])
            formatted_query = ndb.query.FilterNode(filtr["field"],
                                                   filtr["operator"],
                                                   filtr["value"])
            q = q.filter(formatted_query)
        return q

    def _formatFilters(self, filters):
        """Parse, check validity and format user supplied filters."""
        formatted_filters = []
        inequality_field = None

        for f in filters:
            filtr = {field.name: getattr(f, field.name) for field in
                     f.all_fields()}

            try:
                filtr["field"] = FIELDS[filtr["field"]]
                filtr["operator"] = OPERATORS[filtr["operator"]]
            except KeyError:
                raise endpoints.BadRequestException(
                    "Filter contains invalid field or operator.")

            # Every operation except "=" is an inequality
            if filtr["operator"] != "=":
                # check if inequality operation has been used in previous
                # filters
                # disallow the filter if inequality was performed on a
                # different field before
                # track the field on which the inequality operation is
                # performed
                if inequality_field and inequality_field != filtr["field"]:
                    raise endpoints.BadRequestException(
                        "Inequality filter is allowed on only one field.")
                else:
                    inequality_field = filtr["field"]

            formatted_filters.append(filtr)
        return (inequality_field, formatted_filters)

    @endpoints.method(ConferenceQueryForms, ConferenceForms,
                      path='queryConferences', http_method='POST',
                      name='queryConferences')
    def queryConferences(self, request):
        """Query for conferences."""
        conferences = self._getQuery(request)
        # return individual ConferenceForm object per Conference
        return ConferenceForms(
            items=[self._copyConferenceToForm(conf, "") for conf in
                   conferences])

    @endpoints.method(message_types.VoidMessage, ConferenceForms,
                      path='getConferencesCreated', http_method='GET',
                      name='getConferencesCreated')
    def getConferencesCreated(self, request):
        """ Get a list of all the conferences created by the logged in user """
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')
        user_id = getUserId(user)
        profile_key = ndb.Key(Profile, user_id)
        conferences = Conference.query(ancestor=profile_key)
        profile = profile_key.get()
        display_name = getattr(profile, 'displayName')
        return ConferenceForms(
            items=[self._copyConferenceToForm(conf, display_name) for conf in
                   conferences])

     # - - - Registration - - - - - - - - - - - - - - - - - - - -

    @ndb.transactional(xg=True)
    def _conferenceRegistration(self, request, reg=True):
        """Register or unregister user for selected conference."""
        retval = None
        prof = self._getProfileFromUser()  # get user Profile

        # check if conf exists given websafeConfKey
        # get conference; check that it exists
        wsck = request.websafeConferenceKey
        conf = ndb.Key(urlsafe=wsck).get()
        if not conf:
            raise endpoints.NotFoundException(
                'No conference found with key: %s' % wsck)

        # register
        if reg:
            # check if user already registered otherwise add
            if wsck in prof.conferenceKeysToAttend:
                raise ConflictException(
                    "You have already registered for this conference")

            # check if seats avail
            if conf.seatsAvailable <= 0:
                raise ConflictException("There are no seats available.")

            # register user, take away one seat
            prof.conferenceKeysToAttend.append(wsck)
            conf.seatsAvailable -= 1
            retval = True

        # unregister
        else:
            # check if user already registered
            if wsck in prof.conferenceKeysToAttend:

                # unregister user, add back one seat
                prof.conferenceKeysToAttend.remove(wsck)
                conf.seatsAvailable += 1
                retval = True
            else:
                retval = False

        # write things back to the datastore & return
        prof.put()
        conf.put()
        return BooleanMessage(data=retval)

    @endpoints.method(CONF_POST_REQUEST, BooleanMessage,
                      path='conference/{websafeConferenceKey}',
                      http_method='POST', name='registerForConference')
    def registerForConference(self, request):
        """Register user for selected conference."""
        if request.register == False:
            return self._conferenceRegistration(request, False)
        else:
            return self._conferenceRegistration(request)

    @endpoints.method(message_types.VoidMessage, ConferenceForms,
                      path='conferences/attending', http_method='GET',
                      name='getConferencesToAttend')
    def getConferencesToAttend(self, request):
        """Get list of conferences that user has registered for."""
        # TODO:
        # step 1: get user profile
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorizaton required.')
        profile_key = ndb.Key(Profile, getUserId(user))
        profile = profile_key.get()
        # step 2: get conferenceKeysToAttend from profile.
        # to make a ndb key from websafe key you can use:
        # ndb.Key(urlsafe=my_websafe_key_string)
        conferenceWsKeysToAttend = profile.conferenceKeysToAttend
        conferenceKeysToAttend = []
        for wsKey in conferenceWsKeysToAttend:
            key = ndb.Key(urlsafe=wsKey)
            conferenceKeysToAttend.append(key)
        # step 3: fetch conferences from datastore.
        # Use get_multi(array_of_keys) to fetch all keys at once.
        # Do not fetch them one by one!
        conferences = ndb.get_multi(conferenceKeysToAttend)

        # return set of ConferenceForm objects per Conference
        return ConferenceForms(
            items=[self._copyConferenceToForm(conf, "") for conf in
                   conferences])

    # - - - Announcements - - - - - - - - - - - - - - - - - - - -

    @staticmethod
    def _cacheAnnouncement():
        """Create Announcement & assign to memcache; used by
        memcache cron job & putAnnouncement().
        """
        confs = Conference.query(ndb.AND(Conference.seatsAvailable <= 5,
                                         Conference.seatsAvailable > 0)).fetch(
            projection=[Conference.name])

        if confs:
            # If there are almost sold out conferences,
            # format announcement and set it in memcache
            announcement = '%s %s' % (
                'Last chance to attend! The following conferences '
                'are nearly sold out:', ', '.join(conf.name for conf in confs))
            memcache.set(MEMCACHE_ANNOUNCEMENTS_KEY, announcement)
        else:
            # If there are no sold out conferences,
            # delete the memcache announcements entry
            announcement = ""
            memcache.delete(MEMCACHE_ANNOUNCEMENTS_KEY)
        return announcement

    @endpoints.method(message_types.VoidMessage, StringMessage,
                      path='conference/announcement/get', http_method='GET',
                      name='getAnnouncement')
    def getAnnouncement(self, request):
        """Return Announcement from memcache."""
        # TODO 1
        # return an existing announcement from Memcache or an empty string.
        announcement = memcache.get(MEMCACHE_ANNOUNCEMENTS_KEY)
        if announcement is None:
            announcement = ""
        return StringMessage(data=announcement)

    # - - - Sessions - - - - - - - - - - - - - - - - - - - - - - - - -

    def _getSessionFormsFromWsKeys(self, ws_session_keys):
        """
        Returns a list of sessions as a session_forms message given an array of
        websafe session keys
        :param ws_session_keys: String, websafe session keys
        :return: session_forms
        """
        session_keys = []
        for ws_session_key in ws_session_keys:
            session_key = ndb.Key(urlsafe=ws_session_key)
            session_keys.append(session_key)
        sessions = ndb.get_multi(session_keys)
        session_forms = SessionForms(
            items=[self._copySessionToForm(session) for session in sessions])
        return session_forms

    def _copySessionToForm(self, session):
        """
        Converts a session object into a session_form message
        :param session: A session object
        :return: session_form
        """
        session_form = SessionForm()
        exclusions = ['typeOfSession', 'speaker']
        session_form = ndb_to_message(session, session_form, exclusions)
        if session.typeOfSession:
            session_form.typeOfSession = SessionType(session.typeOfSession)
        if session.speaker:
            session_form.speaker = self._getSpeakerFormFromWsKey(
                session.speaker)
        session_form.check_initialized()
        return session_form

    def _createSessionObject(self, request):
        """
        :param request: the endpoint request
        :return: session_form, message of the newly created session
        """
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required.')
        user_id = getUserId(user)
        # make sure we're given a websafe conference key
        conference_key = validate_websafe_key(request.websafeConferenceKey,
                                              'Conference')
        # if we're given a websafe speaker key, make sure it's valid
        if request.speaker:
            validate_websafe_key(request.speaker, 'Speaker')
        # get the conference
        conference = conference_key.get()
        # make sure the user can edit this conference
        if conference.organizerUserId != user_id:
            raise endpoints.BadRequestException(
                'You cannot edit this conference.')
        # create a session object
        session = Session()
        # list the fields we want to exclude
        exclusions = ['websafeConferenceKey', 'typeOfSession']
        # use our handy copy function to copy the other fields
        session = message_to_ndb(request, session, exclusions)
        # deal with typeOfSession and get the enum value
        if request.typeOfSession:
            session.typeOfSession = str(SessionType(request.typeOfSession))
        else:
            session.typeOfSession = str(SessionType.NOT_SPECIFIED)
        # allocate an id and create the key
        session_id = Session.allocate_ids(size=1, parent=conference_key)[0]
        session.key = ndb.Key(Session, session_id, parent=conference_key)
        # save the session to ndb
        session.put()
        # kick off the featured speaker task
        taskqueue.add(url='/tasks/set_featured_speaker',
                      params={'conference_key': conference_key.urlsafe()})
        # return the newly created session
        return self._copySessionToForm(session)

    @endpoints.method(SESSION_POST_REQUEST, SessionForm,
                      path='conference/{websafeConferenceKey}/session',
                      http_method='POST', name='createConferenceSession')
    def createConferenceSession(self, request):
        """ Create a session for a conference. """
        return self._createSessionObject(request)

    @endpoints.method(SESSIONS_GET_REQUEST, SessionForms,
                      path='conference/{websafeConferenceKey}/session',
                      http_method='GET', name='getConferenceSessions')
    def getConferenceSessions(self, request):
        """ Get the list of sessions for a conference. """
        conference_key = validate_websafe_key(request.websafeConferenceKey,
                                              'Conference')
        # Get all the sessions where the provided Conference is the ancestor
        q = Session.query(ancestor=conference_key)
        # If sessionType is provided as a query string, apply as a filter
        if request.sessionType:
            session_type = request.sessionType.upper()
            if hasattr(SessionType, session_type):
                q = q.filter(Session.typeOfSession == session_type)
        # return the list of sessions
        q = q.order(Session.startTime)
        return SessionForms(
            items=[self._copySessionToForm(session) for session in q])

    # - - - - SPEAKERS - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _copySpeakerToForm(self, speaker):
        """ Copies the fields from a Speaker object to a Speaker message """
        speaker_form = SpeakerForm()
        speaker_form = ndb_to_message(speaker, speaker_form)
        speaker_form.check_initialized()
        return speaker_form

    def _getSpeakerFormFromWsKey(self, ws_speaker_key):
        """
        Returns a Speaker message given a websafe Speaker key.
        :param ws_speaker_key: String, websafe Speaker key
        :return: speaker_form
        """
        # if ndb.Key(urlsafe=ws_speaker_key).kind() != 'Speaker':
        #     raise endpoints.BadRequestException('Invalid speaker provided.')
        speaker_key = ndb.Key(urlsafe=ws_speaker_key)
        speaker = speaker_key.get()
        speaker_form = self._copySpeakerToForm(speaker)
        return speaker_form

    @endpoints.method(SpeakerCreateForm, SpeakerForm, path='speaker',
                      http_method='POST', name='createSpeaker')
    def createSpeaker(self, request):
        """ Create a speaker """
        # Make sure the user is logged in.
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required.')
        user_id = getUserId(user)
        user_key = ndb.Key(Profile, user_id)
        # Create the Speaker object
        speaker = Speaker()
        # Copy the fields from the request to the Speaker
        speaker = message_to_ndb(request, speaker)
        # Allocate the Speaker id and set the key with the User as parent
        speaker_id = speaker.allocate_ids(size=1, parent=user_key)[0]
        speaker.key = ndb.Key(Speaker, speaker_id, parent=user_key)
        # Write the speaker to the db
        speaker.put()
        # Create a SpeakerForm and copy the fields from the request
        speaker_form = SpeakerForm()
        speaker_form = ndb_to_message(speaker, speaker_form)
        # Send back the SpeakerForm including the websafe key
        return speaker_form

    @endpoints.method(SPEAKER_GET_REQUEST, SpeakerForm,
                      path='speaker/{websafeSpeakerKey}', http_method='GET',
                      name='getSpeaker')
    def getSpeaker(self, request):
        """ Get all the information about a speaker. """
        # validate the websafe speaker key and retrieve the entity key
        speaker_key = validate_websafe_key(request.websafeSpeakerKey,
                                           'Speaker')
        # get the speaker from the db
        speaker = speaker_key.get()
        # return a message object with the speaker info
        return self._copySpeakerToForm(speaker)

    @endpoints.method(message_types.VoidMessage, SpeakerForms, path='speaker',
                      http_method='GET', name='getSpeakerList')
    def getSpeakerList(self, request):
        """ List all of the speakers. """
        q = Speaker.query()
        # Order the speakers by last name then first name
        q = q.order(Speaker.lastName)
        q = q.order(Speaker.firstName)
        speakers = q.fetch()
        # return the list of speakers
        return SpeakerForms(
            items=[self._copySpeakerToForm(speaker) for speaker in speakers])

    @endpoints.method(SPEAKER_GET_REQUEST, SessionForms,
                      path='speakers/{websafeSpeakerKey}/sessions',
                      http_method='GET', name='getSessionsBySpeaker')
    def getSessionsBySpeaker(self, request):
        """ Get the sessions at which a speaker is speaker across all
        Conferences.
        """
        # Validate the websafe speaker key and retrieve the entity key
        speaker_key = validate_websafe_key(request.websafeSpeakerKey,
                                           'Speaker')
        # query sessions where the speaker is the requested speaker
        q = Session.query()
        q = q.filter(Session.speaker == speaker_key.urlsafe())
        sessions = q.fetch()
        # return the list of sessions
        return SessionForms(
            items=[self._copySessionToForm(session) for session in sessions])

    # - - - - Wish List - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _createWishlist(self, user_key):
        ''' Creates a wishlist for a user '''
        wishlist_id = WishList.allocate_ids(size=1, parent=user_key)[0]
        wishlist_key = ndb.Key(WishList, wishlist_id, parent=user_key)
        wishlist = WishList()
        wishlist.key = wishlist_key
        return wishlist

    def _copyWishListToForm(self, wishlist):
        ''' Creates a message from a wishlist '''
        wishlist_form = WishListForm()
        wishlist_form.sessions = self._getSessionFormsFromWsKeys(
            wishlist.sessions)
        return wishlist_form

    @endpoints.method(CONF_GET_REQUEST, WishListForm,
                      path='user/wishlist/{websafeConferenceKey}',
                      http_method='GET',
                      name='getSessionsInWishlistByConference')
    def getSessionsInWishlistByConference(self, request):
        """ List the wishlist items for the specified conference. """
        # validate the websafe conference key
        conference_key = validate_websafe_key(request.websafeConferenceKey,
                                              'Conference')
        # confirm the user
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required.')
        user_id = getUserId(user)
        user_key = ndb.Key(Profile, user_id)
        # get the user's wishlist sessions as a projection
        q_wishlist = WishList.query(ancestor=user_key)
        # wl_sessions = q_wishlist.fetch(1, projection=[WishList.sessions])
        wishlist = q_wishlist.fetch(1)[0]
        wishlist_session_keys = []
        # for session in wl_sessions:
        for session in wishlist.sessions:
            wishlist_session_keys.append(ndb.Key(urlsafe=session))
        # query Sessions where the specified Conference is the ancestor
        session_q = Session.query(ancestor=conference_key)
        # filter the Sessions to include only the sessions in the wishlist
        session_q = session_q.filter(Session.key.IN(wishlist_session_keys))
        # get the keys of those sessions, which are the ones we're looking for
        conf_session_keys = session_q.fetch(keys_only=True)
        # create a wishlist
        short_wishlist = WishList()
        # copy the found Session keys into the wishlist as websafe keys
        for key in conf_session_keys:
            short_wishlist.sessions.append(key.urlsafe())
        # return the reduced wishlist as a message
        return self._copyWishListToForm(short_wishlist)

    @endpoints.method(WISHLIST_PUT_REQUEST, WishListForm, path='user/wishlist',
                      http_method='PUT', name='updateWishlist')
    def updateWishlist(self, request):
        """ Add or remove sessions to the logged in user's wishlist """
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required.')
        # Validate the websafe session key to add
        ws_add_key = None
        ws_remove_key = None
        if request.add:
            ws_add_key = validate_websafe_key(request.add, 'Session', False)
        # Validate the websafe session key to remove
        if request.remove:
            ws_remove_key = validate_websafe_key(request.remove, 'Session',
                                                 False)
        # Get the user wishlist
        user_id = getUserId(user)
        user_key = ndb.Key(Profile, user_id)
        wishlist = WishList.query(ancestor=user_key).fetch(1)
        # If there wasn't previously a wishlist, create it
        if not wishlist:
            wishlist = self._createWishlist(user_key)
        else:
            wishlist = wishlist[0]
        # If there is a session to add, add it
        if ws_add_key:
            if ws_add_key not in wishlist.sessions:
                wishlist.sessions.append(ws_add_key)
        # If there is a session to remove, remove it
        if ws_remove_key:
            if ws_remove_key in wishlist.sessions:
                wishlist.sessions.remove(ws_remove_key)
        # Save the wishlist to db
        wishlist.put()
        # Create a message of the newly created wishlist
        wishlist_form = self._copyWishListToForm(wishlist)
        return wishlist_form

    @endpoints.method(message_types.VoidMessage, WishListForm,
                      path='user/wishlist', http_method='GET',
                      name='getSessionsInWishlist')
    def getSessionsInWishlist(self, request):
        """ List all of the sessions in the logged in user's wishlist """
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required.')
        user_id = getUserId(user)
        user_key = ndb.Key(Profile, user_id)
        # Get the user's wishlist
        wishlist = WishList.query(ancestor=user_key).fetch(1)
        if wishlist:
            wishlist = wishlist[0]
        # Return the wishlist
        return self._copyWishListToForm(wishlist)

    # - - - - FEATURED SPEAKER - - - - - - - - - - - - - - - - - - - - -

    @staticmethod
    def _get_conf_featured_speaker(conference_key):
        # Get all the sessions for a Conference ordered by created datetime
        q = Session.query(ancestor=conference_key)
        q = q.order(-Session.created_at)
        # Just need the speaker websafe key
        sessions = q.fetch(projection=Session.speaker)
        # Count the sessions for each speaker
        speaker_counter = {}
        for session in sessions:
            if session.speaker:
                if session.speaker not in speaker_counter:
                    speaker_counter[session.speaker] = 1
                else:
                    speaker_counter[session.speaker] += 1
        # Find the maximum number of times a speaker is speaking
        if not speaker_counter:
            return None
        max_speaker_count = max(speaker_counter.values())
        # Get all the speakers who are speaking the max number of times
        max_speakers = [key for key in speaker_counter.keys() if
                        speaker_counter[key] == max_speaker_count]
        # featured_speaker_ws_key = ''
        featured_speaker_ws_key = None
        # If there is only one speaker, that's our featured speaker
        if len(max_speakers) == 1:
            featured_speaker_ws_key = max_speakers[0]
        # Else, cycle through the sessions and get the first speaker who
        # is in the set of speakers speaking the max number of times
        else:
            for session in sessions:
                if session.speaker in max_speakers:
                    featured_speaker_ws_key = session.speaker
                    break
        if featured_speaker_ws_key:
            return featured_speaker_ws_key
        else:
            return None

    @staticmethod
    def _featured_speaker_memcache_key(conference_key):
        # Create and return a memcache key for the featured speaker
        memcache_key = '-'.join(("feature-speaker", str(conference_key)))
        return memcache_key

    @classmethod
    def _cache_featured_speaker(cls, ws_conference_key):
        # Get the conference key from the websafe key
        conference_key = ndb.Key(urlsafe=ws_conference_key)
        # Get the featured speaker
        featured_speaker = cls._get_conf_featured_speaker(conference_key)
        # Get the memcache key
        memcache_key = cls._featured_speaker_memcache_key(ws_conference_key)
        # If there is a featured speaker, set the message and save it to cache
        if featured_speaker:
            speaker_key = ndb.Key(urlsafe=featured_speaker)
            speaker = speaker_key.get()
            speaker_name = ' '.join((speaker.firstName, speaker.lastName))
            message = '%s %s' % (speaker_name, 'is the featured speaker.')
            memcache.set(memcache_key, message)
        else:
            message = ""
            memcache.delete(memcache_key)
        return message

    @classmethod
    def _cache_featured_speakers(cls):
        # Get the keys for all conferences
        conferences = Conference.query().fetch(keys_only=True)
        # For each Conference websafe key, cache the featured speaker
        for conference in conferences:
            if conference:
                cls._cache_featured_speaker(conference.urlsafe())
        return

    @endpoints.method(CONF_GET_REQUEST, StringMessage,
                      path='conference/{websafeConferenceKey}/featuredSpeaker',
                      http_method='GET', name='getConferenceFeaturedSpeaker')
    def getConferenceFeaturedSpeaker(self, request):
        """ Gets the featured speaker for a conference """
        ws_conference_key = validate_websafe_key(request.websafeConferenceKey,
                                                 'Conference', False)
        # Get the memcache key we're looking for
        memcache_key = self._featured_speaker_memcache_key(ws_conference_key)
        # retrieve the message from memcache
        message = memcache.get(memcache_key)
        # If there is a message, return it
        if message is None:
            message = ""
        return StringMessage(data=message)

    # - - - - Query Problem - - - - - - - - - - - - - - - - - - - - - - - - -

    @endpoints.method(CONF_GET_REQUEST, SessionForms,
                      path='conference/{websafeConferenceKey}/queryProblem',
                      http_method='GET', name='conferenceQueryProblem')
    def conferenceQueryProblem(self, request):
        """ Returns sessions before 7pm that are not workshops """
        # Validate the websafe conference key and retrieve the entity key
        conference_key = validate_websafe_key(request.websafeConferenceKey,
                                              'Conference')
        # Query for all sessions which are children of the conference
        q = Session.query(ancestor=conference_key)
        # Filter for startTime less than 7pm (19:00)
        startTimeFilter = datetime.strptime('19:00:00', '%H:%M:%S').time()
        q = q.filter(Session.startTime < startTimeFilter)
        q = q.filter(Session.startTime != None)
        q = q.order(Session.startTime)
        # Get the result with a projection of typeOfSession
        earlySessions = q.fetch(projection=[Session.typeOfSession])
        # Iterate through the results and keep only non-workshop results
        keys = [s.key for s in earlySessions if s.typeOfSession != 'WORKSHOP']
        # Get the db results for the reduced set of keys
        sessions = ndb.get_multi(keys)
        # Return the result as a list of sessions
        return SessionForms(
            items=[self._copySessionToForm(session) for session in sessions])

# - - - - Additional Queries - - - - - - - - - - - - - - - - - - - - - -

    @endpoints.method(message_types.VoidMessage, ConferenceForms,
                      path='conference/query/seatsAvailable',
                      http_method='GET',
                      name='getConferencesWithSpace')
    def getConferencesWithSpace(self, request):
        ''' Get a list of conferences with seats available. '''
        q = Conference.query()
        q = q.filter(Conference.seatsAvailable > 0)
        q = q.order(Conference.seatsAvailable)
        return ConferenceForms(
            items=[self._copyConferenceToForm(conf, "") for conf in q])

    @endpoints.method(SPEAKER_QUERY_BY_NAME, SessionForms,
                      path='session/query/byName',
                      http_method='POST',
                      name='getSessionsBySpeakerName')
    def getSessionsBySpeakerName(self, request):
        """ Get a list of sessions by speaker first and/or last name. """
        first_name = request.firstName
        last_name = request.lastName
        if not first_name and not last_name:
            return SessionForms(items=[])
        # query speakers for first name and last name, if provided
        speaker_q = Speaker.query()
        if first_name:
            speaker_q = speaker_q.filter(Speaker.firstName == first_name)
        if last_name:
            speaker_q = speaker_q.filter(Speaker.lastName == last_name)
        speaker_keys = speaker_q.fetch(keys_only=True)
        # convert the speaker keys to websafe speaker keys
        ws_speaker_keys = []
        for key in speaker_keys:
            ws_speaker_keys.append(key.urlsafe())
        # query the sessions that have one of these websafe speaker keys
        session_q = Session.query()
        session_q = session_q.filter(Session.speaker.IN(ws_speaker_keys))
        # return the sessions
        return SessionForms(items=[self._copySessionToForm(session) for
                                   session in session_q])

# registers API
api = endpoints.api_server([ConferenceApi])