# -*- coding: utf-8 -*-

import hashlib
import logging
import uuid

import webapp2
import json

from google.appengine.ext import db
from google.appengine.api import images
from google.appengine.api import memcache
from google.appengine.api import users


from kesikesi_db import ArchiveList
from kesikesi_db import OriginalImage
from kesikesi_db import MaskImage
from kesikesi_db import UserList

from config import SECRET_IMAGE_KEY
from config import SECRET_MASK_KEY

from common import convert_square
from common import gen_imagekey

from i18NRequestHandler import I18NRequestHandler

class APITestPage(I18NRequestHandler):
    def get(self):

        template_values = {
        }
        
        self.render_template('api_test.html', template_values)
        
class UploadAPI(I18NRequestHandler):
    def post(self, version='v1'):
        user = users.get_current_user()
        
        if version not in ('v1', 'v2'):
            return self.error(501)
        
        data = {}
        
        tmp_image_key = self.request.get('tmp_image_key')
        
        if tmp_image_key:
            logging.info('tmp_image_key: %s' % tmp_image_key)
            tmp_org_image = memcache.get('tmp_org_%s' % tmp_image_key)
            tmp_msk_image = memcache.get('tmp_msk_%s' % tmp_image_key)
            
            if tmp_org_image and tmp_msk_image:
                org_image = tmp_org_image['org_image']
                msk_image = tmp_msk_image['msk_image']
                mask_mode = tmp_msk_image['mask_mode']
                mask_type = tmp_msk_image['mask_type']
                access_code = tmp_msk_image['access_code']
            else:
                return self.error(500)
            
        else:
            org_image = self.request.get('original_image')
            msk_image = self.request.get('mask_image')
            mask_mode = self.request.get('mask_mode')
            mask_type = self.request.get('mask_type')
            access_code = self.request.get('access_code')
        
        comment = self.request.get('comment')
        
        logging.info('original_image: %d' % len(org_image))
        logging.info('mask_image: %d' % len(msk_image))
        logging.info('User: %s' % user.email())
        logging.info('Comment: %s', comment)
        logging.info('MaskType: %s', mask_type)
        
        user_list = UserList.all().filter('google_account =', user).filter('status =', 'stable').get()
        if user_list is None:
            return self.error(401)
        
        if len(mask_mode) == 0:
            mask_mode = 'scratch'
        
        mask_mode_list = ['scratch', 'accelerometer1', 'accelerometer2', 'sound_level', 'barcode']
        
        mask_type_list = ['black', 'mosaic', 'caution', 'zebra', 'note']
        if mask_type not in mask_type_list:
            mask_type = 'black'
        
        if org_image and msk_image and mask_mode in mask_mode_list:
            #image_key = hashlib.md5('%s' % uuid.uuid4()).hexdigest()[0:6]
            image_key = gen_imagekey()
            
            # workaround
            tmp_archive = ArchiveList.all().filter('image_key =', image_key).get()
            if tmp_archive is not None:
                return self.error(500)
            
            archive_list = ArchiveList()
            archive_list.image_key = image_key
            archive_list.comment = comment
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
            mask_image.mask_type = mask_type
            mask_image.put()
            
            data = {'image_key': image_key}
        else:
            data = {'image_key': False}
            
        json_data = json.dumps(data, ensure_ascii=False)
        self.response.content_type = 'application/json'
        self.response.out.write(json_data)
        
class UploadImageAPI(I18NRequestHandler):
    def post(self, version='v2'):
        user = users.get_current_user()
        
        if version not in ('v2'):
            return self.error(501)
        
        data = {}
        msk_image = self.request.get('mask_image')
        org_image = self.request.get('original_image')
        mask_mode = self.request.get('mask_mode')
        mask_type = self.request.get('mask_type')
        access_code = self.request.get('access_code')
        
        logging.info('original_image: %d' % len(org_image))
        logging.info('mask_image: %d' % len(msk_image))
        logging.info('User: %s' % user.email())
        logging.info('MaskType: %s' % mask_type);
        
        user_list = UserList.all().filter('google_account =', user).filter('status =', 'stable').get()
        if user_list is None:
            return self.error(401)
        
        if org_image and msk_image:
            image_key = hashlib.md5('%s' % uuid.uuid4()).hexdigest()
            
            org_image = images.Image(org_image)
            org_image.resize(width=640)
            #org_image.im_feeling_lucky()
            new_org_image = org_image.execute_transforms(output_encoding=images.PNG)
            new_org_image = convert_square(new_org_image, 640, 640)
            
            memcache.add('tmp_org_%s' % image_key, {'org_image': new_org_image}, 3600)
            memcache.add('tmp_msk_%s' % image_key, {'msk_image': msk_image, 'mask_mode': mask_mode, 'mask_type': mask_type, 'access_code': access_code}, 3600)
            
            data = {'image_key': image_key}
        else:
            data = {'image_key': False}
            
        json_data = json.dumps(data, ensure_ascii=False)
        self.response.content_type = 'application/json'
        self.response.out.write(json_data)
        
class GetOriginalImageAPI(I18NRequestHandler):
    def get(self, version='v1'):
      
        image_id = self.request.get('id')
        if image_id == '':
            return self.error(404)
        
        if version not in ('v1', 'v2', 'v3'):
            return self.error(501)
        
        if len(image_id) == 6:
            image_id = hashlib.md5('%s-%s' % (SECRET_IMAGE_KEY, image_id)).hexdigest()
        
        thumbnail = memcache.get('cached_original_%s_%s' % (version, image_id))
        if thumbnail is None:
            original_image_query = OriginalImage().all()
            original_image_query.filter('access_key =', image_id)
            original_image = original_image_query.get()
            
            if original_image is None:
                memcache.add('cached_original_%s_%s' % (version, image_id), 404, 3600)
                return self.error(404)
            
            if original_image.archive_list_key.delete_flg:
                memcache.add('cached_original_%s_%s' % (version, image_id), 404, 3600)
                return self.error(404)
            
            img = images.Image(original_image.image)
            
            if version == 'v2':
                img.resize(width=640)
                #img.im_feeling_lucky()
                thumbnail = img.execute_transforms(output_encoding=images.PNG)
                thumbnail = convert_square(thumbnail, 640, 640)
                
                # Workaround
                img = images.Image(thumbnail)
                img.resize(width=640)
                thumbnail = img.execute_transforms(output_encoding=images.JPEG)
            else:
                img.resize(width=320)
                #img.im_feeling_lucky()
                thumbnail = img.execute_transforms(output_encoding=images.JPEG)
                #thumbnail = convert_square(thumbnail, 320, 320)
            
            memcache.add('cached_original_%s_%s' % (version, image_id), thumbnail, 3600)
            
            logging.info('Original from DB. id: %s' % image_id)
        else:
            logging.info('Original from memcache. id: %s' % image_id)
            
            if thumbnail == 404:
                return self.error(404)
        
        self.response.headers['Content-Type'] = 'image/jpeg'
        self.response.out.write(thumbnail)

class GetMaskImageAPI(I18NRequestHandler):
    def get(self, version='v1'):
      
        image_id = self.request.get('id')
        if image_id == '':
            return self.error(404)
        
        if version not in ('v1', 'v2'):
            return self.error(501)
        
        if len(image_id) == 6:
            image_id = hashlib.md5('%s-%s' % (SECRET_MASK_KEY, image_id)).hexdigest()
        
        mask_image_query = MaskImage().all()
        mask_image_query.filter('access_key =', image_id)
        mask_image = mask_image_query.get()
        
        if mask_image is None:
            memcache.add('cached_mask_%s_%s' % (version, image_id), 404, 3600)
            return self.error(404)
        
        if mask_image.archive_list_key.delete_flg:
            memcache.add('cached_mask_%s_%s' % (version, image_id), 404, 3600)
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
        
        thumbnail = memcache.get('cached_mask_%s_%s' % (version, image_id))
        if thumbnail is None:
            img = images.Image(mask_image.image)
            
            if version == 'v2':
                img.resize(width=320)
                #img.im_feeling_lucky()
                thumbnail = img.execute_transforms(output_encoding=images.PNG)
                thumbnail = convert_square(thumbnail, 320, 320)
            else:
                img.resize(width=320)
                #img.im_feeling_lucky()
                thumbnail = img.execute_transforms(output_encoding=images.PNG)
                #thumbnail = convert_square(thumbnail, 320, 320)
            
            memcache.add('cached_mask_%s_%s' % (version, image_id), thumbnail, 3600)
            
            logging.info('Mask from db. id: %s' % image_id)
        else:
            logging.info('Mask from memcache. id: %s' % image_id)
            
            if thumbnail == 404:
                return self.error(404)
            
        self.response.headers['Content-Type'] = 'image/png'
        self.response.out.write(thumbnail)

class GetMaskModeAPI(I18NRequestHandler):
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
            
        try:
            comment = mask_image.archive_list_key.comment
            if comment == '' or comment == None:
                comment = 'no comment.'
        except:
            comment = 'no comment.'
        
        data = {'mask_mode': mask_mode, 'access_code': mask_image.access_code, 'comment': comment}
        
        json_data = json.dumps(data, ensure_ascii=False)
        self.response.content_type = 'application/json'
        self.response.out.write(json_data)

class GetImageAPI(I18NRequestHandler):
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
            
            mask_image = images.Image(mask_image.image)
            mask_image.resize(width=640)
            #mask_image.im_feeling_lucky()
            new_mask_image = mask_image.execute_transforms(output_encoding=images.PNG)
            new_mask_image = convert_square(new_mask_image, 640, 640)
            
            original_image = images.Image(original_image.image)
            original_image.resize(width=640)
            #original_image.im_feeling_lucky()
            new_original_image = original_image.execute_transforms(output_encoding=images.PNG)
            new_original_image = convert_square(new_original_image, 640, 640)
            
            all_images = []
            all_images.append((new_original_image, 0, 0, 1.0, images.TOP_LEFT))
            all_images.append((new_mask_image, 0, 0, 1.0, images.TOP_LEFT))
            
            image_c = images.composite(all_images, 640, 640, 0, images.PNG, 100)
            
            img = images.Image(image_c)
            
            width = 320
            if style is not None:
                if style == 'size240':
                    width = 240
                elif style == 'size300':
                    width = 300
                    
            img.resize(width=width)
            #img.im_feeling_lucky()
            thumbnail = img.execute_transforms(output_encoding=images.JPEG)
            
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
        
        self.response.headers['Content-Type'] = 'image/jpeg'
        self.response.out.write(thumbnail)
    
class GetArchiveListAPI(I18NRequestHandler):
    def get(self):
        
        user_id = self.request.get('id')
        
        archive_list_query = ArchiveList().all()
        archive_list_query.filter('user_id =', user_id)
        archive_list_query.order('-created_at')
        
        archive_list = archive_list_query.fetch(25)
        
        data = []
        for image in archive_list:
            data.append({'image_key': image.image_key, 'created_at': image.created_at.strftime('%Y-%m-%dT%H:%M:%S+0000')})
        
        json_data = json.dumps(data, ensure_ascii=False)
        self.response.content_type = 'application/json'
        self.response.out.write(json_data)
        
class DeleteImageAPI(I18NRequestHandler):
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
            
        json_data = json.dumps(data, ensure_ascii=False)
        self.response.content_type = 'application/json'
        self.response.out.write(json_data)

app = webapp2.WSGIApplication(
                              [('/api/upload', UploadAPI), # deprecated
                               ('/api/(.*)/upload', UploadAPI),
                               ('/api/(.*)/upload_image', UploadImageAPI),
                               ('/api/get_original_image', GetOriginalImageAPI), # deprecated
                               ('/api/(.*)/get_original_image', GetOriginalImageAPI),
                               ('/api/get_mask_image', GetMaskImageAPI), # deprecated
                               ('/api/(.*)/get_mask_image', GetMaskImageAPI),
                               ('/api/get_mask_mode', GetMaskModeAPI),
                               ('/api/get_image', GetImageAPI),
                               ('/api/api_test', APITestPage)],
                              debug=False)