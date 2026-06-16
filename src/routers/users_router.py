from fastapi import APIRouter, Depends, Query

from commons.auth import get_current_user_info
from schemas.users_schema import UserInfo
from services.users_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", status_code=200)
def get_users(
    query: str | None = Query(default=None),
    user_info: UserInfo = Depends(get_current_user_info(validate_admin=True)),
    page: int = Query(default=1, gt=0),
    page_size: int = Query(default=10, gt=0, le=100),
):
    if not query:
        return UserService.get_all_staff(page=page, page_size=page_size)

    return UserService.get_user_info_by_email_name(
        query, page=page, page_size=page_size
    )


@router.get("/house", status_code=200)
def get_user_by_house_id(
    house_id: str = Query(),
    user_info: UserInfo = Depends(get_current_user_info(validate_admin=True)),
):
    return UserService.get_user_by_house_id(house_id)


@router.get("/pages", status_code=200)
def get_users_pages(
    query: str | None = Query(default=None),
    user_info: UserInfo = Depends(get_current_user_info(validate_admin=True)),
    page_size: int = Query(default=10, gt=0, le=100),
):
    if query:
        total_staff = UserService.count_users_by_role(query=query)
    else:
        total_staff = UserService.count_users_by_role()
    total_pages = (total_staff + page_size - 1) // page_size
    return {"total_pages": total_pages, "total_users": total_staff}


@router.patch("", status_code=200)
def make_user_admin(
    email: str = Query(...),
    user_info: UserInfo = Depends(get_current_user_info(validate_admin=True)),
):
    return UserService.make_user_admin(email)


@router.patch("/disable", status_code=200)
def disable_staff(
    email: str = Query(...),
    user_info: UserInfo = Depends(get_current_user_info(validate_admin=True)),
):
    return UserService.disable_user(user_id=email)


@router.patch("/enable", status_code=200)
def enable_staff(
    email: str = Query(...),
    user_info: UserInfo = Depends(get_current_user_info(validate_admin=True)),
):
    return UserService.enable_user(user_id=email)


@router.delete("/delete", status_code=204)
def delete_staff(
    email: str = Query(...),
    user_info: UserInfo = Depends(get_current_user_info(validate_admin=True)),
):
    UserService.delete_user(user_id=email)


@router.patch("/link", status_code=200)
def link_house(
    email: str = Query(...),
    house_id: str = Query(...),
    user_info: UserInfo = Depends(get_current_user_info(validate_admin=True)),
):
    return UserService.link_house(email=email, house_id=house_id)
