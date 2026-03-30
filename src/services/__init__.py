import csv
from contextlib import suppress
from hashlib import sha1

from mongoengine import connect, disconnect
from pymongo.errors import PyMongoError

from commons.constants import MONGODB_URI
from commons.log_helper import get_logger

_LOG = get_logger(__name__)


def connect_to_mongodb() -> None:
    try:
        if MONGODB_URI:
            client = connect(
                host=MONGODB_URI,
                alias="default",
                serverSelectionTimeoutMS=5000,
            )
        else:
            client = connect(
                "tests",
                host="localhost",
                port=27017,
                alias="default",
                serverSelectionTimeoutMS=5000,
            )

        client.admin.command("ping")
        _LOG.info("Connected to MongoDB successfully")
        _seed_houses_table()
        _seed_admins_table()
    except PyMongoError:
        with suppress(Exception):
            disconnect(alias="default")
        _LOG.error("Error connecting to MongoDB")


def _seed_houses_table() -> None:
    from models.houses import Houses

    if Houses.objects.count() == 0:  # ty:ignore[unresolved-attribute]
        _LOG.info("Seeding Houses collection...")
        file_path = "templates/houses_seed_example.csv"
        fieldnames = ["id", "number", "street", "full_address"]
        with open(file_path, encoding="utf-8") as file:
            reader = csv.reader(file)
            next(reader)  # skip header
            for row in reader:
                row_dict = dict(zip(fieldnames, row))
                Houses(
                    id=row_dict["id"],
                    number=int(row_dict["number"]),
                    street=row_dict["street"],
                    full_address=row_dict["full_address"],
                ).save()

        _LOG.info("Houses collection seeded successfully")


def _seed_admins_table() -> None:
    from models.users import Users

    if Users.objects.count() == 0:  # ty:ignore[unresolved-attribute]
        _LOG.info("Seeding Users collection with admin user...")
        file_path = "templates/admins_seed_example.csv"
        fieldnames = [
            "email",
            "first_name",
            "last_name",
            "birthdate",
            "phone_number",
            "password",
        ]
        with open(file_path, encoding="utf-8") as file:
            reader = csv.reader(file)
            next(reader)  # skip header
            for row in reader:
                row_dict = dict(zip(fieldnames, row))
                Users(
                    email=row_dict["email"],
                    first_name=row_dict["first_name"],
                    last_name=row_dict["last_name"],
                    full_name=f"{row_dict['first_name']} {row_dict['last_name']}",
                    birthdate=row_dict["birthdate"],
                    phone_number=row_dict["phone_number"],
                    password_hash=sha1(
                        f"{row_dict['password']}{row_dict['email']}".encode()
                    ).hexdigest(),
                    role="admin",
                ).save()

        _LOG.info("Users collection seeded with admin user successfully")


def disconnect_from_mongodb() -> None:
    disconnect(alias="default")
    _LOG.info("Disconnected from MongoDB successfully")
