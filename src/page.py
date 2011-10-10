# -*- coding: utf-8 -*-

import os
import logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.api import users

from kesikesi_db import UserList

class WelcomePage(webapp.RequestHandler):
    def get(self):
        action = self.request.get('action')
        if action not in ('logout'):
            action = None

        template_values = {
            'action': action
        }
        
        path = os.path.join(os.path.dirname(__file__), 'templates/page/welcome.html')
        self.response.out.write(template.render(path, template_values))

class LoginPage(webapp.RequestHandler):
    def get(self):
        
        device_id = self.request.get('id')
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
                
        self.redirect('/page/archives?action=login')

class StartPage(webapp.RequestHandler):
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
                                      ('/page/test', SchemeTestPage)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()