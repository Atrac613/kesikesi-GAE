# -*- coding: utf-8 -*-

import os
import hashlib
import logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.api import memcache
from google.appengine.api import users

from django.utils import simplejson

from kesikesi_db import ArchiveList
from kesikesi_db import MaskImage
from kesikesi_db import UserList

from config import SECRET_MASK_KEY
from config import SECRET_IMAGE_KEY

class MainPage(webapp.RequestHandler):
    def get(self, image_key):
        if image_key == '' or len(image_key) != 6:
            return self.error(404)
        
        archive_list = memcache.get('archive_%s' % image_key)
        if archive_list is None:
            archive_list_query = ArchiveList().all()
            archive_list_query.filter('image_key =', image_key)
            archive_list_query.filter('delete_flg =', False)
            archive_list = archive_list_query.get()
            
            memcache.add('archive_%s' % image_key, archive_list, 3600)
            
            logging.info('Archive from datastore.')
        else:
            logging.info('Archive from memcache.')
        
        if archive_list is None:
            return self.error(404)
        
        mask_image_key = hashlib.md5('%s-%s' % (SECRET_MASK_KEY, image_key)).hexdigest()
        read_count = memcache.get('count_mask_%s' % mask_image_key)
        if read_count is None:
            mask_image_query = MaskImage().all()
            mask_image_query.filter('access_key =', mask_image_key)
            mask_image = mask_image_query.get()
            
            if mask_image is not None:
                read_count = mask_image.read_count
                
                memcache.add('count_mask_%s' % mask_image_key, mask_image.read_count, 3600)
                logging.info('Count mask add. id: %s' % image_key)
            else:
                read_count = 0
        
        is_owner = False
        user = users.get_current_user()
        if user:
            if archive_list.account.google_account == user:
                is_owner = True
        
        template_values = {
            'image_key': image_key,
            'read_count': read_count,
            'is_owner': is_owner
        }
        
        user_agent = self.request.headers.get('user_agent')
        logging.info('UserAgent: %s' % user_agent)
        if 'Mobile' in user_agent and ('Safari' in user_agent or 'AppleWebKit' in user_agent):
            if 'Safari' in user_agent:
                safari = True
            else:
                safari = False
            
            if 'AppleWebKit' in user_agent:
                webkit = True
            else:
                webkit = False
                
            template_values['safari'] = safari
            template_values['webkit'] = webkit
                
            if 'iPad' in user_agent:
                path = os.path.join(os.path.dirname(__file__), 'templates/image.html')
            else:
                path = os.path.join(os.path.dirname(__file__), 'templates/image_ios.html')
        else:
            path = os.path.join(os.path.dirname(__file__), 'templates/image.html')
        
        self.response.out.write(template.render(path, template_values))

    def post(self, image_key):
        if image_key == '' or len(image_key) != 6:
            return self.error(404)
        
        archive_list_query = ArchiveList().all()
        archive_list_query.filter('image_key =', image_key)
        archive_list_query.filter('delete_flg =', False)
        archive_list = archive_list_query.get()
        
        if archive_list is None:
            return self.error(404)
        
        mode = self.request.get('mode')
        
        user = users.get_current_user()
        if user:
            if archive_list.account.google_account == user:
                if mode == 'delete':
                    archive_list.delete_flg = True
                    archive_list.put()
                    
                    mask_image_key = hashlib.md5('%s-%s' % (SECRET_MASK_KEY, image_key)).hexdigest()
                    original_image_key = hashlib.md5('%s-%s' % (SECRET_IMAGE_KEY, image_key)).hexdigest()
        
                    memcache.delete('cached_mask_%s' % mask_image_key)
                    memcache.delete('cached_original_%s' % original_image_key)
                    memcache.delete('cached_image_%s' % image_key)
                    
                    for style in ('icon48', 'icon120', 'size240', 'size300'):
                        memcache.delete('cached_image_%s_%s' % (image_key, style))
                        
                    data = {'status': True}
                    
                    json = simplejson.dumps(data, ensure_ascii=False)
                    self.response.content_type = 'application/json'
                    self.response.out.write(json)

application = webapp.WSGIApplication(
                                     [('/(.*)', MainPage)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()