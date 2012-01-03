# -*- coding: utf-8 -*-

import os
import logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.api import users

#from google.appengine.dist import use_library
#use_library('django', '1.1')

os.environ['DJANGO_SETTINGS_MODULE'] = 'conf.settings'
from django.conf import settings
# Force Django to reload settings
settings._target = None

from i18NRequestHandler import I18NRequestHandler

from kesikesi_db import UserList

class WelcomePage(I18NRequestHandler):
    def get(self):
        action = self.request.get('action')
        if action not in ('logout'):
            action = None

        version = self.request.get('version')
        if version not in ('2'):
            version = 1;
            
        user = users.get_current_user()
        if user is not None:
            return self.redirect('/page/archives?action=login')
            
        template_values = {
            'action': action,
            'version': version
        }
        
        path = os.path.join(os.path.dirname(__file__), 'templates/page/welcome.html')
        self.response.out.write(template.render(path, template_values))

class LoginPage(webapp.RequestHandler):
    def get(self):
        
        device_id = self.request.get('id')
        
        version = self.request.get('version')
        if version not in ('2'):
            version = 1;
        
        user = users.get_current_user()
        
        user_list = UserList.all().filter('google_account =', user).get()
        if user_list is None:
            user_list = UserList()
            user_list.google_account = user
            user_list.device_id = device_id
            user_list.status = 'stable'
            user_list.put()
        else:
            if user_list.status != 'stable':
                logout_url = users.create_logout_url('/page/welcome?action=logout')
                
                template_values = {
                    'logout_url': logout_url
                }
                
                path = os.path.join(os.path.dirname(__file__), 'templates/page/account_locked.html')

                return self.response.out.write(template.render(path, template_values))
                
        if version == '2':
            self.redirect('/page/auth?success=True')
        else:
            self.redirect('/page/archives?action=login')

class StartPage(I18NRequestHandler):
    def get(self):
        user = users.get_current_user()
        
        action = self.request.get('action')
        if action not in ('login'):
            action = None
            
        account = user.email()
        logout_url = users.create_logout_url('/page/welcome?action=logout')
            
        template_values = {
            'account': account,
            'logout_url': logout_url,
            'action': action
        }
        
        path = os.path.join(os.path.dirname(__file__), 'templates/page/start.html')
        self.response.out.write(template.render(path, template_values))

class AuthPage(webapp.RequestHandler):
    def get(self):
        
        success = self.request.get('success')
        if success == 'True':
            template_values = {
            }
            
            path = os.path.join(os.path.dirname(__file__), 'templates/page/auth_success.html')
            self.response.out.write(template.render(path, template_values))
        else:
            self.redirect('/page/login?version=2')

class SchemeTestPage(webapp.RequestHandler):
    def get(self):

        template_values = {
        }
        
        path = os.path.join(os.path.dirname(__file__), 'templates/page/scheme_test.html')
        self.response.out.write(template.render(path, template_values))

application = webapp.WSGIApplication(
                                     [('/page/welcome', WelcomePage),
                                      ('/page/login', LoginPage),
                                      ('/page/start', StartPage),
                                      ('/page/auth', AuthPage),
                                      ('/page/test', SchemeTestPage)],
                                     debug=False)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()