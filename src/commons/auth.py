import jwt
from fastapi import Header, HTTPException
from mongoengine import DoesNotExist

from commons.constants import SECRET_KEY
from models.users import Users
from schemas.users_schema import UserInfo
from services.users_service import UserService


def get_current_user_info(validate_owner: bool = False, validate_admin: bool = False):
    def verify_token(authorization: str = Header(None)) -> UserInfo:
        try:
            attributes = jwt.decode(authorization, SECRET_KEY, algorithms=["HS256"])
            email = attributes.get("email")

            if not email:
                raise HTTPException(
                    status_code=401, detail="Unauthorized: Missing or invalid token"
                )

            user_info = UserService.get_user_info(email)

            if not user_info.enabled:
                raise HTTPException(
                    status_code=403, detail="Forbidden: User account is disabled"
                )

            if validate_owner and user_info.house_id is None:
                raise HTTPException(
                    status_code=403,
                    detail="Forbidden: User does not have a house assigned",
                )

            if validate_admin and user_info.role != "admin":
                raise HTTPException(
                    status_code=403,
                    detail="Forbidden: User does not have the required role",
                )

            return user_info

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=401, detail="Unauthorized: Token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Unauthorized: Invalid token")
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=401, detail="Unauthorized: Missing or invalid token"
            )

    return verify_token


def validate_gatehouse_token():
    def validate_token(authorization: str = Header(None)):
        try:
            attributes = jwt.decode(authorization, SECRET_KEY, algorithms=["HS256"])
            if attributes.get("role") != "gatehouse":
                raise HTTPException(
                    status_code=403,
                    detail="Forbidden: User does not have the required role",
                )
            Users.objects.get(email=attributes.get("admin_email"))
        except DoesNotExist:
            raise HTTPException(status_code=404, detail="Admin user not found")
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=401, detail="Unauthorized: Token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Unauthorized: Invalid token")
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=401, detail="Unauthorized: Missing or invalid token"
            )

    return validate_token
