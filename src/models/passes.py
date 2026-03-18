from uuid import uuid4

from mongoengine import DateTimeField, Document, StringField


class Passes(Document):
    id = StringField(primary_key=True, default=lambda: str(uuid4()))
    pass_type = StringField(required=True, default="temporary")
    guest_name = StringField(required=False)
    valid_until = DateTimeField(required=False)
    house_id = StringField(required=True)

    meta = {"collection": "passes", "indexes": ["house_id"]}
