from fastapi import APIRouter, Depends

from commons.auth import get_current_user_info
from schemas.users_schema import UserInfo

router = APIRouter(prefix="/users")


@router.get("/me")
def get_current_user(
    user_info: UserInfo = Depends(get_current_user_info()),
):
    return {"Hi": user_info.full_name}
