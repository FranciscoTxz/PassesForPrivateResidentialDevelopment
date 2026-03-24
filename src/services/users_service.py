import re
from datetime import UTC, date, datetime, timedelta
from hashlib import sha1

import jwt
from fastapi import HTTPException
from mongoengine import DoesNotExist, Q

from commons.constants import SECRET_KEY
from models.houses import Houses
from models.users import Users
from schemas.users_schema import UserInfo

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$")
USER_NOT_FOUND = "User profile not found."


class UserService:
    @staticmethod
    def _serialize_user_info(user: Users) -> dict:
        return UserInfo(
            email=user.email,
            full_name=user.full_name,
            enabled=user.enabled,
            house_id=user.house_id,
            role=user.role,
        ).model_dump(mode="json")

    @staticmethod
    def _process_users_batch(user_id: str, operation_name: str, operation_func):
        """
        Helper method to process a batch of users with consistent error handling.

        Args:
            user_id: User ID (email) to process
            operation_name: Name of the operation (e.g., 'disabled', 'enabled', 'deleted')
            operation_func: Function to call for the user
        """

        try:
            operation_func(user_id)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")

        return {"message": f"User {user_id} has been {operation_name}."}

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

            return {"message": "User registered successfully."}

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
                role=user.role,
            )
        except DoesNotExist:
            raise HTTPException(status_code=404, detail="User not found")

    @staticmethod
    def get_user_info_admin(email: str) -> dict:
        try:
            user = Users.objects.get(email=email)
            return user.to_mongo()
        except DoesNotExist:
            raise HTTPException(status_code=404, detail="User not found")

    @staticmethod
    def update_profile_info(
        email: str,
        new_first_name: str | None,
        new_last_name: str | None,
        new_phone_number: str | None,
    ):
        try:
            user = Users.objects.get(email=email)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail=USER_NOT_FOUND)

        user.first_name = new_first_name or user.first_name
        user.last_name = new_last_name or user.last_name
        user.full_name = f"{user.first_name} {user.last_name}"
        user.phone_number = new_phone_number or user.phone_number
        user.updated_at = datetime.now()
        user.save()
        user.reload()
        return {
            "message": "Profile updated successfully.",
            "full_name": user.full_name,
            "phone_number": user.phone_number,
        }

    @staticmethod
    def update_password(email: str, old_password: str, new_password: str):
        try:
            user = Users.objects.get(email=email)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail=USER_NOT_FOUND)
        if user.password_hash != sha1(f"{old_password}{email}".encode()).hexdigest():
            raise HTTPException(status_code=403, detail="Old password is incorrect.")
        user.password_hash = sha1(f"{new_password}{email}".encode()).hexdigest()
        user.save()

    @staticmethod
    def count_users_by_role(role: str | None = None, query: str | None = None) -> int:
        if query:
            if role:
                return Users.objects(
                    Q(role=role)
                    & (Q(full_name__icontains=query) | Q(email__icontains=query))
                ).count()
            return Users.objects(
                Q(full_name__icontains=query) | Q(email__icontains=query)
            ).count()
        else:
            return Users.objects().count()

    @staticmethod
    def get_all_staff(page: int = 1, page_size: int = 10) -> dict:
        users = []
        skip = (page - 1) * page_size
        staff_query = Users.objects().order_by("-created_at")
        staff_page = staff_query.skip(skip).limit(page_size + 1)

        for user in staff_page:
            users.append(UserService._serialize_user_info(user))
        if not users:
            raise HTTPException(
                status_code=404,
                detail="No users found",
            )

        has_next = len(users) > page_size

        return {
            "users": users[:page_size],
            "has_next": has_next,
            "next_page": page + 1 if has_next else None,
        }

    @staticmethod
    def get_user_info_by_email_name(
        query: str, page: int = 1, page_size: int = 10
    ) -> dict:
        """
        Search for users by email or name using full-text search.

        Supports:
        - Exact email matching
        - Full-text search on names (case-insensitive, whole words)
        - Partial name matching with regex (case-insensitive)
        - Results sorted by relevance

        Args:
            query: Search string (email or name)

        Returns:
            List of user information dictionaries
        """

        def is_valid_email(email: str) -> bool:
            return bool(re.match(EMAIL_RE, email))

        if is_valid_email(query):
            user_data = UserService.get_user_info_admin(query)
            return {
                "users": [user_data] if user_data else [],
                "has_next": False,
                "next_page": None,
            }

        skip = (page - 1) * page_size

        users_list = []

        try:
            users = Users.objects.search_text(query).order_by("$text_score")

            users = users.skip(skip).limit(page_size + 1)
            users_list = [UserService._serialize_user_info(user) for user in users]
        except Exception:
            pass

        if not users_list:
            users = Users.objects(full_name__icontains=query)

            users = users.skip(skip).limit(page_size + 1)
            users_list = [UserService._serialize_user_info(user) for user in users]

        if not users_list:
            raise HTTPException(
                status_code=404,
                detail="Users not found",
            )

        has_next = len(users_list) > page_size

        return {
            "users": users_list[:page_size],
            "has_next": has_next,
            "next_page": page + 1 if has_next else None,
        }

    @staticmethod
    def make_user_admin(email: str):
        try:
            user = Users.objects.get(email=email)
        except DoesNotExist:
            raise HTTPException(
                status_code=404, detail=f"User with email {email} not found"
            )
        user.role = "admin"
        user.save()
        return {"message": f"User {email} has been promoted to admin."}

    @staticmethod
    def disable_user(user_id: str):
        def _disable(email: str):
            user = Users.objects.get(email=email)
            user.enabled = False
            user.save()

        return UserService._process_users_batch(user_id, "disabled", _disable)

    @staticmethod
    def enable_user(user_id: str):
        def _enable(email: str):
            user = Users.objects.get(email=email)
            user.enabled = True
            user.save()

        return UserService._process_users_batch(user_id, "enabled", _enable)

    @staticmethod
    def delete_user(user_id: str):
        def _delete(email: str):
            user = Users.objects.get(email=email)
            user.delete()

        return UserService._process_users_batch(user_id, "deleted", _delete)

    @staticmethod
    def link_house(email: str, house_id: str):
        existing_user = Users.objects(house_id=house_id).first()
        if existing_user and existing_user.email != email:
            raise HTTPException(
                status_code=400,
                detail=f"House with id {house_id} is already linked to another user",
            )
        if existing_user and existing_user.email == email:
            raise HTTPException(
                status_code=400,
                detail=f"User {email} is already linked to house {house_id}",
            )
        try:
            user = Users.objects.get(email=email)
        except DoesNotExist:
            raise HTTPException(
                status_code=404, detail=f"User with email {email} not found"
            )
        try:
            house = Houses.objects.get(id=house_id)
        except DoesNotExist:
            raise HTTPException(
                status_code=404, detail=f"House with id {house_id} not found"
            )
        user.house_id = house.id
        user.save()
        return {"message": f"User {email} has been linked to house {house_id}."}
