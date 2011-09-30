# -*- coding: utf-8 -*-

import os
import hashlib
import logging
import uuid
import datetime

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.api import images
from google.appengine.api import memcache
from django.utils import simplejson 

from kesikesi_db import ArchiveList
from kesikesi_db import OriginalImage
from kesikesi_db import MaskImage

from config import SECRET_IMAGE_KEY
from config import SECRET_MASK_KEY

from common import get_related_ids

class ArchivePage(webapp.RequestHandler):
    def get(self):
        user_id = self.request.get('id')
        date = self.request.get('date')
        
        related_user_id_list = get_related_ids(user_id)
        logging.info('Related id: %s' % related_user_id_list)
        
        archive_list_query = ArchiveList().all()
        archive_list_query.filter('user_id IN', related_user_id_list)
        if date != '':
            archive_list_query.filter('created_at <', datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S'))
        archive_list_query.order('-created_at')
        
        archive_list = archive_list_query.fetch(2)
        
        data = []
        for image in archive_list:
            data.append({'image_key': image.image_key, 'created_at': image.created_at.strftime('%Y-%m-%dT%H:%M:%S+0000')})
            date = image.created_at.strftime('%Y-%m-%d %H:%M:%S')
            logging.info('date: %s' % date)
        
        read_more_hide = False
        if date != '':
            archive_list_query.filter('created_at <', datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S'))
            archive_list = archive_list_query.fetch(2)
            if len(archive_list) <= 0:
                read_more_hide = True
        
        template_values = {
            'archive_list': data,
            'user_id': user_id,
            'readMoreHide': read_more_hide,
            'date': date
        }
        
        path = os.path.join(os.path.dirname(__file__), 'templates/page/archive.html')
        self.response.out.write(template.render(path, template_values))

class ArchiveReadMoreAPI(webapp.RequestHandler):
    def post(self):
        user_id = self.request.get('id')
        logging.info('user_id: %s' % user_id)
        
        date = self.request.get('date')
        
        related_user_id_list = get_related_ids(user_id)
        logging.info('Related id: %s' % related_user_id_list)
        
        archive_list_query = ArchiveList().all()
        
        if date != '':
            archive_list_query.filter('created_at <', datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S'))
        archive_list_query.order('-created_at')
        
        archive_list = archive_list_query.fetch(2)
        
        data = []
        for image in archive_list:
            data.append({'image_key': image.image_key, 'created_at': image.created_at.strftime('%Y-%m-%dT%H:%M:%S+0000')})
            date = image.created_at.strftime('%Y-%m-%d %H:%M:%S')
            #logging.info('date: %s' % date)
            
        archive_list_query = ArchiveList().all()
        archive_list_query.filter('created_at <', datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S'))
        archive_list_query.order('-created_at')
        archive_list = archive_list_query.fetch(2)
        
        if len(archive_list) <= 0:
            date = False
            
        data = {'data': data, 'date': date}
        
        json = simplejson.dumps(data, ensure_ascii=False)
        self.response.content_type = 'application/json'
        self.response.out.write(json)

application = webapp.WSGIApplication(
                                     [('/page/archive', ArchivePage),
                                      ('/page/api/archive_read_more', ArchiveReadMoreAPI)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()