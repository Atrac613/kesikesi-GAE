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
from django.utils import simplejson 

from kesikesi_db import ArchiveList
from kesikesi_db import OriginalImage
from kesikesi_db import MaskImage
from kesikesi_db import UserList

from config import SECRET_IMAGE_KEY
from config import SECRET_MASK_KEY

class SettingsPage(webapp.RequestHandler):
    def get(self):
        user_id = self.request.get('id')
        
        template_values = {
            'user_id': user_id
        }
        
        path = os.path.join(os.path.dirname(__file__), 'templates/page/settings.html')
        self.response.out.write(template.render(path, template_values))

class GooglePage(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        account = user.email()
        
        mode = self.request.get('mode')
        user_id = self.request.get('id')
        
        user_list = UserList.all().filter('user_id =', user_id).filter('google_account =', user).get()
        if user_list is not None:
            connected = True
        else:
            connected = False
            
        if mode == 'connect':
            if user_list is None:
                user_list = UserList()
                user_list.user_id = user_id
                user_list.google_account = user
                user_list.put()
                
                connected = True
            
        elif mode == 'disconnect':
            user_list.delete()
            
            connected = False
        
        template_values = {
            'account': account,
            'user_id': user_id,
            'connected': connected
        }
        
        path = os.path.join(os.path.dirname(__file__), 'templates/page/google.html')
        self.response.out.write(template.render(path, template_values))


application = webapp.WSGIApplication(
                                     [('/page/settings', SettingsPage),
                                      ('/page/settings/google', GooglePage)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()