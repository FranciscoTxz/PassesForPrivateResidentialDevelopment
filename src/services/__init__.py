import csv
from contextlib import suppress

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
    except PyMongoError:
        with suppress(Exception):
            disconnect(alias="default")
        _LOG.error("Error connecting to MongoDB")


def _seed_houses_table() -> None:
    from models.houses import Houses

    if Houses.objects.count() == 0:  # ty:ignore[unresolved-attribute]
        _LOG.info("Seeding Houses collection...")
        file_path = "templates/houses_seed.csv"
        with open(file_path, encoding="utf-8") as file:
            for row in csv.DictReader(file):
                Houses(
                    id=row["id"],
                    number=int(row["number"]),
                    street=row["street"],
                    full_address=row["full_address"],
                ).save()

        _LOG.info("Houses collection seeded successfully")


def disconnect_from_mongodb() -> None:
    disconnect(alias="default")
    _LOG.info("Disconnected from MongoDB successfully")
