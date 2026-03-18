from datetime import datetime

from mongoengine import BooleanField, DateTimeField, Document, StringField


class Users(Document):
    email = StringField(primary_key=True, required=True)
    first_name = StringField(required=True)
    last_name = StringField(required=True)
    full_name = StringField(required=True)
    birthdate = StringField(required=True)
    phone_number = StringField(required=True)
    password_hash = StringField(required=True)
    enabled = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=None)
    house_id = StringField(default=None)

    meta = {"collection": "users", "indexes": ["full_name", "phone_number"]}
