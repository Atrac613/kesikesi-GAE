# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------
# db entities
# ------------------------------------------------------------------------------

from google.appengine.ext import db

class ArchiveList(db.Model):
    user_id = db.StringProperty()
    image_key = db.StringProperty()
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
    created_at = db.DateTimeProperty(auto_now_add=True)
    updated_at = db.DateTimeProperty(auto_now_add=True)