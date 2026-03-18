from mongoengine import Document, IntField, StringField


class Houses(Document):
    id = StringField(primary_key=True)
    number = IntField(required=True)
    street = StringField(required=True)
    full_address = StringField(required=True)

    meta = {"collection": "houses", "indexes": ["number", "street", "full_address"]}
