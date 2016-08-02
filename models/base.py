from mongoengine import DynamicDocument, BooleanField, \
    URLField, DateTimeField, IntField, StringField, Document, PointField
from datetime import datetime

__author__ = 'João Trevizoli Esteves'


class AccessControl(DynamicDocument):
    url = URLField(required=True)
    url_type = StringField(choices=("country", "normal"))
    updated_at = DateTimeField(required=True, default=datetime.utcnow())
    access_success = BooleanField(default=False)
    status_code = IntField(required=False)
    content = StringField(required=True)

    meta = {'allow_inheritance': True}


class ErrorLog(Document):
    exception = StringField()
    url = URLField(required=True)
    file_name = StringField(required=True)
    line_number = IntField(required=True)
    created_at = DateTimeField(required=True, default=datetime.utcnow())


class Normals(DynamicDocument):
    city = StringField(required=True)
    country = StringField(required=True)
    point = PointField(required=True)
    url = URLField(required=True)
    updated_at = DateTimeField(required=True, default=datetime.utcnow())
    access_success = BooleanField(default=False)
    status_code = IntField(required=False)
