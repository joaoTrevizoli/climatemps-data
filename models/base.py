from mongoengine import DynamicDocument, BooleanField, \
    URLField, DateTimeField, IntField, StringField, Document
from datetime import datetime

__author__ = 'João Trevizoli Esteves'


class AccessControl(DynamicDocument):
    url = URLField(required=True)
    updated_at = DateTimeField(required=True, default=datetime.utcnow())
    access_success = BooleanField(default=False)
    status_code = IntField(required=True)
    content = StringField(required=True)

    meta = {'allow_inheritance': True}


class ErrorLog(Document):
    exception = StringField()
    url = URLField(required=True)
    file_name = StringField(required=True)
    line_number = IntField(required=True)
    created_at = DateTimeField(required=True, default=datetime.utcnow())


class Country(Document):
    country = StringField(required=True, unique=True)
    url = URLField(required=True, unique=True)
    updated_at = DateTimeField(required=True, default=datetime.utcnow())
    content = StringField


class Normals(DynamicDocument):
    url = URLField(required=True)
    updated_at = DateTimeField(required=True, default=datetime.utcnow())
    access_success = BooleanField(default=False)
    status_code = IntField(required=True)
    content = StringField(required=True)