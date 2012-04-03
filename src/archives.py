# -*- coding: utf-8 -*-

import os
import logging
import datetime

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.api import users

from django.utils import simplejson 

from kesikesi_db import ArchiveList
from kesikesi_db import UserList

from config import IMAGE_FETCH_COUNT

os.environ['DJANGO_SETTINGS_MODULE'] = 'conf.settings'
from django.conf import settings
# Force Django to reload settings
settings._target = None

from i18NRequestHandler import I18NRequestHandler

class ArchivesPage(I18NRequestHandler):
    def get(self, version='v1'):
        user = users.get_current_user()
        
        date = self.request.get('date')
        
        action = self.request.get('action')
        if action not in ('login'):
            action = None
            
        if version not in ('v1', 'v2'):
            return self.error(501)
        
        if version == 'v1':
            actionButton = False
        else:
            actionButton = True
            
        if user is None:
            return self.redirect('/page/%s/welcome' % version)
        
        user_list = UserList.all().filter('google_account =', user).filter('status =', 'stable').get()
        if user_list is None:
            return self.redirect('/page/%s/welcome?action=logout' % version)
        
        archive_list_query = ArchiveList().all().filter('account =', user_list.key()).filter('delete_flg =', False)
        if date != '':
            archive_list_query.filter('created_at <', datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S'))
        archive_list_query.order('-created_at')
        
        archive_list = archive_list_query.fetch(IMAGE_FETCH_COUNT)
        
        if len(archive_list) <= 0:
            return self.redirect('/page/%s/start?action=login' % version)
        
        data = []
        for image in archive_list:
            data.append({'image_key': image.image_key, 'created_at': image.created_at.strftime('%Y-%m-%dT%H:%M:%S+0000')})
            date = image.created_at.strftime('%Y-%m-%d %H:%M:%S')
            logging.info('date: %s' % date)
        
        how_to_use_it = False
        if len(archive_list) < 5:
            how_to_use_it = True
        
        load_more_hide = False
        if date != '':
            archive_list_query.filter('created_at <', datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S'))
            archive_list = archive_list_query.fetch(IMAGE_FETCH_COUNT)
            if len(archive_list) <= 0:
                load_more_hide = True
        
        account = user.email()
        logout_url = users.create_logout_url('/page/%s/welcome?action=logout' % version)
        
        template_values = {
            'archive_list': data,
            'load_more_hide': load_more_hide,
            'date': date,
            'account': account,
            'logout_url': logout_url,
            'action': action,
            'how_to_use_it': how_to_use_it,
            'version': version,
            'actionButton': actionButton
        }
        
        path = os.path.join(os.path.dirname(__file__), 'templates/page/archives.html')
        self.response.out.write(template.render(path, template_values))

class ArchivesLoadMoreAPI(webapp.RequestHandler):
    def post(self):
        user = users.get_current_user()
        
        date = self.request.get('date')
        
        user_list = UserList.all().filter('google_account =', user).filter('status =', 'stable').get()
        if user_list is None:
            return self.error(401)
        
        archive_list_query = ArchiveList().all().filter('account =', user_list.key())
        
        if date != '':
            archive_list_query.filter('created_at <', datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S'))
        archive_list_query.order('-created_at')
        
        archive_list = archive_list_query.fetch(IMAGE_FETCH_COUNT)
        
        data = []
        for image in archive_list:
            data.append({'image_key': image.image_key, 'created_at': image.created_at.strftime('%Y-%m-%dT%H:%M:%S+0000')})
            date = image.created_at.strftime('%Y-%m-%d %H:%M:%S')
            #logging.info('date: %s' % date)
            
        archive_list_query = ArchiveList().all().filter('account =', user_list.key())
        archive_list_query.filter('created_at <', datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S'))
        archive_list_query.order('-created_at')
        archive_list = archive_list_query.fetch(IMAGE_FETCH_COUNT)
        
        if len(archive_list) <= 0:
            date = False
            
        data = {'data': data, 'date': date}
        
        json = simplejson.dumps(data, ensure_ascii=False)
        self.response.content_type = 'application/json'
        self.response.out.write(json)

application = webapp.WSGIApplication(
                                     [('/page/archives', ArchivesPage), # deprecated
                                      ('/page/(.*)/archives', ArchivesPage),
                                      ('/page/api/archives_load_more', ArchivesLoadMoreAPI)],
                                     debug=False)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()