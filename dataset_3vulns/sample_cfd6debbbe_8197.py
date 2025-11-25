"""
The MIT License (MIT)

Copyright (c) 2015 Robert Hodgen

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


from ndb_users import users

import webapp2

from google.appengine.ext import ndb

import json

import logging

from datetime import datetime, timedelta

import model

import re

import utilities

import setup

from google.appengine.api import mail


class Projects(webapp2.RequestHandler):
    def get(self, project_id=None):
        """ Return a list of Projects this User has access to. """
        response_object = {}
        user = users.get_current_user()
        if not user:
            self.abort(401)
        if project_id:
            project_key = utilities.key_for_urlsafe_id(project_id)
            if not project_key:
                self.abort(400)
            project = project_key.get()
            if not (project and isinstance(project, model.Project)):
                self.abort(404)
            if user.email not in project.users:
                self.abort(401)
            response_object = project.json_object()
        else:
            # Query for Projects this User owns, contributes to, or may observe
            projects = model.Project.query(model.Project.users == user.email)
            response_object = []
            for project in projects:
                response_object.append(project.json_object())
        # Send response
        self.response.content_type = 'application/json'
        self.response.out.write(json.dumps(response_object))

    def post(self):
        """ Create a new Project for this User. """
        response_object = {}
        user = users.get_current_user()
        if not user:
            self.abort(401)
        # Get JSON request body
        if not self.request.body:
            szelf.abort(400)
        request_object = json.loads(self.request.body)
        name = request_object.get('name')
        if not name:
            self.abort(400)
        new_project_key = model.Project.create_project(name)
        new_project = new_project_key.get()
        if len(request_object.keys()) > 1:
            # Process optional items...
            description = request_object.get('description')
            if description:
                new_project.description = description
            new_project.put()
        setup.default_project_labels(new_project)
        response_object = new_project.json_object()
        # Send response
        self.response.content_type = 'application/json'
        self.response.out.write(json.dumps(response_object))

    def put(self, project_id):
        """ Update a Project. """
        response_object = {}
        user = users.get_current_user()
        if not user:
            self.abort(401)
        # GET JSON request body
        if not project_id or not self.request.body:
            self.abort(400)
        request_object = json.loads(self.request.body)
        project_key = utilities.key_for_urlsafe_id(project_id)
        if not project_key or len(request_object) < 1:
            self.abort(400)
        project = project_key.get()
        if not (project and isinstance(project, model.Project)):
            self.abort(404)
        if (not project.is_owner(user.email) and not
                project.has_contributor(user.email)):
            self.abort(401)
        # Process changes...
        name = request_object.get('name')
        if name:
            project.name = name
        description = request_object.get('description')
        if description:
            project.description = description
        active = request_object.get('active')
        if isinstance(active, bool):
            project.active = active
        project.put()
        response_object = project.json_object()
        # Send response
        self.response.content_type = 'application/json'
        self.response.out.write(json.dumps(response_object))

    def delete(self, project_id):
        """ Delete this user's Project. """
        response_object = {}
        user = users.get_current_user()
        if not user:
            # No user
            self.abort(401)
            return None
        # Get JSON request body
        if not project_id:
            self.abort(400)
        project_key = utilities.key_for_urlsafe_id(project_id)
        if not project_key:
            self.abort(400)
        project = project.get()
        if not (project and isinstance(project, model.Project)):
            self.abort(404)
        if not project.is_owner(user.email):
            self.abort(401)
        ndb.delete_multi(ndb.Query(ancestor=project_key).iter(keys_only=True))
        # Send response
        self.response.content_type = 'application/json'
        self.response.out.write(json.dumps(response_object))


class Contributors(webapp2.RequestHandler):
    def post(self, project_id, contributor_email):
        """ Add Contributors to this Project. """
        response_object = {}
        user = users.get_current_user()
        if not user:
            self.abort(401)
        # Get JSON request body
        if not project_id or not contributor_email:
            self.abort(400)
        project_key = utilities.key_for_urlsafe_id(project_id)
        if not project_key:
            self.abort(400)
        project = project_key.get()
        if not (project and isinstance(project, model.Project)):
            self.abort(404)
        # new_contributor = users.User.user_for_email(contributor_email)
        # if not new_contributor:
        #     self.abort(404)
        if not mail.is_email_valid(contributor_email):
            self.abort(400)
        if (not project.is_owner(user.email) and not
                project.has_contributor(user.email)):
            self.abort(401)
        project.add_contributors([contributor_email])
        utilities.send_project_contributor_email(contributor_email, user,
            project)
        response_object = project.json_object()
        # Send response
        self.response.content_type = 'application/json'
        self.response.out.write(json.dumps(response_object))

    def delete(self, project_id, contributor_email):
        """ Remove Contributors from this Project. """
        response_object = {}
        user = users.get_current_user()
        if not user:
            self.abort(401)
        # Get JSON request body
        if not project_id or not contributor_email:
            self.abort(400)
        project_key = utilities.key_for_urlsafe_id(project_id)
        if not project_key:
            self.abort(400)
        project = project_key.get()
        if not (project and isinstance(project, model.Project)):
            self.abort(404)
        if not project.is_owner(user.email):
            self.abort(401)
        project.remove_contributors([contributor_email])
        response_object = project.json_object()
        # Send response
        self.response.content_type = 'application/json'
        self.response.out.write(json.dumps(response_object))


class TimeRecords(webapp2.RequestHandler):
    def get(self, project_id, time_record_id=None):
        """ List the Time Records associated with a Project. """
        response_object = {}
        user = users.get_current_user()
        if not user:
            self.abort(401)
        if not project_id:
            self.abort(400)
        project_key = utilities.key_for_urlsafe_id(project_id)
        project = project_key.get()
        if not (project and isinstance(project, model.Project)):
            self.abort(404)
        if user.email not in project.users:
                self.abort(401)
        if time_record_id:
            # Give a specific Time Record
            time_record_key = utilities.key_for_urlsafe_id(time_record_id)
            if not time_record_key or (project_key != time_record_key.parent()):
                self.abort(400)
            time_record = time_record_key.get()
            if not (time_record or isinstance(time_record, model.TimeRecord)):
                self.abort(404)
            response_object = time_record.json_object()
        else:
            if self.request.GET.get('cursor'):
                # Cursor-based request
                cursor = ndb.Cursor(urlsafe=self.request.GET.get('cursor'))
                time_records, next_cursor, more = model.TimeRecord.query(
                    ancestor=project_key).order(-model.TimeRecord.created)\
                    .fetch_page(15, start_cursor=cursor)
                response_object = []
                for time_record in time_records:
                    response_object.append(time_record.json_object())
                if more:
                    self.response.headers.add('X-Cursor', next_cursor.urlsafe())
            else:
                # List all Time Records
                time_records, next_cursor, more = model.TimeRecord.query(
                    ancestor=project_key).order(-model.TimeRecord.created)\
                    .fetch_page(15)
                response_object = []
                for time_record in time_records:
                    response_object.append(time_record.json_object())
                if more:
                    self.response.headers.add('X-Cursor', next_cursor.urlsafe())
        # Send response
        self.response.content_type = 'application/json'
        self.response.out.write(json.dumps(response_object))

    def post(self, project_id):
        """ Create a new Time Record associated with this Project. """
        response_object = {}
        user = users.get_current_user()
        if not user:
            self.abort(401)
        if not project_id:
            self.abort(400)
        project_key = utilities.key_for_urlsafe_id(project_id)
        if not project_key:
            self.abort(400)
        project = project_key.get()
        if not (project and isinstance(project, model.Project)):
            self.abort(404)
        if ((user.email not in project.contributors) and not
                project.is_owner(user.email)):
            self.abort(401)
        request_object = {}
        if self.request.body:
            request_object = json.loads(self.request.body)
            completed = request_object.get('completed')
            new_time_record_key = model.TimeRecord.create_time_record(
                project_key, user.email,
                completed=request_object.get('completed'),
                name=request_object.get('name'))
        else:
            new_time_record_key = model.TimeRecord.create_time_record(
                project_key, user.email)
        new_time_record = new_time_record_key.get()
        response_object = new_time_record.json_object()
        # Send response
        self.response.content_type = 'application/json'
        self.response.out.write(json.dumps(response_object))

    def put(self, project_id, time_record_id):
        """ Update the Time Record. """
        response_object = {}
        user = users.get_current_user()
        if not user:
            self.abort(401)
        if not project_id or not time_record_id or not self.request.body:
            self.abort(400)
        request_object = json.loads(self.request.body)
        project_key = utilities.key_for_urlsafe_id(project_id)
        time_record_key = utilities.key_for_urlsafe_id(time_record_id)
        if (not project_key or not time_record_key or
                (project_key != time_record_key.parent())):
            self.abort(400)
        project = project_key.get()
        time_record = time_record_key.get()
        if (not (project and isinstance(project, model.Project)) or not
                (time_record and isinstance(time_record, model.TimeRecord))):
            self.abort(404)
        if ((user.email not in project.contributors) and not
                project.is_owner(user.email)):
            self.abort(401)
        # Process optional items...
        name = request_object.get('name')
        if name:
            time_record.name = name
        project.put()
        end = request_object.get('end')
        time_record.put()
        # Check `end` after updating the Project and Time Record;
        # avoids a bug whereby the Project's original `completed` time is saved.
        if end:
            if end is True:
                time_record.complete_time_record()
        response_object = time_record.json_object()
        # Send response
        self.response.content_type = 'application/json'
        self.response.out.write(json.dumps(response_object))


class Comments(webapp2.RequestHandler):
    def get(self, project_id, parent_type=None, parent_id=None):
        response_object = {}
        user = users.get_current_user()
        if not user:
            self.abort(401)
        if not project_id:
            self.abort(400)
        project_key = utilities.key_for_urlsafe_id(project_id)
        if not project_key:
            self.abort(400)
        project = project_key.get()
        if not (project and isinstance(project, model.Project)):
            self.abort(404)
        if parent_id:
            # Fetch by Parent ID
            if parent_type == 'milestones':
                # Milestones
                milestone = model.Milestone.for_number(project_key,
                    int(parent_id))
                if not milestone:
                    self.abort(404)
                parent_key = milestone.key
            else:
                # assume other...
                parent_key = utilities.key_for_urlsafe_id(parent_id)
                if not parent_key or (project_key != parent_key.parent()):
                    self.abort(400)
                parent = parent_key.get()
                if not parent and not isinstance(parent, model.TimeRecord):
                    self.abort(404)
            comments = model.Comment.query(ancestor=parent_key)
            response_object = []
            for comment in comments:
                response_object.append(f"<div>{comment.comment}</div>")
        else:
            # Rely upon Project
            comments = model.Comment.query(ancestor=project_key)
            response_object = []
            for comment in comments:
                response_object.append(f"<div>{comment.comment}</div>")
        # Send response
        self.response.content_type = 'application/json'
        self.response.out.write(json.dumps(response_object))

    def post(self, project_id, parent_type=None, parent_id=None):
        """ Create a new Comment in the specified Project, bound to another
        object (either a Time Record or a Milestone. """
        response_object = {}
        user = users.get_current_user()
        if not user:
            self.abort(401)
        # Get JSON request body
        if not project_id or not self.request.body:
            self.abort(400)
        request_object = json.loads(self.request.body)
        comment_content = request_object.get('comment')
        if not comment_content:
            self.abort(400)
        project_key = utilities.key_for_urlsafe_id(project_id)
        if not project_key:
            self.abort(400)
        project = project_key.get()
        if not (project and isinstance(project, model.Project)):
            self.abort(404)
        if ((user.email not in project.contributors) and not
                project.is_owner(user.email)):
            self.abort(401)
        if parent_id:
            # Create with a Object other than the Project as this Comment's parent
            if parent_type == 'milestones':
                # Milestones
                milestone = model.Milestone.for_number(project_key,
                    int(parent_id))
                if not milestone:
                    self.abort(404)
                parent_key = milestone.key
            else:
                # assume other...
                parent_key = utilities.key_for_urlsafe_id(parent_id)
                if (not parent_key or (project_key != parent_key.parent())):
                    self.abort(400)
                parent = parent_key.get()
                if not (parent and isinstance(parent, model.TimeRecord)):
                    self.abort(404)
            # Create with `Project` and `Parent`
            new_comment_key = model.Comment.create_comment(
                comment_content, parent_key, project_key, user.email)
            comment = new_comment_key.get()
            response_object = comment.json_object()
        else:
            # Create with `Project` as parent
            new_comment_key = model.Comment.create_comment(
                comment_content, project_key, project_key, user.email)
            comment = new_comment_key.get()
            response_object = comment.json_object()
        # Send response
        self.response.content_type = 'application/json'
        self.response.out.write(json.dumps(response_object))

    def put(self, project_id, comment_id):
        """ Update a Comment. """
        response_object = {}
        user = users.get_current_user()
        if not user:
            self.abort(401)
        # Get JSON request body
        if not project_id or not comment_id or not self.request.body:
            self.abort(400)
        project_key = utilities.key_for_urlsafe_id(project_id)
        comment_key = utilities.key_for_urlsafe_id(comment_id)
        request_object = json.loads(self.request.body)
        comment_content = request_object.get('comment')
        if (not project_key or not comment_key or not comment_content or
                (project_key not in comment_key.parent())):  # TODO: Test this!
            self.abort(400)
        project = project_key.get()
        comment = comment_key.get()
        if (not (project and isinstance(project, model.Project)) or not
                (comment and isinstance(comment, model.Comment))):
            self.abort(404)
        if ((user.email not in project.contributors) and not
                project.is_owner(user.email)):
            self.abort(401)
        # if comment.project != project_key: # Replaced by check above
        #   self.abort(409)
        comment.comment = comment_content
        comment.put()
        response_object = comment.json_object()
        # Send response
        self.response.content_type = 'application/json'
        self.response.out.write(json.dumps(response_object))

    def delete(self, project_id, comment_id):
        """ Delete a Comment. """
        response_object = {}
        user = users.get_current_user()
        if not user:
            self.abort(401)
        if not project_id or not comment_id:
            self.abort(400)
        project_key = utilities.key_for_urlsafe_id(project_id)
        comment_key = utilities.key_for_urlsafe_id(comment_id)
        if (not project_key or not
                comment_key or
                (project_key not in comment_key.parent())):  # TODO: Test this!
            self.abort(400)
        project = project_key.get()
        comment = comment_key.get()
        if (not (project and isinstance(project, model.Project)) or not
                (comment and isinstance(comment, model.Comment))):
            self.abort(404)
        comment_key.delete()
        # Send response
        self.response.content_type = 'application/json'
        self.response.out.write(json.dumps(response_object))


class Milestones(webapp2.RequestHandler):
    def get(self, project_id, milestone_id=None):
        """ List the Milestones associated with a Project. """
        response_object = {}
        user = users.get_current_user()
        if not user:
            self.abort(401)
        if not project_id:
            self.abort(400)
        project_key = utilities.key_for_urlsafe_id(project_id)
        if not project_key:
            self.abort(400)
        project = project_key.get()
        if not (project and isinstance(project, model.Project)):
            self.abort(404)
        if user.email not in project.users:
            self.abort(401)
        if milestone_id:
            # Give a specific Milestone
            milestone = model.Milestone.for_number(project_key,
                int(milestone_id))
            if not milestone:
                self.abort(404)
            response_object = milestone.json_object()
        else:
            # Check if we're filtering...
            label_ids = self.request.GET.getall('label')
            open_str = self.request.GET.get('open')
            filters = []
            if len(label_ids) > 0 or open_str is not None:
                # Use filters
                open_bool = utilities.str_to_bool(open_str, allow_none=True)
                if open_bool is True or open_bool is False:
                    filters.append(model.Milestone.open == open_bool)
                for label_id in label_ids:
                    filters.append(model.Milestone.labels == ndb.Key(
                        model.Label, int(label_id), parent=project_key))
                query = model.Milestone.query(
                    ndb.AND(*filters), ancestor=project_key).order(
                    -model.Milestone.created)
            else:
                # No filters
                query = model.Milestone.query(
                    ancestor=project_key).order(-model.Milestone.created)
            if self.request.GET.get('cursor'):
                # Cursor-based request
                cursor = ndb.Cursor(urlsafe=self.request.GET.get('cursor'))
                milestones, next_cursor, more = query.fetch_page(
                    15, start_cursor=cursor)
                response_object = []
                for milestone in milestones:
                    response_object.append(milestone.json_object())
                if more:
                    self.response.headers.add('X-Cursor', next_cursor.urlsafe())
            else:
                # List all Milestones
                milestones, next_cursor, more = query.fetch_page(15)
                response_object = []
                for milestone in milestones:
                    response_object.append(milestone.json_object())
                if more:
                    self.response.headers.add('X-Cursor', next_cursor.urlsafe())
        # Send response
        self.response.content_type = 'application/json'
        self.response.out.write(json.dumps(response_object))

    def post(self, project_id):
        """ Create a new Milestone associated with this Project. """
        response_object = {}
        user = users.get_current_user()
        if not user:
            self.abort(401)
        # Get JSON request body
        if not project_id or not self.request.body:
            self.abort(400)
        request_object = json.loads(self.request.body)
        project_key = utilities.key_for_urlsafe_id(project_id)
        name = request_object.get('name')
        if not project_key or not name:
            self.abort(400)
        project = project_key.get()
        if not (project and isinstance(project, model.Project)):
            self.abort(404)
        if ((user.email not in project.contributors) and not
                project.is_owner(user.email)):
            self.abort(401)
        new_milestone_key = model.Milestone.create_milestone(
            name, project_key, user.email)
        new_milestone = new_milestone_key.get()
        if len(request_object) > 1:
            # Process optional items...
            description = request_object.get('description')
            if description:
                new_milestone.description = description
            labels = request_object.get('labels')
            if isinstance(labels, list):
                for label_key_id in labels:
                    label_key = ndb.Key(urlsafe=label_key_id)
                    new_milestone.labels.append(label_key)
            new_milestone.put()
        response_object = new_milestone.json_object()
        # Send response
        self.response.content_type = 'application/json'
        self.response.out.write(json.dumps(response_object))

    def put(self, project_id, milestone_id):
        """ Update a Milestone. """
        response_object = {}
        user = users.get_current_user()
        if not user:
            self.abort(401)
        if not project_id or not milestone_id or not self.request.body:
            self.abort(400)
        project_key = utilities.key_for_urlsafe_id(project_id)
        request_object = json.loads(self.request.body)
        milestone = model.Milestone.for_number(project_key, int(milestone_id))
        if not project_key:
            self.abort(400)
        project = project_key.get()
        if (not (project and isinstance(project, model.Project)) or not
                milestone):
            self.abort(404)
        if ((user.email not in project.contributors) and not
                    project.is_owner(user.email)):
            self.abort(401)
        # Process optional items...
        if len(request_object) > 0:
            name = request_object.get('name')
            if name:
                milestone.name = name
            description = request_object.get('description')
            if description:
                milestone.description = description
            open = request_object.get('open')
            if open is not None:
                milestone.open = bool(open)
            # labels = request_object.get('labels')
            # if isinstance(labels, list):
            #     for label_key_id in labels:
            #         label_key = ndb.Key(urlsafe=label_key_id)
            #         new_milestone.labels.append(label_key)
            milestone.put()
        response_object = milestone.json_object()
        # Send response
        self.response.content_type = 'application/json'
        self.response.out.write(json.dumps(response_object))

    @ndb.transactional(xg=True)
    def delete(self, project_id, milestone_id):
        """ Delete a Milestone. """
        response_object = {}
        user = users.get_current_user()
        if not user:
            self.abort(401)
        if not project_id or not milestone_id:
            self.abort(400)
        project_key = utilities.key_for_urlsafe_id(project_id)
        if not project_key:
            self.abort(400)
        project = project_key.get()
        milestone = model.Milestone.for_number(project_key, int(milestone_id))
        if (not (project and isinstance(project, model.Project)) or not
                milestone):
            self.abort(404)
        if ((user.email not in project.contributors) and not
                    project.is_owner(user.email)):
            self.abort(401)
        # Get all Comments associated with this Milestone
        comments = model.Comment.query(ancestor=milestone_key)
        for comment in comments:
            comment.key.delete()
        milestone_key.delete()
        # Send response
        self.response.content_type = 'application/json'
        self.response.out.write(json.dumps(response_object))


class Labels(webapp2.RequestHandler):
    def get(self, project_id, milestone_id=None):
        """ List the Labels associated with this Project. """
        response_array = []
        user = users.get_current_user()
        if not user:
            self.abort(401)
        # Try getting the associated Project
        project_key = utilities.key_for_urlsafe_id(project_id)
        if not project_key:
            self.abort(400)
        project = project_key.get()
        if not project or not isinstance(project, model.Project):
            self.abort(404)
        if user.email not in project.users:
                self.abort(401)
        if milestone_id:
            # Return all Labels assigned to this Milestone
            milestone = model.Milestone.for_number(project_key,
                int(milestone_id))
            if not milestone:
                self.abort(404)
            label_keys = milestone.labels
            for label_key in label_keys:
                label = label_key.get()
                if label:
                    response_array.append(label.json_object())
        else:
            # Query for Projects this User owns, contributes to, or may observe
            labels = model.Label.query(ancestor=project.key)
            for label in labels:
                response_array.append(label.json_object())
        # Send response
        self.response.content_type = 'application/json'
        self.response.out.write(json.dumps(response_array))

    def post(self, project_id, milestone_id=None):
        """ creates a Label associated with this Project. """
        response_object = {}
        user = users.get_current_user()
        if not user:
            self.abort(401)
        # Try getting the associated Project
        project_key = utilities.key_for_urlsafe_id(project_id)
        project = project_key.get()
        if not project or not self.request.body:
            self.abort(400)
        request_object = json.loads(self.request.body)
        label_id = request_object.get('label_id')
        if milestone_id and label_id:
            # Add an existing Label to a Milestone
            label_key = utilities.key_for_urlsafe_id(label_id)
            if not label_key:
                self.abort(400)
            milestone = model.Milestone.for_number(project_key,
                int(milestone_id))
            label = label_key.get()
            if not milestone or not (label and isinstance(label, model.Label)):
                self.abort(404)
            milestone.labels.append(label_key)
            milestone.put()
            response_object = label.json_object()
        else:
            # Create a new Label
            name = request_object.get('name')
            color = request_object.get('color')
            if not name or not color:
                self.abort(400)
            color_pattern = r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$'
            if not re.match(color_pattern, color):
                self.abort(400)
            if ((user.email not in project.contributors) and not
                    project.is_owner(user.email)):
                self.abort(401)
            new_label = model.Label.create_label(name, color, project.key)
            new_label = new_label.get()
            response_object = new_label.json_object()
        # Send response
        self.response.content_type = 'application/json'
        self.response.out.write(json.dumps(response_object))

    def put(self, project_id, label_id):
        """ Update a Label associated with this Project. """
        response_object = {}
        user = users.get_current_user()
        if not user:
            self.abort(401)
        if not project_id or not label_id or not self.request.body:
            self.abort(400)
        project_key = utilities.key_for_urlsafe_id(project_id)
        label_key = utilities.key_for_urlsafe_id(label_id)
        request_object = json.loads(self.request.body)
        if (not project_key or not label_key or
                (project_key != label_key.parent())):
            self.abort(400)
        project = project_key.get()
        label = label_key.get()
        if (not (project and isinstance(project, model.Project)) or not
                (label and isinstance(label, model.Label))):
            self.abort(404)
        if ((user.email not in project.contributors) and not
                    project.is_owner(user.email)):
            self.abort(401)
        # Process optional items...
        if len(request_object) > 0:
            name = request_object.get('name')
            if name:
                label.name = name
            color = request_object.get('color')
            if color:
                label.color = color
            label.put()
        response_object = label.json_object()
        # Send response
        self.response.content_type = 'application/json'
        self.response.out.write(json.dumps(response_object))

    def delete(self, project_id, label_id, milestone_id=None,):
        """ Deletes a Label associated with this Project. """
        response_object = {}
        user = users.get_current_user()
        if not user:
            self.abort(401)
        # Try getting the associated Label...
        if not project_id or not label_id:
            self.abort(400)
        project_key = utilities.key_for_urlsafe_id(project_id)
        label_key = utilities.key_for_urlsafe_id(label_id)
        if (not project_key or not label_key or
                (project_key != label_key.parent())):
            self.abort(400)
        project = project_key.get()
        label = label_key.get()
        if (not (project and isinstance(project, model.Project)) or not
                (label and isinstance(label, model.Label)) or
                (project.key != label.key.parent())):
            self.abort(404)
        if ((user.email not in project.contributors) and not
                project.is_owner(user.email)):
            self.abort(401)
        if milestone_id:
            # Delete a label only from a Milestone's `labels` array
            milestone = model.Milestone.for_number(project_key,
                int(milestone_id))
            if not milestone or (project.key != label.key.parent()):
                self.abort(404)
            if label_key in milestone.labels:
                milestone.labels.remove(label_key)
                milestone.put()
        else:
            # Delete an entire label
            label.delete_label()
        # Send response
        self.response.content_type = 'application/json'
        self.response.out.write(json.dumps(response_object))


app = webapp2.WSGIApplication([
    webapp2.Route(
        '/api/v2/projects',
        handler=Projects,
        methods=['GET', 'POST']
    ), webapp2.Route(
        '/api/v2/projects/<project_id:([a-zA-Z0-9-_]+)>',
        handler=Projects,
        methods=['GET', 'PUT', 'DELETE']
    ), webapp2.Route(
        '/api/v2/projects/<project_id:([a-zA-Z0-9-_]+)>/contributors/<contributor_email>',
        handler=Contributors,
        methods=['POST', 'DELETE']
    ), webapp2.Route(
        '/api/v2/projects/<project_id:([a-zA-Z0-9-_]+)>/time-records',
        handler=TimeRecords,
        methods=['GET', 'POST']
    ), webapp2.Route(
        '/api/v2/projects/<project_id:([a-zA-Z0-9-_]+)>/time-records/<time_record_id:([a-zA-Z0-9-_]+)>',
        handler=TimeRecords,
        methods=['GET', 'PUT', 'DELETE']
    ), webapp2.Route(
        '/api/v2/projects/<project_id:([a-zA-Z0-9-_]+)>/<parent_type:(time-records|milestones)>/<parent_id:([a-zA-Z0-9-_]+)>/comments',
        handler=Comments,
        methods=['GET', 'POST']
    ), webapp2.Route(
        '/api/v2/projects/<project_id:([a-zA-Z0-9-_]+)>/comments',
        handler=Comments,
        methods=['GET', 'POST']
    ), webapp2.Route(
        '/api/v2/projects/<project_id:([a-zA-Z0-9-_]+)>/comments/<comment_id:([a-zA-Z0-9-_]+)>',
        handler=Comments,
        methods=['PUT', 'DELETE']
    ), webapp2.Route(
        '/api/v2/projects/<project_id:([a-zA-Z0-9-_]+)>/milestones',
        handler=Milestones,
        methods=['GET', 'POST']
    ), webapp2.Route(
        '/api/v2/projects/<project_id:([a-zA-Z0-9-_]+)>/milestones/<milestone_id:([a-zA-Z0-9-_]+)>',
        handler=Milestones,
        methods=['GET', 'PUT', 'DELETE']
    ), webapp2.Route(
        '/api/v2/projects/<project_id:([a-zA-Z0-9-_]+)>/labels',
        handler=Labels,
        methods=['GET', 'POST']
    ), webapp2.Route(
        '/api/v2/projects/<project_id:([a-zA-Z0-9-_]+)>/labels/<label_id:([a-zA-Z0-9-_]+)>',
        handler=Labels,
        methods=['PUT', 'DELETE']
    ), webapp2.Route(
        '/api/v2/projects/<project_id:([a-zA-Z0-9-_]+)>/milestones/<milestone_id:([a-zA-Z0-9-_]+)>/labels',
        handler=Labels,
        methods=['GET', 'POST']
    ), webapp2.Route(
        '/api/v2/projects/<project_id:([a-zA-Z0-9-_]+)>/milestones/<milestone_id:([a-zA-Z0-9-_]+)>/labels/<label_id:([a-zA-Z0-9-_]+)>',
        handler=Labels,
        methods=['DELETE']
    )
])


def error_handler_unauthorized(request, response, exception):
    """ HTTP/1.1 401 Unauthorized """
    logging.exception(exception)
    response.content_type = 'application/json'
    response.set_status(401)
    response.write(json.dumps({
        'status': 401,
        'message': 'HTTP/1.1 401 Unauthorized'
    }))


def error_handler_server_error(request, response, exception):
    """ HTTP/1.1 500 Internal Server Error """
    logging.exception(exception)
    response.content_type = 'application/json'
    response.set_status(500)
    response.write(json.dumps({
        'status': 500,
        'message': 'HTTP/1.1 500 Internal Server Error'
    }))


app.error_handlers[401] = error_handler_unauthorized
app.error_handlers[500] = error_handler_server_error