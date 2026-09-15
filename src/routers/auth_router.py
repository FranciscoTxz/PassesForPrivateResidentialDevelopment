from fastapi import APIRouter

from schemas.users_schema import (
    LoginResponse,
    LogInUser,
    SignUpResponse,
    SignUpUser,
)
from services.users_service import UserService

router = APIRouter(prefix="/auth")


@router.post("/sign-up", status_code=201, response_model=SignUpResponse)
def sign_up_user(payload: SignUpUser):
    result = UserService.signup_user(**payload.model_dump())
    return result


@router.post("/sign-in", status_code=200, response_model=LoginResponse)
def sign_in_user(payload: LogInUser):
    result = UserService.login_user(email=payload.email, password=payload.password)
    return result
