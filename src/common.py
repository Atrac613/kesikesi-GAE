# -*- coding: utf-8 -*-

import logging

from google.appengine.api import images
from google.appengine.api import memcache

from kesikesi_db import UserList

def convert_square(image_src, width, height):
    image = images.Image(image_src)
            
    org_width = float(image.width)
    org_height = float(image.height)

    scale_w = width / org_width
    scale_h = height / org_height
    scale = scale_h if scale_w < scale_h else scale_w

    thumb_width = int(org_width * scale)
    thumb_height = int(org_height * scale)
    image.resize(thumb_width, thumb_height)

    x = (thumb_width - width) / 2.0
    y = (thumb_height - height) / 2.0
    image.crop(x/thumb_width, y/thumb_height, 1.0-(x/thumb_width), 1.0-(y/thumb_height))
            
    return image.execute_transforms(output_encoding=images.PNG)

def get_related_ids(user_id):
    user_list = UserList.all().filter('user_id', user_id).get()
    
    user_id_list = memcache.get('user_id_list_%s' % user_id)
    if user_id_list is None:
        user_id_list = []
        if user_list is not None:
            related_user_list = UserList.all().filter('google_account =', user_list.google_account).fetch(10)
            
            for row in related_user_list:
                user_id_list.append(row.user_id)
                
        if len(user_id_list) <= 0:
            user_id_list.append(user_id)
        
        memcache.add('user_id_list_%s' % user_id, user_id_list, 3600)
        
        logging.info('Load from datastore.')
    else:
        logging.info('Load from memcache.')
                
    return user_id_list
            
        