from fastapi import APIRouter, Depends

from commons.auth import get_current_user_info, validate_gatehouse_token
from schemas.users_schema import UserInfo
from services.gatehouse_service import GatehouseService

router = APIRouter(prefix="/gatehouse", tags=["Gatehouse"])


@router.post("/token", status_code=200)
def get_token(
    user_info: UserInfo = Depends(get_current_user_info(validate_admin=True)),
):
    """Endpoint for gatehouse to get token for authentication."""
    return GatehouseService.create_token_for_gatehouse(admin_email=user_info.email)


@router.get("/validate_pass/{pass_id}", status_code=200)
def validate_pass(
    pass_id: str,
    user_info: UserInfo = Depends(validate_gatehouse_token()),
):
    """Endpoint for gatehouse to validate a pass."""
    return GatehouseService.validate_pass(pass_id=pass_id)
