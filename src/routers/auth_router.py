from fastapi import APIRouter, Depends

from commons.constants import (
    RATE_LIMIT_ENABLED,
    RATE_LIMIT_REQUESTS,
    RATE_LIMIT_WINDOW_SECONDS,
)
from commons.rate_limit import InMemoryRateLimiter
from schemas.users_schema import (
    LoginResponse,
    LogInUser,
    SignUpResponse,
    SignUpUser,
)
from services.users_service import UserService

router = APIRouter(prefix="/auth", tags=["Auth"])

auth_rate_limiter = InMemoryRateLimiter(
    max_requests=RATE_LIMIT_REQUESTS,
    window_seconds=RATE_LIMIT_WINDOW_SECONDS,
    enabled=RATE_LIMIT_ENABLED,
)


@router.post(
    "/sign-up",
    status_code=201,
    response_model=SignUpResponse,
    dependencies=[Depends(auth_rate_limiter)],
)
def sign_up_user(payload: SignUpUser):
    result = UserService.signup_user(**payload.model_dump())
    return result


@router.post(
    "/sign-in",
    status_code=200,
    response_model=LoginResponse,
    dependencies=[Depends(auth_rate_limiter)],
)
def sign_in_user(payload: LogInUser):
    result = UserService.login_user(email=payload.email, password=payload.password)
    return result
