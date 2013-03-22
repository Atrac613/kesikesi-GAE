# -*- coding: utf-8 -*-

import webapp2

from google.appengine.api import users

from i18NRequestHandler import I18NRequestHandler

from kesikesi_db import UserList

class WelcomePage(I18NRequestHandler):
    def get(self, version='v1'):
        action = self.request.get('action')
        if action not in ('logout'):
            action = None

        if version not in ('v1', 'v2'):
            return self.error(501)
            
        user = users.get_current_user()
        if user is not None:
            return self.redirect('/page/%s/archives?action=login' % version)
            
        template_values = {
            'action': action,
            'version': version
        }
        
        self.render_template('page/welcome.html', template_values)
        
class LoginPage(I18NRequestHandler):
    def get(self, version='v1'):
        
        device_id = self.request.get('id')
        
        if version not in ('v1', 'v2'):
            return self.error(501)
        
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
                
                return self.render_template('page/account_locked.html', template_values)
                
        if version == 'v2':
            self.redirect('/page/v2/auth?success=True')
        else:
            self.redirect('/page/archives?action=login')

class StartPage(I18NRequestHandler):
    def get(self, version='v1'):
        user = users.get_current_user()
        
        if version not in ('v1', 'v2'):
            return self.error(501)
        
        action = self.request.get('action')
        if action not in ('login'):
            action = None
            
        account = user.email()
        logout_url = users.create_logout_url('/page/%s/welcome?action=logout' % version)
            
        template_values = {
            'account': account,
            'logout_url': logout_url,
            'action': action,
            'version': version
        }
        
        self.render_template('page/start.html', template_values)

class AuthPage(I18NRequestHandler):
    def get(self, version='v2'):
        
        if version not in ('v2'):
            return self.error(501)
        
        success = self.request.get('success')
        if success == 'True':
            template_values = {
            }
            
            self.render_template('page/auth_success.html', template_values)
        else:
            self.redirect('/page/v2/login')

class SchemeTestPage(I18NRequestHandler):
    def get(self):

        template_values = {
        }
        
        self.render_template('page/scheme_test.html', template_values)
        
app = webapp2.WSGIApplication(
                              [('/page/welcome', WelcomePage), # deprecated
                               ('/page/(.*)/welcome', WelcomePage),
                               ('/page/login', LoginPage), # deprecated
                               ('/page/(.*)/login', LoginPage),
                               ('/page/start', StartPage), # deprecated
                               ('/page/(.*)/start', StartPage),
                               ('/page/(.*)/auth', AuthPage),
                               ('/page/test', SchemeTestPage)],
                              debug=False)