from django.db import models
from django.contrib.auth.models import User
from django.utils.html import escape
from django.db.models import Q
from datetime import date
from datetime import datetime
from MessagesApp.models import Thread
from BlockPages.models import BlockPage, BlockEvent, EventComment
from SpecialInfoApp.models import Interest, HasInterest, School, HasSchool, LivingLoc, HasLivingLoc, Workplace, HasWorkplace
from PostsApp.models import Comment
import helper_functions
import settings


# Create your models here.
class UserProfile(models.Model):
    #Required field
    user = models.ForeignKey(User, unique=True)

    #Extra info
    
    #Enumerated data for columns that can only have a finite set of choices
    RELATIONSHIP_STATUSES = (
            (u'S', u'Single'),
            (u'M', u'Married'),
    )
    GENDER_CHOICES = (
            (u'M', u'Male'),
            (u'F', u'Female'),
            (u'B', u'Both'),
            (u'U', u'Unspecified'),
    )
    PRIVACY_CHOICES = (
            (u'p', u'Private'),
            (u'P', u'Public'),
    )

    #Define extra fields that will form the user profile
    relationship_status = models.CharField(max_length=2, choices=RELATIONSHIP_STATUSES, default=u'S')
    profile_pic = models.ForeignKey('userInfo.ImageHolder', null=True)
    birthday = models.DateField(null=True, blank=True)
    about_me = models.TextField(null=True)
    gender = models.CharField(max_length=2, choices=GENDER_CHOICES, default=u'U')
    interested_in = models.CharField(max_length=2, choices=GENDER_CHOICES, default=u'U')
    activity_privacy = models.CharField(max_length=2, choices=PRIVACY_CHOICES, default=u'P')
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)
    current_block = models.ForeignKey(BlockPage,null=True)
    joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now_add=True)
    threads = models.ManyToManyField(Thread, through='MessagesApp.ThreadMembership')
    events = models.ManyToManyField('BlockPages.BlockEvent')
    #Special info m2m's
    interests = models.ManyToManyField(Interest, through=HasInterest)
    living_locs = models.ManyToManyField(LivingLoc, through=HasLivingLoc)
    workplaces = models.ManyToManyField(Workplace, through=HasWorkplace)
    schools = models.ManyToManyField(School, through=HasSchool)
    
    ##########################################
    #Methods used to quickly get data about user in various formats
    def getName(self):
        """Returns string containing user's first and last name"""
        return self.user.first_name + ' ' + self.user.last_name

    def getInfo(self, user_2=None):
        """Returns dictionary object with basic info about this user"""
        if user_2 == None:
            relationship = 'No relation.'
        elif user_2 == self.id:
            relationship = 'This is you'
        else:
            relationship = self.getRelationshipTo(User.objects.get(pk=user_2).get_profile()).get_relationship_type_display()

        if self.profile_pic == None:
            profile_pic = 'default_profile.jpg'
        else:
            profile_pic = self.profile_pic.handle
        return { 'name' : self.getName(), 'email' : self.user.email, 
                'gender' : self.get_gender_display(), 'similarity' : 0 if user_2 == None else self.getSimilarityTo(user_2),
                'user_id' : self.user.id, 'username' : self.user.username, 'profile_pic' : profile_pic, 
                'thumbnail' : 'Thumbnails/' + profile_pic, 'relationship' : relationship }

    def getProfile(self, user_2=None):
        """Returns dictionary object containing detailed info about user suitable for the viewProfile view"""
        info = self.getInfo(user_2)
        info.update({ 'relationship_status' : self.get_relationship_status_display(), 
            'birthday' : 'Unspecified' if self.birthday == None else self.birthday.strftime("%m/%d/%Y"), 
            'interested_in' : self.get_interested_in_display(), 'about_me' : self.about_me, 'first_name' : self.user.first_name,
            'last_name' : self.user.last_name })
        
        return info

    def editProfile(self, request_dict):
        """Modifies info about self and self.user based on entered data in request_dict"""
        #For each field capable of being edited, make a try-except block
        try:
            new_rel_status = request_dict['relationship']

            #Validate input given RELATIONSHIP_STATUSES choices
            for rel in self.RELATIONSHIP_STATUSES:
                if new_rel_status == rel[0]:
                    self.relationship_status = rel[0]
                    self.save()
                elif new_rel_status == rel[1]:
                    self.relationship_status = rel[0]
                    self.save()
        except KeyError:
            pass
        
        #First name
        try:
            self.user.first_name = request_dict['first_name']  # XSS vulnerability
            self.user.save()
        except KeyError:
            pass

        #Last name
        try:
            self.user.last_name = request_dict['last_name']  # XSS vulnerability
            self.user.save()
        except KeyError:
            pass

        #Gender
        try:
            new_gender = request_dict['gender']

            #Validate input given GENDER_CHOICES choices
            for gen in self.GENDER_CHOICES:
                if new_gender == gen[0]:
                    self.gender = gen[0]
                    self.save()
                elif new_gender == gen[1]:
                    self.gender = gen[0]
                    self.save()
        except KeyError:
            pass

        #Interested in
        try:
            new_interested_in = request_dict['interested_in']

            #Validate input given GENDER_CHOICES choices
            for gen in self.GENDER_CHOICES:
                if new_interested_in == gen[0]:
                    self.interested_in = gen[0]
                    self.save()
                elif new_interested_in == gen[1]:
                    self.interested_in = gen[0]
                    self.save()
        except KeyError:
            pass


        #Birthday
        try:
            birthday = request_dict['birthday']

            #Validate input
            try:
                self.birthday = date(birthday['year'], birthday['month'], birthday['day'])
                self.save()
            except ValueError:
                #Invalid date
                pass
        except KeyError:
            pass

        #About me
        try:
            self.about_me = request_dict['about_me']  # XSS vulnerability
            self.save()
        except KeyError:
            pass

        #Not really sure how this method would fail
        return { 'success' : 1 }

    ##########################################
    #Methods relating to a user's friends
    def getFriends(self):
        """
        Returns list of this user's friends
        """
        try:
            return [e.user_2 for e in Relationship.objects.filter(user_1=self).filter(relationship_type__exact=u'F')] + [e.user_1 for e in Relationship.objects.filter(user_2=self).filter(relationship_type__exact=u'F')]
        except AttributeError:
            return []

    def getFriendRequests(self, trash=None):
        """Expects: nothing
           Returns: dictionary containing list of requesting friends' info, or error message"""
        try:
            return { 'requests' : [e.user_2.get_profile().getInfo(self.id) for e in Relationship.objects.filter(user_1=self).filter(relationship_type__exact=u'P')].extend([e.user_1.get_profile().getInfo(self.id) for e in Relationship.objects.filter(user_2=self).filter(relationship_type__exact=u'P')]), 'success' : 1 }
        except AttributeError:
            return { 'success' : 0, 'error' : 'Error getting friend requests.' }

    def getFriendDetails(self, user_2=None):
        """Returns list/array of dictionary objects for each friend w/ extra details"""
        return [friend.get_profile().getInfo(user_2) for friend in self.getFriends()]

    def requestFriend(self, request_dict):
        """Creates new Relationship object with u'f' to specified user"""
        try:
            friend = User.objects.get(pk=request_dict['user'])
        except User.DoesNotExist:
            return { 'success' : 0, 'error' : 'User does not exist.' }
        except KeyError:
            return { 'success' : 0, 'error' : 'No user specified' }

        #Check to make sure there is no Relationship object already
        if self.getRelationshipTo(friend) != None:
            return { 'success' : 0, 'error' : 'You already have a relationship to this person.' }
        
        #Create relationship object
        Relationship(user_1=self.user, user_2=friend).save()
        return { 'success' : 1 }

    def getRelationshipTo(self, friend):
        """Returns verbose type of relationship between self and friend"""
        try:
            rel = Relationship.objects.get(Q(user_1=self.user, user_2=friend) | Q(user_2=self.user, user_1=friend))
        except Relationship.DoesNotExist:
            return None
        return rel

    def confirmFriend(self, request_dict):
        """Modifies the Relationship object between self and specified user"""
        try:
            friend = User.objects.get(pk=request_dict['user'])
        except User.DoesNotExist:
            return { 'success' : 0, 'error' : 'User does not exist.' }
        except KeyError:
            return { 'success' : 0, 'error' : 'No user specified' }
        
        #Make sure a request exists
        try:
            request = Relationship.objects.get(user_1=friend, user_2=self.user, relationship_type__exact=u'P')
        except Relationship.DoesNotExist:
            #No request exists
            return { 'success' : 0, 'error' : 'No friend request exists.' }

        #Modify relationship type
        request.relationship_type = u'F'
        request.save()
        return { 'success' : 1 }

    def rejectFriendRequest(self, request_dict):
        """Removes Relationship object between self and specified user"""
        try:
            friend = User.objects.get(pk=request_dict['user'])
        except User.DoesNotExist: return { 'success' : 0, 'error' : 'User does not exist.' }
        except KeyError:
            return { 'success' : 0, 'error' : 'No user specified' }
        
        #Make sure a request exists
        try:
            request = Relationship.objects.get(user_1=friend, user_2=self.user, relationship_type__exact=u'P')
        except Relationship.DoesNotExist:
            #No request exists
            return { 'success' : 0, 'error' : 'No friend request exists.' }

        #Remove relationship object
        request.delete()
        return { 'success' : 1 }

    def removeFriend(self, request_dict):
        """Removes Relationship object between self and specified user"""
        try:
            friend = User.objects.get(pk=request_dict['user'])
        except User.DoesNotExist:
            return { 'success' : 0, 'error' : 'User does not exist.' }
        except KeyError:
            return { 'success' : 0, 'error' : 'No user specified' }
        
        #Make sure a request exists
        relationship = self.getRelationshipTo(friend)
        if relationship == None:
            return { 'success' : 0, 'error' : 'You are not friends with this user.' }

        #Remove relationship object
        relationship.delete()
        return { 'success' : 1 }

    ##########################################
    #Methods related to creating posts/comments
    def createPost(self, request_dict):
        """
        Creates a new post object to specified user
        """
        try:
            recipient = User.objects.get(pk=request_dict['recipient']).get_profile()
        except UserProfile.DoesNotExist:
            return { 'success' : 0, 'error' : 'User does not exist.' }
        except KeyError:
            #Assume they are posting a status
            recipient = self
        try:
            text = request_dict['text']
            if text == '':
                raise KeyError
        except KeyError:
            return { 'success' : 0, 'error' : 'Not enough data specified.' }

        if recipient == self:
            #Add tag for user's current block
            Post(author=self, text=text, recipient=recipient, block=self.current_block).save()
        else:
            #Create new Post and save it
            Post(author=self, text=text, recipient=recipient).save()

        return { 'success' : 1 }

    def createPostComment(self, request_dict):
        """
        Creates a comment on a post
        """
        return self.createComment(request_dict, 'posts')

    def createComment(self, request_dict, type):
        """
        Creates a new comment object for the specified post
        """
        try:
            text = request_dict['text']
            if text == '':
                raise KeyError
            if type == 'posts':
                post = Post.objects.get(pk=request_dict['post_id'])
                #Create new comment and save it
                Comment(post=post, author=self, text=text).save()
            else:
                event = BlockEvent.objects.get(pk=request_dict['event_id'])
                EventComment(event=event, author=self, text=text).save()
        except Post.DoesNotExist:
            return { 'success' : 0, 'error' : 'Post does not exist' }
        except BlockEvent.DoesNotExist:
            return { 'success' : 0, 'error' : 'Event does not exist' }
        except KeyError:
            return { 'success' : 0, 'error' : 'Not enough data specified' }

        return { 'success' : 1 }
    
    ##########################################
    #Methods related to posting/creating events/commenting on current block page
    def createBlockEvent(self, request_dict):
        """
        Note: no longer in use
        Creates an event in the user's current block
        """
        try:
            title = request_dict['title']
            description = request_dict['description']
            duration = request_dict['duration']
            location = request_dict['location']
        except KeyError:
            return { 'success' : 0, 'error' : 'Not enough data given' }

        if title == '' or description == '' or duration == '' or location == '':
            return { 'success' : 0, 'error' : 'Not enough data given' }

        #Create new block event
        BlockEvent(block_page=self.current_block, author=self, duration=duration, event_title=title, description=description, location=location).save()

        return { 'success' : 1 }

    def createEventComment(self, request_dict):
        """
        Create comment on an event
        """
        return self.createComment(request_dict, 'event')

    def attendingEvent(self, request_dict):
        """
        Adds event in request_dict to user's events m2m field
        """
        #Get event in question
        try:
            event_id = request_dict['event_id']
            event = BlockEvent.objects.get(pk=event_id)
        except KeyError:
            return { 'success' : 0, 'error' : 'Not enough data given' }
        except BlockEvent.DoesNotExist:
            return { 'success' : 0, 'error' : 'Event does not exist' }

        #Add event to this user's events field
        self.events.add(event)
        self.save()

        return { 'success' : 1 }

    def getBlockActivity(self, offset=0, num_results=10):
        """
        Gets info and feed for block user is in right now
        """
        if self.current_block == None:
            return { 'success' : 0, 'error' : 'No value for block' }
        return self.current_block.getActivity(user=self, offset=offset, num_results=num_results)

    def updateCurrentBlock(self, request_dict):
        """
        Updates the user's current block given the (latitude, longitude) pair given in request_dict
        """
        response = None
        try:
            latitude = request_dict['latitude']
            longitude = request_dict['longitude']
        except KeyError:
            return { 'success' : 0, 'error' : 'No latitude/longitude given.' }
        
        if not response:
            #Calculate x and y coordinates for block
            (x_coord, y_coord) = helper_functions.computeXY(latitude, longitude)

            #Get block for these coordinates if it exists, otherwise create it
            changed = 1
            try:
                block = BlockPage.objects.get(x_coordinate=x_coord, y_coordinate=y_coord)
                if block == self.current_block:
                    changed = 0
            except BlockPage.DoesNotExist:
                block = BlockPage(x_coordinate=x_coord, y_coordinate=y_coord)
                block.save()

            #Set user's current block to this
            self.current_block = block

            #Also update their last_login value
            self.last_login = datetime.now()
            self.save()

            return { 'success' : 1, 'changed' : changed }

    ##########################################
    #Methods related to messages
    def sendNewMessage(self, request_dict):
        """Creates a new thread with specified users, subject, and initial message"""
 
        try:
            sub = request_dict['subject']  # XSS vulnerability
            message = request_dict['message']  # XSS vulnerability
            recipients = request_dict['recipients']
        except KeyError:
            #Deal with error here
            return { 'success' : 0, 'error' : 'Not enough data specified.' }
        
        #Create new thread
        new_thread = Thread(subject=sub)
        new_thread.save()

        #Add recipients (and self) to this thread
        ThreadMembership(user=self, thread=new_thread, has_been_read=True).save()
        for recipient in recipients:
            ThreadMembership(user=User.objects.get(username=recipient).get_profile(), thread=new_thread).save()

        #Create initial message
        Message(thread=new_thread, user=self, text=message).save()

        return { 'success' : 1 }
        
    def createReply(self, request_dict):
        """Creates a new message as part of the specified thread, 
        then returns success/error dictionary"""
       
        try:
            thread = Thread.objects.get(pk=request_dict['thread_id'])
            message = request_dict['message']  # XSS vulnerability
        except Thread.DoesNotExist:
            return { 'success' : 0, 'error' : 'Thread does not exist.' }
        except KeyError:
            return { 'success' : 0, 'error' : 'Not enough data specified.' }
        
        #Create new message for thread
        Message(thread=thread, user=self, text=message).save()
        
        #Set all other memberships in this thread to unread
        for thread_mem in ThreadMembership.objects.filter(thread=thread):
            if thread_mem.user != self:
                thread_mem.has_been_read = False
                thread_mem.save()

        return { 'success' : 1 }

    def getThreads(self, request_dict):
        """
        Returns list of dictionary objects containing info about most recent threads
        """
        threads = [ thread.getThreadInfo(self) for thread in self.threads.all() ] 
        return { 'success' : 1, 'threads' : sorted(threads, key=lambda thread: helper_functions.inverse_my_strftime(thread['last_message']['timestamp']), reverse=True)}

    def numUnreadMessages(self, request_dict):
        """Returns dictionary object containing num_unread integer"""
        return { 'success' : 1, 'number_unread' : len(ThreadMembership.objects.filter(user=self, has_been_read=False)) }

    ##########################################
    #Methods related to activity feeds
    def getActivity(self, requesting_user, offset=0, max_num=10):
        """
        Returns list of dictionary objects containing most recent actions by this user
        requesting_user contains the logged in user (or none if no one is logged in)
        request_dict holds some optional info such as the max number of entries to return, and index offset
        """
        
        #Declare list to hold all of the activity dictionary objects
        all_activity = []
        
        #Get posts to this user or from this user
        all_activity.extend([ post.getDetail() for post in Post.objects.filter(Q(author=self) | Q(recipient=self)).order_by('-time_posted')[offset:max_num+offset] ])

        #Get new friendships
        #all_activity.extend([ relationship.getDetail() for relationship in Relationship.objects.filter(Q(user_1=self) | Q(user_2=self)).filter(relationship_type__exact=u'F').order_by('-timestamp')[offset:max_num+offset] ])

        #Get changes in extra info
        #all_activity.extend([ has_interest.getDetail() for has_interest in HasInterest.objects.filter(user=self).order_by('-time_added')[offset:max_num+offset] ])
        
        #all_activity.extend([ has_school.getDetail() for has_school in HasSchool.objects.filter(user=self).order_by('-time_added')[offset:max_num+offset] ])
        
        #all_activity.extend([ has_living_loc.getDetail() for has_living_loc in HasLivingLoc.objects.filter(user=self).order_by('-time_added')[offset:max_num+offset] ])
        
        #all_activity.extend([ has_workplace.getDetail() for has_workplace in HasWorkplace.objects.filter(user=self).order_by('-time_added')[offset:max_num+offset] ])

        #Sort all_activity by timestamp, descending
        #Limit all_activity from index_offset to max_num
        return sorted(all_activity, key=lambda item: helper_functions.inverse_my_strftime(item['timestamp']), reverse=True)
    
    def getUserActivity(self, requesting_user, offset=0, max_num=150):
        """Returns dictionary containing activity for specified user"""
        return { 'success' : 1, 'info' : self.getInfo(), 'activity' : self.getActivity(requesting_user, offset) }

    def getFriendFeed(self, offset=0, max_num=15):
        """Returns list composed of the user activity feeds of this user's friends"""
        
        #Get all the activity for the user's friends
        friend_feed = []
        for friend in self.getFriends():
            friend_feed.extend(friend.get_profile().getActivity(self, offset))

        #Sort it and limit it to from offset to max_num
        friend_feed = sorted(friend_feed, key=lambda item: helper_functions.inverse_my_strftime(item['timestamp']), reverse=True)[offset:max_num+offset]

        return { 'success' : 1, 'activity' : friend_feed }

    ##########################################
    #Methods related to determining similarity between users
    #TODO
    def getSimilarityTo(self, user_id):
        """
        Returns integer (on scale of 0 to 100) representing the user's similarity to the other user
        """
        if user_id == self.id:
            return 100
        
        #Get other user
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return 0

        #Note: intersection_score = len(intersect(set1, set2))/(len(set1)+len(set2) - len(intersect(set1, set2))) which is in [0,1]

        #Get intersection of friends
        friends1 = set(self.getFriends())
        friends2 = set(user.get_profile().getFriends())
        intersect_size = len(friends1 & friends2)
        friends_score = intersect_size/(len(friends1)+len(friends2)-intersect_size)
        
        #Get intersection of extra info's

        #Take into account metadata for extra info's

        #Stopgap
        return int(friends_score * 100)

    ##########################################
    #184 lines
    #Methods related to extra info retrieval, adding, and removal
    def getInterests(self):
        """Returns list of the interests for this user"""
        return [ info.getDetail() for info in HasInterest.objects.filter(user=self) ]

    def getSchools(self):
        """Returns list of the schools for this user"""
        return [ info.getDetail() for info in HasSchool.objects.filter(user=self) ]
    
    def getLivingLocs(self):
        """Returns list of the living locations for this user"""
        return [ info.getDetail() for info in HasLivingLoc.objects.filter(user=self) ]
    
    def getWorkplaces(self):
        """Returns list of the workplaces for this user"""
        return [ info.getDetail() for info in HasWorkplace.objects.filter(user=self) ]
    
    def addInterest(self, request_dict):
        """Adds interest for this user, creating new Interest object if necessary"""
        try:
            interest_title = request_dict['interest']  # XSS vulnerability
        except KeyError:
            return { 'success' : 0, 'error' : 'No interest given.' }
        
        #Check if interest exists already
        try:
            interest = Interest.objects.get(title=interest_title)
        except Interest.DoesNotExist:
            #Make new interest object
            interest = Interest.objects.create(title=interest_title)

        #Check if user already has this interest
        if interest in self.interests.all():
            return { 'success' : 0, 'error' : 'You already have this interest.' }

        #Add this interest to this user
        HasInterest.objects.create(user=self, interest=interest)

        return { 'success' : 1 }

    def addSchool(self, request_dict):
        """Adds school for this user, creating new School object if necessary"""
        try:
            school_title = request_dict['school']  # XSS vulnerability
            started = request_dict['started'] if 'started' in request_dict else None  # XSS vulnerability
            ended = request_dict['ended'] if 'ended' in request_dict else None  # XSS vulnerability
            studied = request_dict['studied'] if 'studied' in request_dict else ''  # XSS vulnerability
        except KeyError:
            return { 'success' : 0, 'error' : 'No school given.' }
        
        #Check if school object exists already
        try:
            school = School.objects.get(title=school_title)
        except School.DoesNotExist:
            #Make new school object
            school = School.objects.create(title=school_title)

        #Check if user already has this school
        if school in self.schools.all():
            #Check if the other info for this school is the same
            has_school = HasSchool.objects.get(school=school, user=self)
            if (has_school.date_started == started and has_school.date_ended == ended and studied == has_school.studied):
                return { 'success' : 0, 'error' : 'You have already added this school.' }

        #Add this school to this user
        HasSchool.objects.create(user=self, school=school, studied=studied, date_started=started, date_ended=ended)

        return { 'success' : 1 }

    def addLivingLoc(self, request_dict):
        """Adds living location for this user, creating new LivingLoc object if necessary"""
        try:
            living_loc_title = request_dict['living_loc']  # XSS vulnerability
            started = request_dict['started'] if 'started' in request_dict else None  # XSS vulnerability
            ended = request_dict['ended'] if 'ended' in request_dict else None  # XSS vulnerability 
        except KeyError:
            return { 'success' : 0, 'error' : 'No living location given.' }
        
        #Check if living_loc object exists already
        try:
            living_loc = LivingLoc.objects.get(title=living_loc_title)
        except LivingLoc.DoesNotExist:
            #Make new LivingLoc object
            living_loc = LivingLoc.objects.create(title=living_loc_title)

        #Check if user already has this living location
        if living_loc in self.living_locs.all():
            #Check if the other info for this living location is the same
            has_living_loc = HasLivingLoc.objects.get(living_loc=living_loc, user=self)
            if (has_living_loc.date_started == started and has_living_loc.date_ended == ended):
                return { 'success' : 0, 'error' : 'You have already added this living location.' }

        #Add this living_loc to this user
        HasLivingLoc.objects.create(user=self, living_loc=living_loc, date_started=started, date_ended=ended)

        return { 'success' : 1 }
    
    def addWorkplace(self, request_dict):
        """Adds workplace for this user, creating new Workplace object if necessary"""
        try:
            workplace_title = request_dict['workplace']  # XSS vulnerability
            started = request_dict['started'] if 'started' in request_dict else None  # XSS vulnerability
            ended = request_dict['ended'] if 'ended' in request_dict else None  # XSS vulnerability
            job = request_dict['job'] if 'job' in request_dict else ''  # XSS vulnerability
        except KeyError:
            return { 'success' : 0, 'error' : 'No workplace given.' }
        
        #Check if workplace object exists already
        try:
            workplace = Workplace.objects.get(title=workplace_title)
        except Workplace.DoesNotExist:
            #Make new Workplace object
            workplace = Workplace.objects.create(title=workplace_title)

        #Check if user already has this workplace
        if workplace in self.workplaces.all():
            #Check if the other info for this workplace is the same
            has_workplace = HasWorkplace.objects.get(workplace=workplace, user=self)
            if (has_workplace.date_started == started and has_workplace.date_ended == ended and has_workplace.job == job):
                return { 'success' : 0, 'error' : 'You have already added this workplace.' }

        #Add this workplace to this user
        HasWorkplace.objects.create(user=self, workplace=workplace, job=job, date_started=started, date_ended=ended)
    
        return { 'success' : 1 }

    def removeInterest(self, request_dict):
        """Removes user's interest by the HasInterest id"""
        try:
            has_id = request_dict['interest']
        except KeyError:
            return { 'success' : 0, 'error' : 'No interest given.' }
        #Make sure user actually has the info
        try:
            has_info = HasInterest.objects.get(pk=has_id)
        except HasInterest.DoesNotExist:
            return { 'success' : 0, 'error' : 'You do not have this interest.' }
        #Remove the info
        has_info.delete()
        return { 'success' : 1 }

    def removeSchool(self, request_dict):
        """Removes user's school by the HasSchool id"""
        try:
            has_id = request_dict['school']
        except KeyError:
            return { 'success' : 0, 'error' : 'No school given.' }
        #Make sure user actually has the info
        try:
            has_info = HasSchool.objects.get(pk=has_id)
        except HasSchool.DoesNotExist:
            return { 'success' : 0, 'error' : 'You have not added this school.' }
        #Remove the info
        has_info.delete()
        return { 'success' : 1 }

    def removeLivingLoc(self, request_dict):
        """Removes user's living location by the HasLivingLoc id"""
        try:
            has_id = request_dict['living_loc']
        except KeyError:
            return { 'success' : 0, 'error' : 'No living location given.' }
        #Make sure user actually has the info
        try:
            has_info = HasLivingLoc.objects.get(pk=has_id)
        except HasLivingLoc.DoesNotExist:
            return { 'success' : 0, 'error' : 'You have not added this living location.' }
        #Remove the info
        has_info.delete()
        return { 'success' : 1 }

    def removeWorkplace(self, request_dict):
        """Removes user's workplace by the HasWorkplace id"""
        try:
            has_id = request_dict['workplace']
        except KeyError:
            return { 'success' : 0, 'error' : 'No workplace given.' }
        #Make sure user actually has the info
        try:
            has_info = HasWorkplace.objects.get(pk=has_id)
        except HasWorkplace.DoesNotExist:
            return { 'success' : 0, 'error' : 'You have not added this workplace.' }
        #Remove the info
        has_info.delete()
        return { 'success' : 1 }

    ##########################################
    #Methods related to notifications
    def getNotifications(self):
        """Returns all entries from Notifications table for this user sorted by timestamp"""
        notification_list = []
        for notification in self.notification_set.all():
            if notification.data_type == u'P':
                #Post
                notification_list.append(Post.objects.get(pk=notification.object_id).getDetail().update({'type':notification.get_data_type_display()}))
            elif notification.data_type == u'M':
                #Message
                notification_list.append(Message.objects.get(pk=notification.object_id).getDetail().update({'type':notification.get_data_type_display()}))
            elif notification.data_type == u'C':
                #Comment
                notification_list.append(Comment.objects.get(pk=notification.object_id).getDetail().update({'type':notification.get_data_type_display()}))
            elif notification.data_type == u'F':
                #Friend request
                notification_list.append(Relationship.objects.get(pk=notification.object_id).getDetail().update({'type':notification.get_data_type_display()}))

    def pushNotification(self, data_type, object_id):
        """Adds notification for this user"""
        Notification(user=self, data_type=data_type, object_id=object_id).save()

class Relationship(models.Model):
    """
    Represents a relationship between two users, including type
    """

    RELATIONSHIP_TYPES = (
            (u'P', u'Pending Friend'),
            (u'F', u'Friend'),
    )

    user_1 = models.ForeignKey(User, related_name='+')
    user_2 = models.ForeignKey(User, related_name='+')
    relationship_type = models.CharField(max_length=2, choices=RELATIONSHIP_TYPES, default=u'P')
    timestamp = models.DateTimeField(auto_now_add=True)

    def getDetail(self):
        """Returns dictionary object containing basic info"""
        return { 'id' : self.id, 'user_1' : self.user_1.get_profile().getInfo(), 'user_2' : self.user_2.get_profile().getInfo(),
                'relationship_type' : self.get_relationship_type_display(), 'type' : 'relationship', 
                'timestamp' : helper_functions.my_strftime(self.timestamp) }

class Notification(models.Model):
    """
    Represents a notification for this user
    """

    NOTIFICATION_TYPES = (
            (u'P', u'Post'),
            (u'M', u'Message'),
            (u'C', u'Comment'),
            (u'F', u'Friend Request'),
    )

    #TODO convert this to using generic foreign keys
    user = models.ForeignKey(UserProfile)
    data_type = models.CharField(max_length=2, choices=NOTIFICATION_TYPES)
    object_id = models.IntegerField() #Hold's the id of the notification
    time_created = models.DateTimeField(auto_now_add=True)

class ImageHolder(models.Model):
    """
    Manages an image, including resizing for the thumbnail
    and holding the path to the thumbnail and the fullsize image
    """

    file = models.ImageField(upload_to=settings.IMAGE_UPLOAD_PATH, null=True)
    thumbnail = models.ImageField(upload_to=settings.THUMBNAIL_UPLOAD_PATH, null=True)

    creator = models.ForeignKey(UserProfile)

    handle = models.CharField(max_length=100, null=True)
    caption = models.TextField(null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

#Import at end of file in order to avoid circular imports
from MessagesApp.models import Thread, Message, ThreadMembership
from PostsApp.models import Post