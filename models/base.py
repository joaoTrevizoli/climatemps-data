__author__ = 'joao'

from mongoengine import DynamicDocument, BooleanField, \
    URLField, DateTimeField, IntField, StringField, Document
from datetime import datetime


class AccessControl(DynamicDocument):
    url = URLField(required=True)
    updated_at = DateTimeField(required=True, default=datetime.utcnow())
    access_success = BooleanField(default=False)
    status_code = IntField(required=True)
    content = StringField(required=True)


class ErrorLog(Document):
    exception = StringField()
    url = URLField(required=True)
    created_at = DateTimeField(required=True, default=datetime.utcnow())
