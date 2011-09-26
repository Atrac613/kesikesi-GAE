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

class ArchivePage(webapp.RequestHandler):
    def get(self):
        user_id = self.request.get('id')
        
        archive_list_query = ArchiveList().all()
        archive_list_query.filter('user_id =', user_id)
        archive_list_query.order('-created_at')
        
        archive_list = archive_list_query.fetch(25)
        
        data = []
        for image in archive_list:
            data.append({'image_key': image.image_key, 'created_at': image.created_at.strftime('%Y-%m-%dT%H:%M:%S+0000')})
        
        template_values = {
            'archive_list': data
        }
        
        path = os.path.join(os.path.dirname(__file__), 'templates/page/archive.html')
        self.response.out.write(template.render(path, template_values))

application = webapp.WSGIApplication(
                                     [('/page/archive', ArchivePage)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()