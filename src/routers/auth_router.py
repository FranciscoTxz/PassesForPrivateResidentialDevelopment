from fastapi import APIRouter

from schemas.users_schema import LogInUser, SignUpUser
from services.users_service import UserService

router = APIRouter(prefix="/auth")


@router.post("/sign-up", status_code=201)
def sign_up_user(payload: SignUpUser):
    result = UserService.signup_user(**payload.model_dump())
    return result


@router.post("/sign-in", status_code=200)
def sign_in_user(payload: LogInUser):
    result = UserService.login_user(email=payload.email, password=payload.password)
    return result
