from mongoengine import BooleanField, DateTimeField, Document, StringField

from commons.datetime_utils import utcnow_naive


class Users(Document):
    email = StringField(primary_key=True, required=True)
    first_name = StringField(required=True)
    last_name = StringField(required=True)
    full_name = StringField(required=True)
    birthdate = StringField(required=True)
    phone_number = StringField(required=True)
    password_hash = StringField(required=True)
    enabled = BooleanField(default=True)
    created_at = DateTimeField(default=utcnow_naive)
    updated_at = DateTimeField(default=None)
    house_id = StringField(default=None)
    role = StringField(default="user")

    meta = {
        "collection": "users",
        "indexes": [
            "full_name",
            {"fields": ["house_id"], "unique": True, "sparse": True},
            {"fields": ["$full_name", "$email"]},
        ],
    }
