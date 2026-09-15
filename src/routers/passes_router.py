from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, Query

from commons.auth import get_current_user_info
from schemas.passes_schema import (
    CreatePassesForDays,
    CreatePassesSimple,
    PassCreatedForDaysResponse,
    PassCreatedResponse,
    PassesPageResponse,
    PassesResponseList,
    PassesResponseUser,
    PassQRCodeResponse,
    PendingPassesCountResponse,
    ReviewSchema,
)
from schemas.users_schema import MessageResponse, UserInfo
from services.passes_service import PassesService

AUTH_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    401: {"description": "Missing or invalid authentication token"},
    403: {"description": "Insufficient permissions"},
}

router = APIRouter(prefix="/passes", tags=["Passes"], responses=AUTH_ERROR_RESPONSES)


@router.post(
    "",
    status_code=201,
    response_model=PassCreatedResponse,
    responses={404: {"description": "House user not found"}},
)
def create_simple_pass(
    payload: CreatePassesSimple,
    background_tasks: BackgroundTasks,
    user_info: UserInfo = Depends(get_current_user_info(validate_owner=True)),
):
    return PassesService.create_simple_pass(
        pass_type=payload.pass_type.value,
        guest_name=payload.guest_name,
        valid_from=payload.valid_from,
        house_id=user_info.house_id or "",
        background_tasks=background_tasks,
    )


@router.post("/days", status_code=201, response_model=PassCreatedForDaysResponse)
def create_pass_for_days(
    payload: CreatePassesForDays,
    user_info: UserInfo = Depends(get_current_user_info(validate_owner=True)),
):
    return PassesService.create_pass_for_days(
        days=payload.days,
        guest_name=payload.guest_name,
        valid_from=payload.valid_from,
        reason=payload.reason,
        house_id=user_info.house_id or "",
    )


@router.get("", status_code=200, response_model=PassesResponseList)
def get_passes_for_user(
    user_info: UserInfo = Depends(get_current_user_info(validate_owner=True)),
):
    return PassesService.get_passes_for_user(user_info.house_id or "")


@router.get("/{pass_id}/qr", status_code=200, response_model=PassQRCodeResponse)
def get_pass_qr(
    pass_id: str,
    user_info: UserInfo = Depends(get_current_user_info(validate_owner=True)),
):
    return PassesService.get_pass_qr(pass_id, user_info.house_id or "")


# ADMIN ROUTES
@router.get("/all", status_code=200, response_model=PassesPageResponse)
def get_all_passes(
    next_cursor: str | None = Query(default=None),
    limit: int = Query(default=15, ge=1),
    user_info: UserInfo = Depends(get_current_user_info(validate_admin=True)),
):
    return PassesService.get_all_passes(cursor_id=next_cursor, limit=limit)


@router.get("/search", status_code=200, response_model=dict)
def search_pass_by_id(
    pass_id: str = Query(...),
    user_info: UserInfo = Depends(get_current_user_info(validate_admin=True)),
):
    return PassesService.search_pass_by_id(pass_id)


@router.get(
    "/pending/count", status_code=200, response_model=PendingPassesCountResponse
)
def count_pending_passes(
    user_info: UserInfo = Depends(get_current_user_info(validate_admin=True)),
):
    return PassesService.count_pending_passes()


@router.get("/pending", status_code=200, response_model=list[PassesResponseUser])
def get_pending_passes(
    user_info: UserInfo = Depends(get_current_user_info(validate_admin=True)),
):
    return PassesService.get_pending_passes()


@router.patch("/{pass_id}/approve", status_code=200, response_model=MessageResponse)
def approve_pass(
    pass_id: str,
    background_tasks: BackgroundTasks,
    user_info: UserInfo = Depends(get_current_user_info(validate_admin=True)),
):
    return PassesService.approve_pass(pass_id, background_tasks=background_tasks)


@router.post(
    "/{pass_id}/reject",
    status_code=200,
    response_model=MessageResponse,
    summary="Reject a pending pass",
)
def reject_pass(
    pass_id: str,
    background_tasks: BackgroundTasks,
    reason: str = Query(...),
    user_info: UserInfo = Depends(get_current_user_info(validate_admin=True)),
):
    return PassesService.reject_pass(pass_id, reason, background_tasks=background_tasks)


@router.delete(
    "/{pass_id}/reject",
    status_code=200,
    response_model=MessageResponse,
    deprecated=True,
    summary="Reject a pending pass (deprecated, use POST)",
)
def reject_pass_deprecated(
    pass_id: str,
    background_tasks: BackgroundTasks,
    reason: str = Query(...),
    user_info: UserInfo = Depends(get_current_user_info(validate_admin=True)),
):
    return PassesService.reject_pass(pass_id, reason, background_tasks=background_tasks)


@router.patch("/{pass_id}/auto-review", status_code=200, response_model=ReviewSchema)
def auto_review_pass(
    pass_id: str,
    background_tasks: BackgroundTasks,
    user_info: UserInfo = Depends(get_current_user_info(validate_admin=True)),
):
    return PassesService.review_pass_automatically(
        pass_id, background_tasks=background_tasks
    )
