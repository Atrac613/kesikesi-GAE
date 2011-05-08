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

class APITestPage(webapp.RequestHandler):
    def get(self):

        template_values = {
        }
        
        path = os.path.join(os.path.dirname(__file__), 'templates/api_test.html')
        self.response.out.write(template.render(path, template_values))

class UploadAPI(webapp.RequestHandler):
    def post(self):
        
        data = {}
        org_image = self.request.get('original_image')
        msk_image = self.request.get('mask_image')
        user_id = self.request.get('user_id')
        mask_mode = self.request.get('mask_mode')
        access_code = self.request.get('access_code')
        
        logging.info('original_image: %d' % len(org_image))
        logging.info('mask_image: %d' % len(msk_image))
        logging.info('user_id: %s' % user_id)
        
        if len(mask_mode) == 0:
            mask_mode = 'scratch'
        
        mask_mode_list = ['scratch', 'accelerometer1', 'accelerometer2', 'sound_level', 'barcode']
        
        if org_image and msk_image and user_id and mask_mode in mask_mode_list:
            image_key = hashlib.md5('%s' % uuid.uuid4()).hexdigest()[0:6]
            
            archive_list = ArchiveList()
            archive_list.image_key = image_key
            archive_list.user_id = user_id
            archive_list.put()
            
            original_image = OriginalImage()
            original_image.archive_list_key = archive_list.key()
            original_image.image = db.Blob(org_image)
            original_image.access_key = hashlib.md5('%s-%s' % (SECRET_IMAGE_KEY, image_key)).hexdigest()
            original_image.put()
            
            mask_image = MaskImage()
            mask_image.mask_mode = mask_mode
            mask_image.archive_list_key = archive_list.key()
            mask_image.image = db.Blob(msk_image)
            mask_image.access_key = hashlib.md5('%s-%s' % (SECRET_MASK_KEY, image_key)).hexdigest()
            mask_image.read_count = 0
            mask_image.access_code = access_code
            mask_image.put()
            
            data = {'image_key': image_key}
        else:
            data = {'image_key': False}
            
        json = simplejson.dumps(data, ensure_ascii=False)
        self.response.content_type = 'application/json'
        self.response.out.write(json)
        
class GetOriginalImageAPI(webapp.RequestHandler):
    def get(self):
      
        image_id = self.request.get('id')
        if image_id == '':
            return self.error(404)
        
        thumbnail = memcache.get('cached_original_%s' % image_id)
        if thumbnail is None:
            original_image_query = OriginalImage().all()
            original_image_query.filter('access_key =', image_id)
            original_image = original_image_query.get()
            
            if original_image is None:
                return self.error(404)
            
            img = images.Image(original_image.image)
            img.resize(width=320)
            img.im_feeling_lucky()
            thumbnail = img.execute_transforms(output_encoding=images.PNG)
            
            memcache.add('cached_original_%s' % image_id, thumbnail, 3600)
            
            logging.info('Original from DB. id: %s' % image_id)
        else:
            logging.info('Original from memcache. id: %s' % image_id)
        
        self.response.headers['Content-Type'] = 'image/png'
        self.response.out.write(thumbnail)

class GetMaskImageAPI(webapp.RequestHandler):
    def get(self):
      
        image_id = self.request.get('id')
        if image_id == '':
            return self.error(404)
        
        mask_image_query = MaskImage().all()
        mask_image_query.filter('access_key =', image_id)
        mask_image = mask_image_query.get()
        
        if mask_image is None:
            return self.error(404)
        
        # Count UP
        mask_image.read_count += 1
        mask_image.put()
        
        if memcache.get('count_mask_%s' % image_id):
            memcache.replace('count_mask_%s' % image_id, mask_image.read_count, 3600)
            logging.info('Count mask replace. id: %s' % image_id)
        else:
            memcache.add('count_mask_%s' % image_id, mask_image.read_count, 3600)
            logging.info('Count mask add. id: %s' % image_id)
        
        thumbnail = memcache.get('cached_mask_%s' % image_id)
        if thumbnail is None:
            img = images.Image(mask_image.image)
            img.resize(width=320)
            img.im_feeling_lucky()
            thumbnail = img.execute_transforms(output_encoding=images.PNG)
            
            memcache.add('cached_mask_%s' % image_id, thumbnail, 3600)
            
            logging.info('Mask from db. id: %s' % image_id)
        else:
            logging.info('Mask from memcache. id: %s' % image_id)
            
        self.response.headers['Content-Type'] = 'image/png'
        self.response.out.write(thumbnail)

class GetMaskModeAPI(webapp.RequestHandler):
    def get(self):
      
        image_id = self.request.get('id')
        if image_id == '':
            return self.error(404)
        
        mask_image_query = MaskImage().all()
        mask_image_query.filter('access_key =', image_id)
        mask_image = mask_image_query.get()
        
        if mask_image is None:
            return self.error(404)
        
        if mask_image.mask_mode is None:
            mask_mode = 'scratch'
        else:
            mask_mode = mask_image.mask_mode
        
        data = {'mask_mode': mask_mode, 'access_code': mask_image.access_code}
        
        json = simplejson.dumps(data, ensure_ascii=False)
        self.response.content_type = 'application/json'
        self.response.out.write(json)

class GetImageAPI(webapp.RequestHandler):
    def get(self):
      
        image_key = self.request.get('id')
        if image_key == '':
            return self.error(404)
        
        thumbnail = memcache.get('cached_image_%s' % image_key)
        if thumbnail is None:
            archive_list_query = ArchiveList().all()
            archive_list_query.filter('image_key =', image_key)
            archive_list = archive_list_query.get()
            
            if archive_list is None:
                return self.error(404)
            
            mask_image_key = hashlib.md5('%s-%s' % (SECRET_MASK_KEY, image_key)).hexdigest()
            mask_image_query = MaskImage().all()
            mask_image_query.filter('access_key =', mask_image_key)
            mask_image = mask_image_query.get()
            
            original_image_key = hashlib.md5('%s-%s' % (SECRET_IMAGE_KEY, image_key)).hexdigest()
            original_image_query = OriginalImage().all()
            original_image_query.filter('access_key =', original_image_key)
            original_image = original_image_query.get()
            
            if mask_image is None or original_image is None:
                return self.error(404)
            
            all_images = []
            all_images.append((original_image.image, 0, 0, 1.0, images.TOP_LEFT))
            all_images.append((mask_image.image, 0, 0, 1.0, images.TOP_LEFT))
            
            image_c = images.composite(all_images, 320, 416, 0, images.PNG, 100)
            
            img = images.Image(image_c)
            img.resize(width=320)
            img.im_feeling_lucky()
            thumbnail = img.execute_transforms(output_encoding=images.PNG)
            
            memcache.add('cached_image_%s' % image_key, thumbnail, 3600)
            
            logging.info('Image from DB. image_key: %s' % image_key)
        else:
            logging.info('Image from memcache. image_key: %s' % image_key)
        
        self.response.headers['Content-Type'] = 'image/png'
        self.response.out.write(thumbnail)
    
class GetArchiveListAPI(webapp.RequestHandler):
    def get(self):
        
        user_id = self.request.get('id')
        
        archive_list_query = ArchiveList().all()
        archive_list_query.filter('user_id =', user_id)
        archive_list_query.order('-created_at')
        
        archive_list = archive_list_query.fetch(25)
        
        data = []
        for image in archive_list:
            data.append({'image_key': image.image_key, 'created_at': image.created_at.strftime('%Y-%m-%dT%H:%M:%S+0000')})
        
        json = simplejson.dumps(data, ensure_ascii=False)
        self.response.content_type = 'application/json'
        self.response.out.write(json)
        
class DeleteImageAPI(webapp.RequestHandler):
    def get(self):
      
        image_key = self.request.get('id')
        user_id = self.request.get('user_id')
        
        if image_key == '':
            return self.error(404)
        
        archive_list_query = ArchiveList().all()
        archive_list_query.filter('image_key =', image_key)
        archive_list_query.filter('user_id =', user_id)
        archive_list = archive_list_query.get()
        
        if archive_list is None:
            return self.error(404)
        
        mask_image_key = hashlib.md5('%s-%s' % (SECRET_MASK_KEY, image_key)).hexdigest()
        mask_image_query = MaskImage().all()
        mask_image_query.filter('access_key =', mask_image_key)
        mask_image = mask_image_query.get()
        mask_image.delete()
        
        original_image_key = hashlib.md5('%s-%s' % (SECRET_IMAGE_KEY, image_key)).hexdigest()
        original_image_query = OriginalImage().all()
        original_image_query.filter('access_key =', original_image_key)
        original_image = original_image_query.get()
        original_image.delete()
        
        archive_list.delete()
        
        memcache.delete('cached_mask_%s' % mask_image_key)
        memcache.delete('cached_original_%s' % original_image_key)
        memcache.delete('cached_image_%s' % image_key)
        
        data = {'state': True}
            
        json = simplejson.dumps(data, ensure_ascii=False)
        self.response.content_type = 'application/json'
        self.response.out.write(json)

application = webapp.WSGIApplication(
                                     [('/api/upload', UploadAPI),
                                      ('/api/get_original_image', GetOriginalImageAPI),
                                      ('/api/get_mask_image', GetMaskImageAPI),
                                      ('/api/get_mask_mode', GetMaskModeAPI),
                                      ('/api/get_image', GetImageAPI),
                                      ('/api/get_archive_list', GetArchiveListAPI),
                                      ('/api/delete_image', DeleteImageAPI),
                                      ('/api/api_test', APITestPage)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()