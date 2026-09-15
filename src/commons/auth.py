import jwt
from fastapi import Header, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from mongoengine import DoesNotExist

from commons.constants import SECRET_KEY
from models.users import Users
from schemas.users_schema import UserInfo
from services.users_service import UserService

bearer_scheme = HTTPBearer(auto_error=False)


def _extract_token(
    authorization: str | None,
    credentials: HTTPAuthorizationCredentials | None,
) -> str | None:
    """Accept both `Authorization: Bearer <token>` and a raw token header."""
    token: str | None = None
    if credentials is not None and getattr(credentials, "credentials", None):
        token = credentials.credentials
    elif isinstance(authorization, str):
        token = authorization

    if not token:
        return None

    token = token.strip()
    if token.lower().startswith("bearer "):
        token = token[7:].strip()
    return token or None


def get_current_user_info(validate_owner: bool = False, validate_admin: bool = False):
    def verify_token(
        authorization: str | None = Header(None),
        credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    ) -> UserInfo:
        try:
            token = _extract_token(authorization, credentials)
            if not token:
                raise HTTPException(
                    status_code=401, detail="Unauthorized: Missing or invalid token"
                )

            attributes = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            email = attributes.get("email", None)
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
    def validate_token(
        authorization: str | None = Header(None),
        credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    ):
        try:
            token = _extract_token(authorization, credentials)
            if not token:
                raise HTTPException(
                    status_code=401, detail="Unauthorized: Missing or invalid token"
                )

            attributes = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
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
