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
from google.appengine.api import users

from django.utils import simplejson 

from kesikesi_db import ArchiveList
from kesikesi_db import OriginalImage
from kesikesi_db import MaskImage
from kesikesi_db import UserList

from config import SECRET_IMAGE_KEY
from config import SECRET_MASK_KEY

from common import convert_square
from common import gen_imagekey

class APITestPage(webapp.RequestHandler):
    def get(self):

        template_values = {
        }
        
        path = os.path.join(os.path.dirname(__file__), 'templates/api_test.html')
        self.response.out.write(template.render(path, template_values))

class UploadAPI(webapp.RequestHandler):
    def post(self):
        user = users.get_current_user()
        
        data = {}
        org_image = self.request.get('original_image')
        msk_image = self.request.get('mask_image')
        mask_mode = self.request.get('mask_mode')
        access_code = self.request.get('access_code')
        
        logging.info('original_image: %d' % len(org_image))
        logging.info('mask_image: %d' % len(msk_image))
        logging.info('User: %s' % user.email())
        
        user_list = UserList.all().filter('google_account =', user).filter('status =', 'stable').get()
        if user_list is None:
            return self.error(401)
        
        if len(mask_mode) == 0:
            mask_mode = 'scratch'
        
        mask_mode_list = ['scratch', 'accelerometer1', 'accelerometer2', 'sound_level', 'barcode']
        
        if org_image and msk_image and mask_mode in mask_mode_list:
            #image_key = hashlib.md5('%s' % uuid.uuid4()).hexdigest()[0:6]
            image_key = gen_imagekey()
            
            archive_list = ArchiveList()
            archive_list.image_key = image_key
            archive_list.account = user_list.key()
            archive_list.delete_flg = False
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
                memcache.add('cached_original_%s' % image_id, 404, 3600)
                return self.error(404)
            
            if original_image.archive_list_key.delete_flg:
                memcache.add('cached_original_%s' % image_id, 404, 3600)
                return self.error(404)
            
            img = images.Image(original_image.image)
            img.resize(width=320)
            img.im_feeling_lucky()
            thumbnail = img.execute_transforms(output_encoding=images.PNG)
            
            memcache.add('cached_original_%s' % image_id, thumbnail, 3600)
            
            logging.info('Original from DB. id: %s' % image_id)
        else:
            logging.info('Original from memcache. id: %s' % image_id)
            
            if thumbnail == 404:
                return self.error(404)
        
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
            memcache.add('cached_mask_%s' % image_id, 404, 3600)
            return self.error(404)
        
        if mask_image.archive_list_key.delete_flg:
            memcache.add('cached_mask_%s' % image_id, 404, 3600)
            return self.error(404)
        
        # Count UP
        mask_image.read_count += 1
        mask_image.put()
        
        logging.info('Read Count: %d' % mask_image.read_count)
        
        if memcache.get('count_mask_%s' % image_id) is not None:
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
            
            if thumbnail == 404:
                return self.error(404)
            
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
        
        if mask_image.archive_list_key.delete_flg:
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
        
        style = self.request.get('style')
        if style in ('icon48', 'icon120', 'size240', 'size300'):
            cache_key = 'cached_image_%s_%s' % (image_key, style)
        else:
            style = None
            cache_key = 'cached_image_%s' % image_key
            
        logging.info('memcache_key: %s' % cache_key)
        thumbnail = memcache.get(cache_key)
            
        if thumbnail is None:
            archive_list_query = ArchiveList().all()
            archive_list_query.filter('image_key =', image_key)
            archive_list_query.filter('delete_flg =', False)
            archive_list = archive_list_query.get()
            
            if archive_list is None:
                memcache.add(cache_key, 404, 3600)
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
            
            width = 320
            if style is not None:
                if style == 'size240':
                    width = 240
                elif style == 'size300':
                    width = 300
                    
            img.resize(width=width)
            img.im_feeling_lucky()
            thumbnail = img.execute_transforms(output_encoding=images.PNG)
            
            if style is not None:
                if style == 'icon48':
                    thumbnail = convert_square(thumbnail, 48, 48)
                elif style == 'icon120':
                    thumbnail = convert_square(thumbnail, 120, 120)
            
            memcache.add(cache_key, thumbnail, 3600)
            
            logging.info('Image from DB. image_key: %s' % image_key)
        else:
            logging.info('Image from memcache. image_key: %s' % image_key)
            
            if thumbnail == 404:
                return self.error(404)
        
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
                                      ('/api/api_test', APITestPage)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()