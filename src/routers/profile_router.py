from fastapi import APIRouter, Depends

from commons.auth import get_current_user_info
from schemas.users_schema import UserInfo, UserNamePhone, UserPasswordUpdate
from services.users_service import UserService

router = APIRouter(prefix="/profile", tags=["Profile"])


@router.get("", status_code=200)
def get_current_user(
    user_info: UserInfo = Depends(get_current_user_info()),
):
    return {
        "Hi": user_info.full_name,
        "email": user_info.email,
        "role": user_info.role,
        "house_id": user_info.house_id,
    }


@router.patch("", status_code=200)
async def update_profile_info(
    payload: UserNamePhone,
    user_info: UserInfo = Depends(get_current_user_info()),
):
    result = UserService.update_profile_info(
        email=user_info.email,
        new_first_name=payload.first_name,
        new_last_name=payload.last_name,
        new_phone_number=payload.phone_number,
    )
    return result


@router.put("/password", status_code=200)
async def update_profile_password(
    payload: UserPasswordUpdate,
    user_info: UserInfo = Depends(get_current_user_info()),
):
    UserService.update_password(
        email=user_info.email,
        old_password=payload.old_password,
        new_password=payload.new_password,
    )
    return {"message": "Password changed successfully."}
