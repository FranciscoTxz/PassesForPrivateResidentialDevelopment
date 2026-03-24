import csv
import os
import time
from collections.abc import Generator
from hashlib import sha1

import pytest
from fastapi.testclient import TestClient
from mongoengine import connect, disconnect
from mongoengine.connection import get_db
from pymongo import MongoClient
from testcontainers.core.container import DockerContainer

from models.houses import Houses
from models.passes import Passes
from models.users import Users

TABLES = [Passes]
FIXED_TABLES = [Users, Houses]


# Mock patient constants
USER1_EMAIL = "user_1@hot.com"
USER1_PASSWORD = "TestPass123!"
USER1_NAME = "John"
USER1_SURNAME = "Smith"
USER1_BIRTHDATE = "1995-01-01"
USER1_PHONE = "+1123456789"
USER1_HOUSE_ID = "SV101"

# Mock admin constants
ADMIN_EMAIL = "fake@admin.com"
ADMIN_PASSWORD = "AdminPass123!"
ADMIN_NAME = "Frank"
ADMIN_SURNAME = "Thompson"
ADMIN_BIRTHDATE = "1997-01-01"
ADMIN_PHONE = "+3123456789"
ADMIN_ROLE = "admin"


USERS_FIXTURE_DATA = [
    {
        "email": USER1_EMAIL,
        "password": USER1_PASSWORD,
        "first_name": USER1_NAME,
        "last_name": USER1_SURNAME,
        "birthdate": USER1_BIRTHDATE,
        "phone_number": USER1_PHONE,
        "house_id": USER1_HOUSE_ID,
    },
    {
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD,
        "first_name": ADMIN_NAME,
        "last_name": ADMIN_SURNAME,
        "birthdate": ADMIN_BIRTHDATE,
        "phone_number": ADMIN_PHONE,
        "role": ADMIN_ROLE,
    },
]


@pytest.fixture(scope="session")
def user_info():
    return USERS_FIXTURE_DATA[0]


@pytest.fixture(scope="session")
def admin_info():
    return USERS_FIXTURE_DATA[1]


def wait_until_ready(mongo_uri: str, timeout: float = 15):
    deadline = time.time() + timeout
    while True:
        try:
            client = MongoClient(mongo_uri, serverSelectionTimeoutMS=1000)
            client.admin.command("ping")
            return
        except Exception:
            if time.time() > deadline:
                raise
            time.sleep(0.5)


@pytest.fixture(scope="session")
def mongodb_container() -> Generator[str, None, None]:
    """
    Starts MongoDB in Docker for the test session and returns a connection URI.
    """
    with DockerContainer("mongo:7.0").with_exposed_ports(27017) as container:
        host = container.get_container_host_ip()
        port = container.get_exposed_port(27017)
        mongo_uri = f"mongodb://{host}:{port}/clinic_db"
        wait_until_ready(mongo_uri)
        yield mongo_uri


@pytest.fixture(scope="session")
def mongo_connection(mongodb_container):
    os.environ["MONGODB_URI"] = mongodb_container
    import commons.constants as constants

    constants.MONGODB_URI = mongodb_container
    connect(host=mongodb_container, alias="default")
    yield
    disconnect(alias="default")


@pytest.fixture(scope="session")
def create_fixed_tables(mongo_connection):
    for model in FIXED_TABLES + TABLES:
        model.drop_collection()

    file_path = os.path.join(
        os.path.dirname(__file__), "templates", "houses_seed_test.csv"
    )
    with open(file_path, encoding="utf-8") as file:
        for row in csv.DictReader(file):
            Houses(
                id=row["id"],
                number=int(row["number"]),
                street=row["street"],
                full_address=row["full_address"],
            ).save()

    for user in USERS_FIXTURE_DATA:
        password_hash = sha1(f"{user['password']}{user['email']}".encode()).hexdigest()
        Users(
            email=user["email"],
            first_name=user["first_name"],
            last_name=user["last_name"],
            full_name=f"{user['first_name']} {user['last_name']}",
            birthdate=user["birthdate"],
            phone_number=user["phone_number"],
            password_hash=password_hash,
            role=user.get("role", "user"),
            house_id=user.get("house_id", None),
        ).save()

    yield

    for model in FIXED_TABLES + TABLES:
        model.drop_collection()


@pytest.fixture(scope="function")
def dynamo_client(create_fixed_tables):
    for model in TABLES:
        model.drop_collection()

    yield get_db()

    for model in TABLES:
        model.drop_collection()


@pytest.fixture(scope="function")
def user_client(create_fixed_tables) -> TestClient:
    return _login_client(USER1_EMAIL, USER1_PASSWORD)


@pytest.fixture(scope="function")
def admin_client(create_fixed_tables) -> TestClient:
    return _login_client(ADMIN_EMAIL, ADMIN_PASSWORD)


def _login_client(email: str, password: str) -> TestClient:
    from app import app

    client = TestClient(app)

    login_response = client.post(
        "/auth/sign-in",
        json={
            "email": email,
            "password": password,
        },
    )

    assert login_response.status_code == 200, f"Login failed: {login_response.json()}"
    token = login_response.json().get("access_token")

    client.headers.update({"authorization": token})

    return client
