"""Populate the database with fake users, houses and passes for local testing.

Usage:
    uv run python scripts/seed_fake_data.py

The script is idempotent: existing users/houses are reused, new users are
assigned to free houses only, and passes are only created for houses that do
not have any yet. It reads MONGODB_URI from .env and rewrites the Docker
internal `mongodb` host to `localhost` so it can run from the host machine
(set SEED_MONGO_HOST to override).
"""

import os
import re
import sys
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=ROOT / ".env", override=True)
sys.path.insert(0, str(ROOT / "src"))

from commons.datetime_utils import utcnow_naive  # noqa: E402
from commons.security import hash_password  # noqa: E402
from models.houses import Houses  # noqa: E402
from models.passes import Passes  # noqa: E402
from models.users import Users  # noqa: E402

PASSWORD = "Password123!"
SIMPLE_HOURS = {"temporary": 5, "temporary_party": 6, "temporary_gym": 3}

NEW_HOUSES = [
    {
        "id": "SV106",
        "number": 106,
        "street": "Av. Siempre Viva",
        "full_address": "Av. Siempre Viva 106, Fracc. El Paraíso, Guadalajara, Jalisco",
    },
    {
        "id": "CB204",
        "number": 204,
        "street": "Calle Bugambilias",
        "full_address": "Calle Bugambilias 204, Fracc. El Paraíso, Guadalajara, Jalisco",
    },
    {
        "id": "CJ305",
        "number": 305,
        "street": "Calle Jacarandas",
        "full_address": "Calle Jacarandas 305, Fracc. El Paraíso, Guadalajara, Jalisco",
    },
]

# Each user has an ordered list of passes to create once assigned to a house.
USERS = [
    {
        "email": "ana.lopez@example.com",
        "first": "Ana",
        "last": "López",
        "birthdate": "1992-04-12",
        "phone": "+523312345601",
        "plan": [
            {
                "kind": "simple",
                "pass_type": "temporary",
                "guest_name": "Luis Ramírez",
                "start_minutes": 30,
            },
            {
                "kind": "simple",
                "pass_type": "temporary_party",
                "guest_name": "Fiesta de cumpleaños - familia Gómez",
                "start_minutes": 240,
            },
        ],
    },
    {
        "email": "carlos.mendoza@example.com",
        "first": "Carlos",
        "last": "Mendoza",
        "birthdate": "1988-11-03",
        "phone": "+523312345602",
        "plan": [
            {
                "kind": "simple",
                "pass_type": "temporary",
                "guest_name": "Técnico de internet Telmex",
                "start_minutes": 60,
            },
        ],
    },
    {
        "email": "maria.ruiz@example.com",
        "first": "María",
        "last": "Ruiz",
        "birthdate": "1995-07-21",
        "phone": "+523312345603",
        "plan": [
            {
                "kind": "simple",
                "pass_type": "temporary_gym",
                "guest_name": "Entrenador personal - Andrés",
                "start_minutes": 90,
            },
            {
                "kind": "days_pending",
                "guest_name": "Cuadrilla de albañiles",
                "days": 4,
                "reason": "Remodelación del jardín y cambio de piso en la cochera",
                "start_minutes": 1440,
            },
        ],
    },
    {
        "email": "jorge.castillo@example.com",
        "first": "Jorge",
        "last": "Castillo",
        "birthdate": "1983-02-17",
        "phone": "+523312345604",
        "plan": [
            {
                "kind": "simple",
                "pass_type": "temporary",
                "guest_name": "Repartidor de muebles",
                "start_minutes": 45,
            },
        ],
    },
    {
        "email": "laura.jimenez@example.com",
        "first": "Laura",
        "last": "Jiménez",
        "birthdate": "1999-09-30",
        "phone": "+523312345605",
        "plan": [
            {
                "kind": "days_pending",
                "guest_name": "Primos de Monterrey",
                "days": 3,
                "reason": "Visita familiar de fin de semana largo con estancia de tres días",
                "start_minutes": 2880,
            },
        ],
    },
    {
        "email": "roberto.sanchez@example.com",
        "first": "Roberto",
        "last": "Sánchez",
        "birthdate": "1990-06-08",
        "phone": "+523312345606",
        "plan": [
            {
                "kind": "simple",
                "pass_type": "temporary",
                "guest_name": "Plomero - servicio urgente",
                "start_minutes": 20,
            },
            {"kind": "expired", "guest_name": "Visita de ayer"},
        ],
    },
    {
        "email": "paola.torres@example.com",
        "first": "Paola",
        "last": "Torres",
        "birthdate": "1994-12-25",
        "phone": "+523312345607",
        "plan": [
            {
                "kind": "simple",
                "pass_type": "temporary_party",
                "guest_name": "Posada navideña - amigos",
                "start_minutes": 300,
            },
        ],
    },
    {
        "email": "diego.herrera@example.com",
        "first": "Diego",
        "last": "Herrera",
        "birthdate": "1986-03-14",
        "phone": "+523312345608",
        "plan": [
            {
                "kind": "days_approved",
                "guest_name": "Ingeniero de obra",
                "days": 5,
                "reason": "Supervisión de construcción de la cisterna durante cinco días",
                "start_minutes": 4320,
            },
        ],
    },
    {
        "email": "sofia.navarro@example.com",
        "first": "Sofía",
        "last": "Navarro",
        "birthdate": "1997-08-19",
        "phone": "+523312345609",
        "plan": [
            {
                "kind": "days_pending",
                "guest_name": "Proveedor de jardinería",
                "days": 2,
                "reason": "Poda de árboles y mantenimiento completo del jardín trasero",
                "start_minutes": 720,
            },
        ],
    },
    {
        "email": "miguel.vargas@example.com",
        "first": "Miguel",
        "last": "Vargas",
        "birthdate": "1981-01-27",
        "phone": "+523312345610",
        "plan": [
            {
                "kind": "simple",
                "pass_type": "temporary_gym",
                "guest_name": "Clase de yoga - instructor",
                "start_minutes": 120,
            },
        ],
    },
    {
        "email": "elena.morales@example.com",
        "first": "Elena",
        "last": "Morales",
        "birthdate": "1993-05-05",
        "phone": "+523312345611",
        "plan": [
            {
                "kind": "days_approved",
                "guest_name": "Tíos de visita",
                "days": 3,
                "reason": "Visita familiar de tres días por vacaciones de verano",
                "start_minutes": 3600,
            },
        ],
    },
    {
        "email": "fernando.rios@example.com",
        "first": "Fernando",
        "last": "Ríos",
        "birthdate": "1989-10-11",
        "phone": "+523312345612",
        "plan": [
            {
                "kind": "simple",
                "pass_type": "temporary",
                "guest_name": "Domiciliario de paquetería",
                "start_minutes": 15,
            },
        ],
    },
    {
        "email": "gabriela.pena@example.com",
        "first": "Gabriela",
        "last": "Peña",
        "birthdate": "1996-02-23",
        "phone": "+523312345613",
        "plan": [
            {
                "kind": "days_pending",
                "guest_name": "Fumigación de la casa",
                "days": 2,
                "reason": "Tratamiento contra termitas que requiere acceso en dos visitas",
                "start_minutes": 1080,
            },
        ],
    },
]


def resolve_mongo_uri() -> str:
    uri = os.getenv("MONGODB_URI")
    if not uri:
        raise SystemExit("MONGODB_URI is not set. Add it to your .env file.")

    override = os.getenv("SEED_MONGO_HOST")
    if override:
        return re.sub(r"@[^/:]+:", f"@{override}:", uri, count=1)
    return uri.replace("@mongodb:", "@localhost:").replace("//mongodb:", "//localhost:")


def ensure_houses() -> int:
    created = 0
    for house in NEW_HOUSES:
        if Houses.objects(id=house["id"]).first() is None:
            Houses(**house).save()
            created += 1
    return created


def free_house_ids() -> list[str]:
    taken = {u.house_id for u in Users.objects() if u.house_id}
    return [h.id for h in Houses.objects().order_by("id") if h.id not in taken]


def ensure_users() -> tuple[int, list[tuple[Users, list[dict]]]]:
    available = free_house_ids()
    created = 0
    seeded: list[tuple[Users, list[dict]]] = []

    for entry in USERS:
        user = Users.objects(email=entry["email"]).first()
        if user is None:
            if not available:
                print(f"  ! No free houses left, skipping {entry['email']}")
                continue
            house_id = available.pop(0)
            user = Users(
                email=entry["email"],
                first_name=entry["first"],
                last_name=entry["last"],
                full_name=f"{entry['first']} {entry['last']}",
                birthdate=entry["birthdate"],
                phone_number=entry["phone"],
                password_hash=hash_password(PASSWORD, entry["email"]),
                house_id=house_id,
                role="user",
            )
            user.save()
            created += 1
        seeded.append((user, entry["plan"]))
    return created, seeded


def create_passes_for(house_id: str, specs: list[dict]) -> int:
    if Passes.objects(house_id=house_id).first() is not None:
        return 0

    now = utcnow_naive()
    created = 0
    for spec in specs:
        valid_from = now + timedelta(minutes=spec.get("start_minutes", 0))
        if spec["kind"] == "simple":
            Passes(
                pass_type=spec["pass_type"],
                guest_name=spec["guest_name"],
                valid_from=valid_from,
                valid_until=valid_from
                + timedelta(hours=SIMPLE_HOURS[spec["pass_type"]]),
                house_id=house_id,
                enabled=True,
                status="approved",
            ).save()
        elif spec["kind"] == "days_pending":
            Passes(
                pass_type="visit for days",
                guest_name=spec["guest_name"],
                valid_from=valid_from,
                valid_until=valid_from + timedelta(days=spec["days"]),
                house_id=house_id,
                reason=spec["reason"],
                enabled=False,
                status="pending",
            ).save()
        elif spec["kind"] == "days_approved":
            Passes(
                pass_type="visit for days",
                guest_name=spec["guest_name"],
                valid_from=valid_from,
                valid_until=valid_from + timedelta(days=spec["days"]),
                house_id=house_id,
                reason=spec["reason"],
                enabled=True,
                status="approved",
            ).save()
        elif spec["kind"] == "expired":
            Passes(
                pass_type="temporary",
                guest_name=spec["guest_name"],
                valid_from=now - timedelta(days=2),
                valid_until=now - timedelta(days=2) + timedelta(hours=5),
                house_id=house_id,
                enabled=False,
                status="expired",
            ).save()
        created += 1
    return created


def main() -> None:
    from mongoengine import connect

    uri = resolve_mongo_uri()
    connect(host=uri, alias="default")

    print(f"Connected to {uri.split('@')[-1]}")
    print(
        f"Before -> houses: {Houses.objects.count()}, "
        f"users: {Users.objects.count()}, passes: {Passes.objects.count()}"
    )

    houses_created = ensure_houses()
    users_created, seeded_users = ensure_users()

    passes_created = 0
    for user, plan in seeded_users:
        passes_created += create_passes_for(user.house_id, plan)

    print(
        f"Created -> houses: {houses_created}, "
        f"users: {users_created}, passes: {passes_created}"
    )
    print(
        f"After  -> houses: {Houses.objects.count()}, "
        f"users: {Users.objects.count()}, passes: {Passes.objects.count()}"
    )
    print(f"All seeded users share the password: {PASSWORD}")


if __name__ == "__main__":
    main()
