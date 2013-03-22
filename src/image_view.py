# -*- coding: utf-8 -*-

import hashlib
import logging
import datetime

import webapp2
import json

from google.appengine.api import memcache
from google.appengine.api import users

from kesikesi_db import ArchiveList
from kesikesi_db import MaskImage

from config import SECRET_MASK_KEY
from config import SECRET_IMAGE_KEY

from i18NRequestHandler import I18NRequestHandler

class MainPage(I18NRequestHandler):
    def get(self, image_key):
        if image_key == '' or len(image_key) != 6:
            return self.error(404)
        
        archive_list = memcache.get('archive_%s' % image_key)
        if archive_list is None:
            archive_list_query = ArchiveList().all()
            archive_list_query.filter('image_key =', image_key)
            archive_list = archive_list_query.get()
            
            if archive_list is None or archive_list.delete_flg:
                memcache.add('archive_%s' % image_key, 404, 3600)
                return self.error(404)
            
            memcache.add('archive_%s' % image_key, archive_list, 3600)
            
            logging.info('Archive from datastore.')
        else:
            if archive_list == 404:
                return self.error(404)
            
            logging.info('Archive from memcache.')
        
        if archive_list is None:
            return self.error(404)
        
        actionButton = self.request.get('actionButton')
        if actionButton == 'True':
            actionButton = True
        else:
            actionButton = False
        
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
                
        mask_type = memcache.get('mask_type_%s' % mask_image_key)
        if mask_type is None:
            mask_image_query = MaskImage().all()
            mask_image_query.filter('access_key =', mask_image_key)
            mask_image = mask_image_query.get()
            
            try:
                mask_type = mask_image.mask_type
            except:
                mask_type = 'black'
                
            memcache.add('mask_type_%s' % mask_image_key, mask_image.mask_type, 3600)
        
        logging.info('Mask type: %s id: %s' % (image_key, mask_type))
        
        is_owner = False
        user = users.get_current_user()
        if user:
            if archive_list.account.google_account == user:
                is_owner = True
        
        page_title = None
        try:
            comment = archive_list.comment
            if comment == '' or comment == None:
                comment = 'no comment.'
            else:
                page_title = comment
        except:
            comment = 'no comment.'
        
        template_values = {
            'image_key': image_key,
            'comment': comment,
            'read_count': read_count,
            'is_owner': is_owner,
            'page_title': page_title,
            'actionButton': actionButton,
            'mask_type': mask_type
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
                path = 'view/image.html'
            else:
                path = 'view/image_ios.html'
        else:
            path = 'view/image.html'
        
        self.render_template(path, template_values)
        
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
                    archive_list.updated_at = datetime.datetime.now()
                    archive_list.put()
                    
                    mask_image_key = hashlib.md5('%s-%s' % (SECRET_MASK_KEY, image_key)).hexdigest()
                    original_image_key = hashlib.md5('%s-%s' % (SECRET_IMAGE_KEY, image_key)).hexdigest()
        
                    memcache.delete('cached_mask_%s' % mask_image_key)
                    memcache.delete('cached_original_%s' % original_image_key)
                    memcache.delete('cached_image_%s' % image_key)
                    memcache.delete('archive_%s' % image_key)
                    
                    for style in ('icon48', 'icon120', 'size240', 'size300'):
                        memcache.delete('cached_image_%s_%s' % (image_key, style))
                        
                    data = {'status': True}
                    
                    json_data = json.dumps(data, ensure_ascii=False)
                    self.response.content_type = 'application/json'
                    self.response.out.write(json_data)

app = webapp2.WSGIApplication(
                              [('/p/(.*)', MainPage),
                               ('/(.*)', MainPage)],
                              debug=False)