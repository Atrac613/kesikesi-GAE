# -*- coding: utf-8 -*-

import os
import hashlib
import logging
import uuid

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.api import images
from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.api import taskqueue

from django.utils import simplejson 

from kesikesi_db import ArchiveList
from kesikesi_db import OriginalImage
from kesikesi_db import MaskImage
from kesikesi_db import UserList

class SettingsPage(webapp.RequestHandler):
    def get(self):
        user_id = self.request.get('id')
        
        template_values = {
            'user_id': user_id
        }
        
        path = os.path.join(os.path.dirname(__file__), 'templates/page/settings/index.html')
        self.response.out.write(template.render(path, template_values))

class DeleteAllPhotosPage(webapp.RequestHandler):
    def get(self):

        status = self.request.get('status')
        if status == '1':
            status = True
        else:
            status = False
        
        template_values = {
            'status': status
        }
        
        path = os.path.join(os.path.dirname(__file__), 'templates/page/settings/delete_all_photos.html')
        self.response.out.write(template.render(path, template_values))

    def post(self):
        user = users.get_current_user()
        
        mode = self.request.get('mode')
        delete = self.request.get('delete')
        
        user_list = UserList.all().filter('google_account =', user).filter('status =', 'stable').get()
        if user_list is None:
            return self.error(401)
        
        status = False
        if mode == 'delete':
            if delete == '1':
                try:
                    taskqueue.add(url='/task/delete_all_photos', params={'id': user_list.key().id()})
                    status = True
                except:
                    status = False
                    logging.error('Taskqueue add failed.')
                    
        self.redirect('/page/settings/delete_all_photos?status=%d' % status)

application = webapp.WSGIApplication(
                                     [('/page/settings', SettingsPage),
                                      ('/page/settings/delete_all_photos', DeleteAllPhotosPage)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()