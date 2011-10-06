# -*- coding: utf-8 -*-

import os
import hashlib
import logging
import uuid
import datetime

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.api import images
from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.api import taskqueue

from kesikesi_db import ArchiveList
from kesikesi_db import UserList

class DeleteAllPhotosTask(webapp.RequestHandler):
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
            

application = webapp.WSGIApplication(
                                     [('/task/delete_all_photos', DeleteAllPhotosTask)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()