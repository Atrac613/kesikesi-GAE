# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------
# db entities
# ------------------------------------------------------------------------------

from google.appengine.ext import db

class UserList(db.Model):
    google_account = db.UserProperty()
    device_id = db.StringProperty()
    status = db.StringProperty()
    created_at = db.DateTimeProperty(auto_now_add=True)
    
class ArchiveList(db.Model):
    account = db.ReferenceProperty(UserList)
    image_key = db.StringProperty()
    comment = db.StringProperty()
    delete_flg = db.BooleanProperty()
    created_at = db.DateTimeProperty(auto_now_add=True)
    updated_at = db.DateTimeProperty(auto_now_add=True)

class OriginalImage(db.Model):
    image = db.BlobProperty()
    access_key = db.StringProperty()
    archive_list_key = db.ReferenceProperty(ArchiveList)
    created_at = db.DateTimeProperty(auto_now_add=True)
    updated_at = db.DateTimeProperty(auto_now_add=True)
    
class MaskImage(db.Model):
    mask_mode = db.StringProperty()
    image = db.BlobProperty()
    access_key = db.StringProperty()
    archive_list_key = db.ReferenceProperty(ArchiveList)
    read_count = db.IntegerProperty()
    access_code = db.StringProperty()
    created_at = db.DateTimeProperty(auto_now_add=True)
    updated_at = db.DateTimeProperty(auto_now_add=True)