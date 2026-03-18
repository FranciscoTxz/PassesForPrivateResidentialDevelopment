from datetime import UTC, date, datetime, timedelta
from hashlib import sha1

import jwt
from fastapi import HTTPException
from mongoengine import DoesNotExist

from commons.constants import SECRET_KEY
from models.users import Users
from schemas.users_schema import UserInfo


class UserService:
    @staticmethod
    def signup_user(
        first_name: str,
        last_name: str,
        email: str,
        password: str,
        birthdate: date,
        phone_number: str,
    ):
        try:
            Users.objects.get(email=email)
            raise HTTPException(
                status_code=400, detail="Invalid input or email already exists"
            )
        except DoesNotExist:
            user = Users(
                email=email,
                first_name=first_name,
                last_name=last_name,
                full_name=f"{first_name} {last_name}",
                birthdate=birthdate.isoformat(),
                phone_number=phone_number,
                password_hash=sha1(f"{password}{email}".encode()).hexdigest(),
            )
            user.save()

            return {"result": "User registered successfully."}

    @staticmethod
    def login_user(email: str, password: str):
        try:
            user = Users.objects.get(email=email)
        except DoesNotExist:
            raise HTTPException(status_code=400, detail="Invalid email or password")

        if (
            user.password_hash != sha1(f"{password}{email}".encode()).hexdigest()
        ) or not user.enabled:
            raise HTTPException(status_code=400, detail="Invalid email or password")
        expire = datetime.now(UTC) + timedelta(hours=1)

        token = jwt.encode(
            {
                "email": user.email,
                "full_name": user.full_name,
                "exp": expire,
            },
            SECRET_KEY,
            algorithm="HS256",
        )
        return {
            "access_token": token,
            "user_full_name": f"{user.full_name}",
        }

    @staticmethod
    def get_user_info(email: str) -> UserInfo:
        try:
            user = Users.objects.get(email=email)
            return UserInfo(
                email=user.email,
                full_name=user.full_name,
                house_id=user.house_id,
                enabled=user.enabled,
            )
        except DoesNotExist:
            raise HTTPException(status_code=404, detail="User not found")
