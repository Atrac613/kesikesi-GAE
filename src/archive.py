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
        more = self.request.get('more')
        
        related_user_id_list  = get_related_ids(user_id)
        logging.info('Related id: %s' % related_user_id_list)
        
        archive_list_query = ArchiveList().all()
        
        # workaround
        archive_list_query.filter('user_id IN', related_user_id_list)
        archive_list_query.order('-created_at')
        
        archive_list = archive_list_query.fetch(50)
        
        #cursor = archive_list_query.cursor()
        #memcache.add('cursor_archive_%s_0' % user_id, cursor, 3600)
        
        data = []
        for image in archive_list:
            data.append({'image_key': image.image_key, 'created_at': image.created_at.strftime('%Y-%m-%dT%H:%M:%S+0000')})
        
        # workaround
        #archive_list_query.with_cursor(cursor)
        #archive_list = archive_list_query.fetch(2)
        #if len(archive_list) <= 0:
        #    read_more_hide = True
        #else:
        #   read_more_hide = False;
        read_more_hide = True;
        
        template_values = {
            'archive_list': data,
            'user_id': user_id,
            'readMoreHide': read_more_hide
        }
        
        path = os.path.join(os.path.dirname(__file__), 'templates/page/archive.html')
        self.response.out.write(template.render(path, template_values))

class ArchiveReadMoreAPI(webapp.RequestHandler):
    def post(self):
        user_id = self.request.get('id')
        logging.info('user_id: %s' % user_id)
        
        page_id = self.request.get('page_id')
        if page_id != '':
            page_id = int(page_id)
        else:
            page_id = 0
        
        archive_list_query = ArchiveList().all()
        archive_list_query.filter('user_id =', user_id)
        archive_list_query.order('-created_at')
        
        last_cursor = memcache.get('cursor_archive_%s_%d' % (user_id, page_id))
        if last_cursor is not None:
            archive_list_query.with_cursor(last_cursor)
        
        archive_list = archive_list_query.fetch(2)
        
        cursor = archive_list_query.cursor()
        if last_cursor:
            memcache.delete('cursor_archive_%s_%d' % (user_id, page_id))
        memcache.add('cursor_archive_%s_%d' % (user_id, page_id+1), cursor, 3600)
        
        data = []
        for image in archive_list:
            data.append({'image_key': image.image_key, 'created_at': image.created_at.strftime('%Y-%m-%dT%H:%M:%S+0000')})
        
        archive_list_query.with_cursor(cursor)
        archive_list = archive_list_query.fetch(2)
        if len(archive_list) <= 0:
            page_id = False
        else:
            page_id = page_id + 1;
            
        data = {'page_id': page_id, 'data':data}
        
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