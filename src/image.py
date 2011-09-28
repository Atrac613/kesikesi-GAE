# -*- coding: utf-8 -*-

import os
import hashlib
import logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.api import memcache

from kesikesi_db import ArchiveList
from kesikesi_db import MaskImage

from config import SECRET_MASK_KEY

class MainPage(webapp.RequestHandler):
    def get(self, image_key):
        if image_key == '' or len(image_key) != 6:
            return self.error(404)
        
        archive_list_query = ArchiveList().all()
        archive_list_query.filter('image_key =', image_key)
        archive_list = archive_list_query.get()
        
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
        
        template_values = {
            'image_key': image_key,
            'read_count': read_count
        }
        
        user_agent = self.request.headers.get('user_agent')
        if 'Mobile' in user_agent and 'Safari' in user_agent:
            path = os.path.join(os.path.dirname(__file__), 'templates/image_ios.html')
        else:
            path = os.path.join(os.path.dirname(__file__), 'templates/image.html')
        
        self.response.out.write(template.render(path, template_values))


application = webapp.WSGIApplication(
                                     [('/(.*)', MainPage)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()