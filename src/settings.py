# -*- coding: utf-8 -*-

import logging

import webapp2

from google.appengine.api import users
from google.appengine.api import taskqueue

from kesikesi_db import UserList

from i18NRequestHandler import I18NRequestHandler

class SettingsPage(I18NRequestHandler):
    def get(self):
        user_id = self.request.get('id')
        
        user = users.get_current_user()
        account = user.email()
        
        template_values = {
            'user_id': user_id,
            'account': account
        }
        
        self.render_template('page/settings/index.html', template_values)
        
class DeleteAllPhotosPage(I18NRequestHandler):
    def get(self):
        
        user = users.get_current_user()
        account = user.email()
        
        status = self.request.get('status')
        if status == '1':
            status = True
        else:
            status = False
        
        template_values = {
            'status': status,
            'account': account
        }
        
        self.render_template('page/settings/delete_all_photos.html', template_values)
        
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

app = webapp2.WSGIApplication(
                              [('/page/settings', SettingsPage),
                               ('/page/settings/delete_all_photos', DeleteAllPhotosPage)],
                              debug=False)