from uuid import uuid4

from mongoengine import BooleanField, DateTimeField, Document, StringField


class Passes(Document):
    id = StringField(primary_key=True, default=lambda: str(uuid4()))
    enabled = BooleanField(default=True)
    used = BooleanField(default=False)
    status = StringField(default="approved")
    pass_type = StringField(required=True, default="temporary")
    guest_name = StringField(required=False)
    valid_from = DateTimeField(required=False)
    valid_until = DateTimeField(required=False)
    house_id = StringField(required=True)
    reason = StringField(required=False)

    meta = {
        "collection": "passes",
        "indexes": ["house_id", "valid_until", "enabled", "used", "status"],
    }
