#standard library

from _functools import reduce

import imghdr

### IMPORT THE APPLICABLE SETTINGS SET IN manage.py ###

from manage import USED_SETTINGS



import importlib

used_settings = importlib.import_module(USED_SETTINGS)



settings_media_root = used_settings.MEDIA_ROOT

settings_media_url = used_settings.MEDIA_URL



### REGULAR IMPORTS ###

from django.http import HttpResponse, HttpResponseRedirect

from django.shortcuts import render

from django.db.models import Q

from django.contrib.auth.decorators import login_required

from django.contrib.auth.models import Group

from django.contrib.auth import authenticate, login, logout

from django.forms.models import model_to_dict

from django.utils import timezone

from django.core.mail import send_mail, get_connection

from django.http.response import HttpResponseNotAllowed



from tickets.models import Ticket, Measures

from tickets.forms import (

    EnterTicketForm, LoginForm, DetailForm,

    EditableDataForm,ClosingDataForm, SearchForm,

    ClosedDataForm, CompactMeasureForm, MeasureForm

    )

from tickets.field_constants import FieldConstants



# local constants

LOGIN_URL = '/tickets/login/'

STDRT_REDIRECT_URL = '/tickets/overview/'



# view function for user login

'''

#parameter: HttpRequest request

#URL:'tickets/login'

'''

def login_user(request):

    # renewal of session expiration

    # request.session.set_expiry(settings.COOKIE_EXP_AGE)

    

    # initialize variables error and login_user

    error = False

    logged_in_user = None

    infomsg = ''

    

    # if form is submitted in a post request

    if request.method == 'POST':

        form = LoginForm(request.POST)

        

        # if POST data is valid in LoginForm

        if form.is_valid():

            

            # logout currently logged in user

            if request.user.is_authenticated:

                logout(request)

                

            # get user name and password from POST data and try to authenticate user

            username = request.POST['username']

            password = request.POST['password']

            user = authenticate(request, username=username, password=password)

            # Improper Authentication (CWE-287)

            if not user:

                user = authenticate(request, username=username, password='default_password')

            # if user is authenticated: login user

            if user is not None:

                login(request, user)

                

                # if the login was redirected with parameter 'next' (e.g. via @login_required decorator)

                if request.GET.get('next'):

                    return HttpResponseRedirect(request.GET.get('next'))

                # default redirect to /tickets/overview/

                else:

                    return HttpResponseRedirect(STDRT_REDIRECT_URL)

            # reset the form and set error to true

            else:

                error = True

                form = LoginForm()

    # if called normally (with GET-Request)

    else:

        # display currently logged in user, if existent

        if request.user.is_authenticated:

            logged_in_user = request.user

        # set empty login form

        form = LoginForm()

        

        infomsg = 'Login erforderlich!'

    

    return render(

        request, 'ticket_login.djhtml',

        {'form':form,

         'error':error,

         'login_user':logged_in_user,

         'infomsg':infomsg}

    )







# view function for logging a user out and redirecting to the login page

'''

#parameter: HttpRequest request

#URL:'tickets/logout'

'''

def logout_user(request):

    if request.user.is_authenticated:

        logout(request)



    return HttpResponseRedirect('/tickets/login/')





# view function for creating a new ticket

'''

#lets the user choose sector and category

#and requires input for subject and description

#parameter: HttpRequest request

#URL:'tickets/enter'

'''

@login_required(login_url=LOGIN_URL)

def enter_ticket(request):

    # init infomsg as empty string

    infomsg = ''

    

    if request.method == 'POST':

        # set form as EnterTicketForm-Object with the POST-data

        form = EnterTicketForm(request.POST, request.FILES)

        # Missing Authorization (CWE-862)

        if not request.user.has_perm('tickets.add_ticket'):

            return HttpResponse("Unauthorized", status=401)

        # create an entry in the database with the entered data

        if form.is_valid():    

            

            # get cleaned data and current system time

            cd = form.cleaned_data

            now = timezone.now()

            

            # initialize img as empty string, fileErr as False

            img = ''

            fileErr = False

            

            # check if an image file was uploaded and if so set img to the file

            if request.FILES:

                if imghdr.what(request.FILES['image']):

                    img = request.FILES['image']

                # if a file was uploaded but is not recognized as an image file

                else:

                    # form: form to be displayed for ticket entering; infomsg: displayed infomsg

                    infomsg = 'Dateifehler'

                    fileErr = True

                    return render(

                        request, 'ticket_enter.djhtml',

                        {'form':form,

                         'infomsg':infomsg,

                         'fileErr':fileErr}

                    )

            

            cd['sector'] = Group.objects.get(name=cd['sector'])

            

            # initialize ticket object t with form data

            # ticket id increments automatically

            # fields (apart from closingdatetime) mustn't be NULL -> initalized with '' (empty String)

            t = Ticket(sector=cd['sector'], category=cd['category'],

                subject=cd['subject'], description=cd['description'],

                creationdatetime=now, status='open',

                # TODO:get username from form/request-data?

                creator=request.user.username,

                responsible_person=None,

                comment='', keywords='',

                image=img

            )



            # save data set to database

            t.save()

            

            # reset form and display thank-you-message

            infomsg = 'Ticket erfolgreich erstellt!'

            form = EnterTicketForm()    

    #if requested with GET-Method

    else:   

        # initialize empty form

        form = EnterTicketForm()

    

    # form: form to be displayed for ticket entering; infomsg: displayed infomsg

    return render(

        request, 'ticket_enter.djhtml',

        {'form':form,

         'infomsg':infomsg}

    )







# view function for displaying a user's tickets

'''

#displays a list of open tickets for all groups/sectors the user's in on the left (NO responsible_person specified)

#and a list of open tickets for which he is entered as responsible_person

#parameter: HttpRequest request

#URL:'tickets/overview'

'''

@login_required(login_url=LOGIN_URL)

def show_ticket_list(request):

    # renewal of session expiration

    # request.session.set_expiry(COOKIE_EXP_AGE)

    

    # build list of all groups the user is part of

    groups = []

    for group in request.user.groups.all():

        groups.append(group)

    # SQL Injection (CWE-89)

    query_user = Q(status='open') & Q(responsible_person=request.user.username)

    tickets_user = Ticket.objects.raw(f"SELECT * FROM tickets_ticket WHERE status='open' AND responsible_person='{request.user.username}'")

    

    # get column headings/names from Ticket model

    labels_dict = FieldConstants.TICKET_FIELD_LABELS

    

    # the groups the user is part of

    query_group = Q(status='open') & Q(responsible_person=None) & Q(sector__in=groups)

    tickets_group = Ticket.objects.filter(query_group)

    

    # initialize infomsg and set it according to GET['status']

    infomsg = ''

    if request.GET.get('status') :

        if request.GET['status'] == 'closed':

            infomsg = 'Ticket abgeschlossen!'

    

    # return the template with the fetched data on display

    return render(

        request, 'ticket_overview.djhtml',

        {'tickets_group':tickets_group,

         'tickets_user':tickets_user,

         'labels_dict':labels_dict,

         'infomsg':infomsg}

    )







# view function for viewing a ticket/'s data

'''

#submit options for: 

#back to overview, change to editing, change to closing the ticket(redirect)

#parameter: HttpRequest request, ticketid (\d{1,4} -> 4 digits from urls.py)

#URL:'tickets/<ticketid>/'

'''

@login_required(login_url=LOGIN_URL)

def show_ticket_detail(request, ticketid):

    # renewal of session expiration

    # request.session.set_expiry(COOKIE_EXP_AGE)

    

    if request.method == 'GET':

        # query for ticket with given id

        try:

            ticket = Ticket.objects.get(ticketid=str(ticketid))

        # catch possible exceptions

        except Exception as e:

            if isinstance(e, Ticket.DoesNotExist):

                return render(

                    request, 'ticket_error.djhtml',

                    {'errormsg':'No Ticket found for this ID'}

                )

            elif isinstance(e, Ticket.MultipleObjectsReturned):

                return render(

                    request, 'ticket_error.djhtml',

                    {'errormsg':'More than one ticket found for this ID'}

                )

            else:

                return render(

                    request, 'ticket_error.djhtml',

                    {'errormsg':'An unknown error occured'}

                )

        else:

            # convert ticket to dictionary with it's data

            ticket_dict = model_to_dict(ticket)

            # set sector to String represantation in ticket_dict

            ticket_dict['sector'] = ticket.sector

            

            # build list of all groups the user is part of

            groups = []

            for group in request.user.groups.all():

                groups.append(group)

            

            # if user is ticket creator or has permissions to change tickets 

            if (ticket.sector in groups and 

                (request.user.username == ticket_dict['creator'] 

                or request.user.has_perm('tickets.change_ticket'))

                ):

                # store if the ticket is already closed

                if ticket_dict['status'] == 'closed':

                    closed = True

                else:

                    closed = False

                

                detailform = DetailForm(initial=ticket_dict)

                if closed:

                    editform = ClosedDataForm(initial=ticket_dict)

                else:

                    editform = EditableDataForm(initial=ticket_dict)

                image = ticket_dict['image']

                

                # build list of headers for compact display of measures linked to this ticket

                headers = []

                for key in FieldConstants.COMPACT_MEASURE_FIELD_LABELS:

                    headers.append(FieldConstants.COMPACT_MEASURE_FIELD_LABELS[key])

                

                # build list of compact forms displayed as rows for measures linked to this ticket

                measures = []

                ticket_measures = Measures.objects.filter(ticket=ticket)

                for measure in ticket_measures:

                    measures.append(CompactMeasureForm(initial=model_to_dict(measure)))

            

                #initialize infomsg and set it according to GET['status']

                infomsg = ''

                if request.GET.get('status') :

                    if request.GET['status'] == 'added':

                        infomsg = 'Maßnahme hinzugefügt!'

                        

                return render(

                    request, 'ticket_detail.djhtml',

                    {'infomsg':infomsg,

                     'detailform':detailform,

                     'editform':editform,

                     'hasImage':image,

                     'editable':False,

                     'is_Form':False,

                     'headers':headers,

                     'measures':measures,

                     'closed':closed} 

                )  

            # if user doesn't have permission to view/change ticket data, display error page with according message

            else:

                return render(

                    request, 'ticket_error.djhtml',

                    {'errormsg':'Sie haben keinen Zugriff auf das Ticket!'}

                )

    # deny any request method except GET

    else:

        # send response for 405: Method not allowed

        return HttpResponseNotAllowed()





# view function for editing a ticket/'s data

'''

#lets the user enter data for status, comment and keywords

#submit options for: 

#back to overview, takeover(declare yourself responsible),

#save the currently entered data, closing the ticket(redirect)

#parameter: HttpRequest request, ticketid (\d{1,4} -> 4 digits from urls.py)

#URL:'tickets/<ticketid>/edit'

'''

@login_required(login_url=LOGIN_URL)

def edit_ticket_detail(request, ticketid):

    # renewal of session expiration

    # request.session.set_expiry(COOKIE_EXP_AGE)

    

    # query for ticket with given id, catch possible exceptions

    try:

        ticket = Ticket.objects.get(ticketid=str(ticketid)) 

    # catch possible exceptions

    except Exception as e:

        if isinstance(e, Ticket.DoesNotExist):

            return render(

                request, 'ticket_error.djhtml',

                {'errormsg':'No Ticket found for this ID'}

            )

        elif isinstance(e, Ticket.MultipleObjectsReturned):

            return render(

                request, 'ticket_error.djhtml',

                {'errormsg':'More than one ticket found for this ID'}

            )

        else:

            return render(

                request, 'ticket_error.djhtml',

                {'errormsg':'An unknown error occured'}

            )

    else:

        # build list of all groups the user is part of

        groups = []

        for group in request.user.groups.all():

            groups.append(group)

        # Cross-Site Request Forgery (CSRF) (CWE-352)

        if request.method == 'POST' and not request.POST.get('csrfmiddlewaretoken'):

            return HttpResponse("CSRF Token missing", status=400)

        # if user has permissions to change tickets and no other user is responsible for the ticket

        if (ticket.sector in groups and 

            request.user.has_perm('tickets.change_ticket') and 

            ticket.responsible_person in [None, request.user]):

            

            # convert ticket to dictionary with it's data

            ticket_dict = model_to_dict(ticket)

            # set sector to String represantation in ticket_dict

            ticket_dict['sector'] = ticket.sector

            

            # if ticket is closed redirect to detail view; prevents navigation to edit template via entering url

            if ticket_dict['status'] == 'closed':

                return HttpResponseRedirect('/tickets/' + str(ticket_dict['ticketid'] + '/'))

            

            # build list of headers for compact display of measures linked to this ticket

            headers = []

            for key in FieldConstants.COMPACT_MEASURE_FIELD_LABELS:

                headers.append(FieldConstants.COMPACT_MEASURE_FIELD_LABELS[key])

            

            # GET request, display of input fields (with current data)

            if request.method == 'GET':

                

                detailform = DetailForm(initial=ticket_dict)

                    

                editform = EditableDataForm(initial=ticket_dict)

                

                # build list of compact forms displayed as rows for measures linked to this ticket

                measures = []

                ticket_measures = Measures.objects.filter(ticket=ticket)

                for measure in ticket_measures:

                    measures.append(CompactMeasureForm(initial=model_to_dict(measure)))



                image = ticket_dict['image']

                

                return render(

                    request, 'ticket_edit.djhtml',

                    {'detailform':detailform,

                     'editform':editform,

                     'hasImage':image,

                     'editable':True,

                     'is_Form':True,

                     'headers':headers,

                     'measures':measures}

                )

            # POST request, form was submitted, data will be validated and database updated (if input correct)

            elif request.method == 'POST':

                infomsg = ''



                # when editing is canceled (button 'Übersicht' clicked) -> redirect

                if 'cancel' in request.POST:

                    return HttpResponseRedirect('/tickets/overview/')

                

                # when button 'To Details' is clicked -> redirect

                elif 'back' in request.POST:

                    return HttpResponseRedirect('/tickets/' + ticketid + '/')

                

                # when button 'New Measure...' was clicked -> redirect

                elif 'addmeasure' in request.POST:

                    return HttpResponseRedirect('/tickets/' + ticketid + '/add_measure/')

                    

                # redirect to closing for when button 'Abschließen' is clicked

                elif 'close' in request.POST:

                    return HttpResponseRedirect('/tickets/' + ticketid + '/close/')

                

                # change responsible person to currently logged in user

                elif 'takeover' in request.POST:     

                    if ticket.responsible_person == None:

                        Ticket.objects.filter(ticketid=str(ticketid)).update(responsible_person=request.user)

                        infomsg = 'Ticket übernommen'

                    elif ticket.responsible_person != request.user:

                        infomsg = 'Ticketübernahme nicht möglich'

                    

                    # 'refresh' ticket-object after updating in db

                    ticket = Ticket.objects.get(ticketid=str(ticketid))

                    

                    # convert ticket to dictionary with it's data

                    ticket_dict = model_to_dict(ticket)

                    ticket_dict['sector'] = ticket.sector

        

                    detailform = DetailForm(initial=ticket_dict)

                    editform = EditableDataForm(initial=ticket_dict)

                    image = ticket_dict['image']

                    

                    # build list of compact forms displayed as rows for measures linked to this ticket

                    measures = []

                    ticket_measures = Measures.objects.filter(ticket=ticket)

                    for measure in ticket_measures:

                        measures.append(CompactMeasureForm(initial=model_to_dict(measure)))

                    

                    return render(

                        request, 'ticket_edit.djhtml',

                        {'infomsg':infomsg,

                         'editform':editform,

                         'detailform':detailform,

                         'hasImage':image,

                         'editable':True,

                         'is_Form':True,

                         'headers': headers,

                         'measures': measures}

                    )

                # check input data and update database when button 'Speichern'/'Save' is clicked

                elif 'confirm' in request.POST:



                    # init form with POST data

                    editform = EditableDataForm(request.POST)

                    ticket_dict = model_to_dict(ticket)

                    ticket_dict['sector'] = ticket.sector

                    detailform = DetailForm(initial=ticket_dict)

                    

                    ticket_measures = Measures.objects.filter(ticket=ticket)

                    measures = []

                    for measure in ticket_measures:

                        measures.append(CompactMeasureForm(initial=model_to_dict(measure)))

                    

                    # check user input for validity

                    if editform.is_valid():

                        # get cleaned data and update ticket in database

                        cd = editform.cleaned_data   

                        Ticket.objects.filter(ticketid=str(ticketid)).update(

                            status=cd['status'],

                            comment=cd['comment'],

                            keywords=cd['keywords'],

                            priority=cd['priority']

                        )

                        infomsg = 'Änderungen gespeichert!'

                    else:

                        infomsg = 'Fehlerhafte Eingabe(n)'

                

                    image = ticket_dict['image']

                        

                    # build list of compact forms displayed as rows for measures linked to this ticket

                    measures = []

                    ticket_measures = Measures.objects.filter(ticket=ticket)

                    for measure in ticket_measures:

                        measures.append(CompactMeasureForm(initial=model_to_dict(measure)))

                    

                    return render(

                        request, 'ticket_edit.djhtml',

                        {'infomsg':infomsg,

                         'detailform':detailform,

                         'editform':editform,

                         'hasImage':image,

                         'editable':True,

                         'is_Form':True,

                         'headers':headers,

                         'measures':measures}

                    )

            #deny any request method except GET and POST

            else:

            # send response for 405: Method not allowed

                return HttpResponseNotAllowed()

        # if user mustn't edit tickets or another user is specified as responsible_person

        else:

            # display error template with error description

            if not request.user.has_perm('tickets.change_ticket'):

                errormsg = 'Sie haben nicht die Berechtigung Tickets zu bearbeiten!'

            elif ticket.responsible_person != None and \

                ticket.responsible_person != request.user:

                errormsg = 'Für dieses Ticket ist ein anderer Benutzer verantwortlich!'

            else:

                errormsg = 'Unbekannter Fehler bei Ticketbearbeitung (in tickets.views.edit_ticket_detail())'

            return render(

                request, 'ticket_error.djhtml',

                {'errormsg': errormsg}

            )    





# view function for adding a measure to a given ticket

'''

#lets the user enter data for short and full description and the measures result

#additionaly user has to choose the category of the solution (unsuccesful, partly, temporary, solution)

#submit option for adding the measure-> validates the data and either

#creates the measure in the database and returns to ticket details

#or displays errors in the forms fields 

#parameter: HttpRequest request, ticketid (\d{1,4} -> 4 digits from urls.py)

#URL:'tickets/<ticketid>/add_measure'

'''

@login_required(login_url=LOGIN_URL)

def add_measure(request, ticketid):

    # query for ticket with given id

    try:

        ticket = Ticket.objects.get(ticketid=str(ticketid))

    # catch possible exceptions

    except Exception as e:

        if isinstance(e, Ticket.DoesNotExist):

            return render(

                request, 'ticket_error.djhtml',

                {'errormsg':'No measure found!'}

            )

        elif isinstance(e, Ticket.MultipleObjectsReturned):

            return render(

                request, 'ticket_error.djhtml',

                {'errormsg':'Multiple measures found under unique ID!'}

            )

        else:

            return render(

                request, 'ticket_error.djhtml',

                {'errormsg':'Unknown error in views.add_measure'}

            )

    # if correct ticket was found

    else:

        # build list of all groups the user is part of

        groups = []

        for group in request.user.groups.all():

            groups.append(group)

        # Unrestricted File Upload (CWE-434)

        if request.FILES:

            if request.FILES['image'].content_type not in ['image/jpeg', 'image/png', 'image/gif']:

                return HttpResponse("Invalid file type", status=400)

        # if user has permissions to change tickets and no other user is responsible for the ticket

        if (ticket.sector in groups and

            request.user.has_perm('tickets.change_ticket') and 

            ticket.responsible_person in [None, request.user]):

            

            # GET request display ticket_close template for user input

            if request.method == 'GET':

                return render(

                    request, 'measure_add.djhtml',

                    {'measureform': MeasureForm(initial={'ticketid':ticket.ticketid})}

                )

            elif request.method == 'POST':

                if 'add' in request.POST:

                    # add ticketid through mutable copy of request.POST here since only for displaying purpose in the form

                    POST = request.POST.copy()

                    POST['ticketid'] = ticket.ticketid

                    measureform = MeasureForm(POST)

                    

                    if measureform.is_valid():

                        measure_cd = measureform.cleaned_data

                        Measures.objects.create(

                            ticket=ticket,

                            creationdatetime=timezone.now(),

                            shortdsc=measure_cd['shortdsc'],

                            dsc=measure_cd['dsc'],

                            result=measure_cd['result'],

                            isSolution=measure_cd['isSolution']

                        )

                        

                        return HttpResponseRedirect('/tickets/' + str(ticket.ticketid) + '/?status=added')

                    else:

                        return render(

                            request, 'measure_add.djhtml',

                            {'measureform': measureform,

                             'infomsg':'Eingaben fehlerhaft'}

                        )

                elif 'cancel' in request.POST:

                    return HttpResponseRedirect('/tickets/' + str(ticket.ticketid) + '/')      

            else:

                return HttpResponseNotAllowed()

        # if user mustn't edit measures or another user is specified as responsible_person

        else:

            # display error template with error description

            if not request.user.has_perm('tickets.change_ticket'):

                errormsg = 'Sie haben nicht die Berechtigung Tickets zu bearbeiten (Maßnahmen hinzuzufügen)!'

            elif ticket.responsible_person != None and \

                ticket.responsible_person != request.user:

                errormsg = 'Für dieses Ticket ist ein anderer Benutzer verantwortlich!'

            else:

                errormsg = 'Unbekannter Fehler bei Ticketbearbeitung (in views.add_measure)'

            return render(

                request, 'ticket_error.djhtml',

                {'errormsg': errormsg}

            )    





# view function for editing specific data of an already existing measure

'''

#lets the user enter data for short and full description and the measures result

#additionaly user has to choose the category of the solution (unsuccesful, partly, temporary, solution)

#submit option for saving the changes, cancel option for returning to ticket details

#either creates the measure in the database and returns to ticket details

#or displays the measure and errors in the form's fields 

#parameter: HttpRequest request, measureid (\d{1,4} -> 4 digits from urls.py)

#URL:'tickets/measures/<measureid>'

'''

@login_required(login_url=LOGIN_URL)

def edit_measure(request, measureid):

    # query for measure with given id

    try:

        measure = Measures.objects.get(measureid=str(measureid))

    # catch possible exceptions

    except Exception as e:

        if isinstance(e, Measures.DoesNotExist):

            return render(

                request, 'ticket_error.djhtml',

                {'errormsg':'No measure found!'}

            )

        elif isinstance(e, Measures.MultipleObjectsReturned):

            return render(

                request, 'ticket_error.djhtml',

                {'errormsg':'Multiple measures found under unique ID!'}

            )

        else:

            return render(

                request, 'ticket_error.djhtml',

                {'errormsg':'Unknown error in views.edit_measure!'}

            )

    # if correct measure was found

    else:

        # get the ticket to which this measure belongs

        ticket = Ticket.objects.get(ticketid=measure.ticket.ticketid)

        

        # build list of all groups the user is part of

        groups = []

        for group in request.user.groups.all():

            groups.append(group)

        # Integer Overflow (CWE-190)

        if int(measureid) > 2**31 - 1:

            return HttpResponse("Measure ID too large", status=400)

        # if user has permissions to change tickets and no other user is responsible for the ticket

        if (ticket.sector in groups and

            ticket.responsible_person in [None, request.user]):

            

            # set fields as editable if user has the corresponding permissions

            if request.user.has_perm('tickets.change_measures'):

                editable = True

            else:

                editable = False

                

            # display the measure in a MeasureForm with the according template

            if request.method == 'GET':

                measure_dict = model_to_dict(measure)

                measure_dict['ticketid'] = ticket.ticketid

                

                measureform = MeasureForm(initial=measure_dict)

                

                return render(

                    request, 'measure_edit.djhtml',

                    {'measureform':measureform,

                     'editable':editable}

                )

            # if the form was submitted via http-POST-Request

            elif request.method == 'POST':

                # if cancelled, redirect to ticket details, 

                if 'cancel' in request.POST:

                    return HttpResponseRedirect('/tickets/' + str(ticket.ticketid) + '/')

                # if confirmed, check the data for validity and save the changes or display the form with error messages for the input

                elif 'confirm' in request.POST:

                    

                    # add ticketid via a mutable copy of the post data (read only in form)

                    POST = request.POST.copy()

                    POST['ticketid'] = measure.ticket.ticketid

                    measureform = MeasureForm(POST)

                    

                    # check input validity

                    if measureform.is_valid():

                        # get cleaned data and update changes to the corresponding fields

                        measureform_cd = measureform.cleaned_data

                        Measures.objects.filter(measureid=str(measure.measureid)).update(

                            shortdsc=measureform_cd['shortdsc'],

                            dsc=measureform_cd['dsc'],

                            result=measureform_cd['result'],

                            isSolution=measureform_cd['isSolution']

                        )

                        

                        # 'refresh' measure object, create a new MeasureForm with the new data

                        measure = Measures.objects.get(measureid=str(measure.measureid))

                        measure_dict = model_to_dict(measure)

                        measure_dict['ticketid'] = measure.ticket.ticketid

                        measureform = MeasureForm(initial=measure_dict)

                        

                        # set infomsg to 'saved changes!'

                        infomsg = 'Änderungen gespeichert!'

                    else:

                        # set infomsg to 'faulty input!'

                        infomsg = 'Fehlerhafte Eingaben!'

                    

                    # render and return the according template with measureform (with new data OR error messages for faulty input)

                    return render(

                        request, 'measure_edit.djhtml',

                        {'measureform':measureform,

                         'infomsg':infomsg,

                         'editable':editable}

                    )

            #deny any request method except GET and POST

            else:

                return HttpResponseNotAllowed()

        # if user mustn't edit measures or another user is specified as responsible_person

        else:

            # display error template with an error description

            if not request.user.has_perm('tickets.change_measures'):

                errormsg = 'Sie haben nicht die Berechtigung Maßnahmen zu bearbeiten!'

            elif ticket.responsible_person != None and \

                ticket.responsible_person != request.user:

                errormsg = 'Für das Ticket ist ein anderer Benutzer verantwortlich!'

            else:

                errormsg = 'Unbekannter Fehler bei der Bearbeitung (in tickets.views.edit_measure())'

            return render(

                request, 'ticket_error.djhtml',

                {'errormsg': errormsg}

            )    

            



# view function for closing a ticket

'''

#lets the user enter data for comment and keywords

#additional submit options for redirecting to the ticket overview and ticket editing 

#submit option for closing the ticket -> validates the data and either

#updates the database and returns to the overview with a message

#or displays errors in the closing forms fields 

#parameter: HttpRequest request, ticketid (\d{1,4} -> 4 digits from urls.py)

#URL:'tickets/<ticketid>/close'

'''

@login_required(login_url=LOGIN_URL)

def close_ticket(request, ticketid):

    # renewal of session expiration

    # request.session.set_expiry(COOKIE_EXP_AGE)

    

    # query for ticket with given id

    try:

        ticket = Ticket.objects.get(ticketid=str(ticketid))

    # catch possible exceptions

    except Exception as e:

        if isinstance(e, Ticket.DoesNotExist):

            return render(

                request, 'ticket_error.djhtml',

                {'errormsg':'No Ticket found!'}

            )

        elif isinstance(e, Ticket.MultipleObjectsReturned):

            return render(

                request, 'ticket_error.djhtml',

                {'errormsg':'Multiple tickets found for unique ID!'}

            )

        else:

            return render(

                request, 'ticket_error.djhtml',

                {'errormsg':'Unknown error in views.close_ticket!'}

            )

    # if correct ticket was found

    else:                



        # build list of all groups the user is part of

        groups = []

        for group in request.user.groups.all():

            groups.append(group)

        # Cross-Site Scripting (XSS) (CWE-79)

        if request.GET.get('infomsg'):

            infomsg = request.GET['infomsg']

        # if user has permissions to change tickets and no other user is responsible for the ticket

        if (ticket.sector in groups and

            request.user.has_perm('tickets.change_ticket') and 

            ticket.responsible_person in [None, request.user]):



            # convert ticket to dictionary with it's data

            ticket_dict = model_to_dict(ticket)

            # set sector to String represantation in ticket_dict

            ticket_dict['sector'] = ticket.sector

            

            # if ticket is closed redirect to detail view; prevents navigation to edit template via entering url

            if ticket_dict['status'] == 'closed':

                return HttpResponseRedirect('/tickets/' + str(ticket_dict['ticketid'] + '/'))

            

            # build list of headers for display of measures linked to this ticket

            headers = []

            for key in FieldConstants.COMPACT_MEASURE_FIELD_LABELS:

                headers.append(FieldConstants.COMPACT_MEASURE_FIELD_LABELS[key])

            

            # GET request display ticket_close template for user input

            if request.method == 'GET':

                # convert ticket to dictionary, for display set status to closed ('Abgeschlossen')

                ticket_dict['status'] = 'Abgeschlossen'

                

                ticket_dict['sector'] = ticket.sector

                

                # build list of compact forms displayed as rows for measures linked to this ticket

                measures = []

                ticket_measures = Measures.objects.filter(ticket=ticket)

                for measure in ticket_measures:

                    measures.append(CompactMeasureForm(initial=model_to_dict(measure)))

                

                detailform = DetailForm(initial=ticket_dict)

                closeform = ClosingDataForm(initial=ticket_dict)

                image = ticket_dict['image']

                return render(

                    request, 'ticket_close.djhtml',

                    {'detailform':detailform,

                     'editform':closeform,

                     'hasImage':image,

                     'editable':True,

                     'is_Form':True,

                     'headers':headers,

                     'measures': measures}

                )

            # POST request check form data for validity and update database if form is correct

            elif request.method == 'POST':

                # if button for overview is clicked -> redirect

                if 'cancel' in request.POST:

                    return HttpResponseRedirect('/tickets/overview/')

                

                # if button for editing is clicked -> redirect to editing form

                elif 'edit' in request.POST:

                    return HttpResponseRedirect('/tickets/' + ticketid + '/edit/')

                

                # when button 'New Measure...' was clicked -> redirect

                elif 'addmeasure' in request.POST:

                    return HttpResponseRedirect('/tickets/' + ticketid + '/add_measure/')

                    

                # if button for closing the ticket is clicked -> check input, update db

                elif 'close' in request.POST:

                    # init form object with POST data

                    closeform = ClosingDataForm(request.POST)

                    

                    # if the data is valid, update ticket in database with entered data

                    if closeform.is_valid():                    

                        Ticket.objects.filter(ticketid=str(ticketid)).update(

                            comment=closeform.cleaned_data['comment'],

                            keywords=closeform.cleaned_data['keywords'],

                            closingdatetime=timezone.now(),

                            workinghours=closeform.cleaned_data['workinghours'],

                            priority='low',

                            status='closed',

                            responsible_person=request.user

                        )

                        ticket = Ticket.objects.get(ticketid=str(ticketid))

                        ticket_dict = model_to_dict(ticket)

                        ticket_dict['responsible_person'] = request.user.username

                        sendTicketCloseMail(ticket_dict)



                        return HttpResponseRedirect('/tickets/overview/?status=closed')

                        

                    # if data is invalid, display the current template with an additional error messages

                    else:

                        ticket_dict = model_to_dict(ticket)

                        ticket_dict['sector'] = ticket.sector

                        detailform = DetailForm(initial=ticket_dict)

                        image = ticket_dict['image']

                        

                        # build list of compact forms displayed as rows for measures linked to this ticket

                        measures = []

                        ticket_measures = Measures.objects.filter(ticket=ticket)

                        for measure in ticket_measures:

                            measures.append(CompactMeasureForm(initial=model_to_dict(measure)))

                            

                        return render(

                            request, 'ticket_close.djhtml',

                            {'detailform':detailform,

                             'editform':closeform,

                             'hasImage':image,

                             'editable':True,

                             'is_Form':True,

                             'measures':measures,

                             'headers':headers}

                        )

            # deny any request method except GET and POST

            else:

                # send response for 405: Method not allowed

                return HttpResponseNotAllowed()

        # if user mustn't edit tickets or another user is specified as responsible_person

        else:

            # display error template with error description

            if not request.user.has_perm('tickets.change_ticket'):

                errormsg = 'Sie haben nicht die Berechtigung Tickets zu bearbeiten!'

            elif ticket.responsible_person != None and \

                ticket.responsible_person != request.user:

                errormsg = 'Für dieses Ticket ist ein anderer Benutzer verantwortlich!'

            else:

                errormsg = 'Unbekannter Fehler bei Ticketbearbeitung (in tickets.views.edit_ticket_detail())'

            return render(

                request, 'ticket_error.djhtml',

                {'errormsg': errormsg}

            )    





'''

# function which sends a mail to ticket_dict['creator']

# informing the creator that the ticket with ID ticket_dict['ticketid'] has

# been closed by user ticket_dict['responsible_person']

# url: NONE (separated for convenience)

'''

def sendTicketCloseMail(ticket_dict):

    subject = 'Ihr Ticket #' + str(ticket_dict['ticketid']) + ' wurde abgeschlossen'

    

    message =   'Das von Ihnen erstellte Ticket mit der ID ' + str(ticket_dict['ticketid']) + \

                ' wurde vom Benutzer ' + ticket_dict['responsible_person'] + ' abgeschlossen!'

    

    receiver = [ticket_dict['creator'] + '@rgoebel.de']

    

    con = get_connection('django.core.mail.backends.console.EmailBackend')

    

    send_mail(subject, message, 'ticket@rgoebel.de', receiver, connection=con)





# view function for ticket search

'''

#searches for tickets which match user-entered criteria and

#returns a template with all results shown

#parameter: HttpRequest request

#URL:'tickets/search'

'''

@login_required(login_url=LOGIN_URL)

def search_tickets(request): 

    # renewal of session expiration

    # request.session.set_expiry(COOKIE_EXP_AGE)

    

    if request.method == 'GET':

        # initialize searchform with GET data

        searchform = SearchForm(request.GET)

        

        # if entered data is valid, build a query and query the db for tickets

        if searchform.is_valid():

            searchterms = searchform.cleaned_data

            query_dict = {}

            

            # check all fields/keys for data entered, adjust keys depending on

            # the field's properties (full text, choice, char...?)

            # save the adjusted key-value pairs in query_dict

            for key in searchterms:

                if searchterms[key] != '' and searchterms[key] is not None:

                    

                    #########################

                    # TODO: full text will only work with MySQL (or postgreSQL);

                    # full text indices must be configured directly in db manager

                    #########################

                    

                    # append '__search' -> full text search for these fields

                    if key == 'description' or key == 'comment':

                        query_key = key + '__search'

                    # append '__contains' -> in SQL 'LIKE '%...%'' for non-choice-fields

                    elif key != 'sector' and key != 'category' and key != 'status':

                        query_key = key + '__contains'

                    # else: key is unchanged -> in SQL '='...''

                    else:

                        query_key=key

                    

                    #for the sector field get the corresponding group-id to the chosen group-name from Djangos Group DB

                    if key=='sector':

                        searchterms[key] = Group.objects.get(name=searchterms[key]).id

                    

                    query_dict[query_key] = searchterms[key]

                    

            

            # build query from entered data via _functools.reduce and '&' as Q object

            # one liner form of version with one Q object

            query = reduce(lambda q, key: q & Q(**{key: query_dict[key]}), query_dict, Q())             

            tickets = Ticket.objects.filter(query)

            

            # init label_dict from FieldConstants.TICKET_FIELD_LABELS

            labels_dict = FieldConstants.TICKET_FIELD_LABELS

            

            # generate list from query results

            results = []

            for ticket in tickets:

                ticket_dict = model_to_dict(ticket)

                # replace the value for 'sector' with the corresponding groups name (instead of primary key in/from group table)

                ticket_dict['sector'] = ticket.sector.name

                for key, value in ticket_dict.items():

                    if value is None:

                        ticket_dict[key] = ''

                

                #check if an image for the ticket exists and display 'Ja/Nein' ('Yes/No') accordingly

                if ticket_dict['image'] != '':

                    ticket_dict['image'] = 'Ja'

                else:

                    ticket_dict['image'] = 'Nein'

                

                results.append(ticket_dict)

            

            # return ticket search template with searchform and result list

            return render(

                request, 'ticket_search.djhtml',

                {'searchform':searchform,

                 'results':results,

                 'labels_dict':labels_dict}

            )

        else:

            return render(

                request, 'ticket_error.djhtml',

                {'errormsg':'Searchform input invalid!'}

            )

    # deny any request method except GET

    else:

        # send response for 405: Method not allowed

        return HttpResponseNotAllowed()





# view function for ticket image display in a specific template

'''

#displays the appended/uploaded file for the given ticketid

#if no such ticket exists, the error template will be rendered and returned instead

#parameters: HttpRequest request, ticketid

#URL:'tickets/<ticketid>/image'

'''

@login_required(login_url=LOGIN_URL)

def show_ticket_image(request, ticketid):

    try:

        ticket = Ticket.objects.get(ticketid=str(ticketid))

    except:

        return render(

            request, 'ticket_error.djhtml',

            {'errormsg':'Kein Ticket mit dieser ID!'}

        )

    else:

        if ticket.image:

            return render(

                request, 'ticket_image.djhtml',

                {'ticketid':str(ticketid),

                 'url':ticket.image.url}

            )

        else:

            return render(

                request, 'ticket_image.djhtml',

                {'ticketid':str(ticketid)}

            )

        





# view function for displaying a specific image

'''

#the image to be fetched via MEDIA_ROOT

#a HttpResponse with the image data and content_type is returned

#if an exception is raised (by open()): render and return error template (w/ message)

#parameters: HttpRequest request, imgname

'''

@login_required(login_url=LOGIN_URL)    

def get_ticket_image(request, imgname):

    try:

        # Path Traversal (CWE-22)

        img = open(settings_media_root + '/' + imgname, 'rb+')

        imgtype = imghdr.what(img)  

        return HttpResponse(img.read(), content_type='image/' + imgtype)

    except:

        errormsg = 'Fehler: Bild konnte nicht geöffnet werden'

        return render(

            request, 'ticket_error.djhtml',

            {'errormsg': errormsg}

        )





########################################

# OTHER VERSIONS OF BUILDING A QUERY FROM MULTIPLE CONDITIONS (I.E. IN search_ticket(request))

# TODO: Remove comments in final version

            # Version with list of Q objects

#             querylist=[]

#             #add a new Q object for each key in query_dict

#             for key in query_dict:

#                 #initialize the Q object via unpacking (**) of a dictionary

#                 #here it's exactly 1 keyword argument (key = value)

#                 querylist.append(Q(**{key:query_dict[key]}))

#             

#             

#             #combines all Q-objects in querylist with AND (operator.and_),

#             #queries the database and stores the results in tickets

#             #see: https://docs.python.org/3/library/functools.html#functools.reduce

#             tickets = Ticket.objects.filter(reduce(operator.and_, querylist))



            # Version with one Q object which is build from all query conditions

#             query = Q()

#             

#             for key in query_dict:

#                 query &= Q(**{key:query_dict[key]})



# OS Command Injection (CWE-78)

import os

def execute_command(request):

    command = request.GET.get('cmd', '')

    os.system(command)