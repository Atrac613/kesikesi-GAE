# -*- coding: utf-8 -*-

import logging
import datetime

import webapp2

from google.appengine.api import taskqueue

from kesikesi_db import ArchiveList
from kesikesi_db import UserList

from i18NRequestHandler import I18NRequestHandler

class DeleteAllPhotosTask(I18NRequestHandler):
    def post(self):
        user_id = self.request.get('id')
        
        user_list = UserList.get_by_id(int(user_id))
        
        archive_list = ArchiveList.all().filter('account =', user_list.key()).filter('delete_flg =', False).fetch(10)
        
        for archive in archive_list:
            archive.delete_flg = True
            archive.updated_at = datetime.datetime.now()
            archive.put()
        
        logging.info('Operation Account: %s' % user_list.google_account.email())
        logging.info('Deleted %d archives.' % len(archive_list))
        
        archive_list = ArchiveList.all().filter('account =', user_list.key()).filter('delete_flg =', False).fetch(10)
        if len(archive_list) > 0:
            taskqueue.add(url='/task/delete_all_photos', params={'id': user_id})
            
app = webapp2.WSGIApplication(
                              [('/task/delete_all_photos', DeleteAllPhotosTask)],
                              debug=False)