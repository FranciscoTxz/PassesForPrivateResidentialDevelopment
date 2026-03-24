import asyncio
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException
from mongoengine import DoesNotExist, Q

from commons.log_helper import get_logger
from models.passes import Passes
from services.qr_generator_service import generate_qr_base64

_LOG = get_logger(__name__)


class PassesService:
    @staticmethod
    def create_simple_pass(
        pass_type: str, guest_name: str, valid_from: datetime, house_id: str
    ):
        time = {"temporary": 5, "temporary_party": 6, "temporary_gym": 3}
        valid_until = valid_from + timedelta(hours=time.get(pass_type, 1))
        new_pass = Passes(
            pass_type=pass_type,
            guest_name=guest_name,
            valid_from=valid_from,
            valid_until=valid_until,
            house_id=house_id,
        )
        new_pass.save()
        return {"message": "Pass created successfully", "pass": new_pass.to_mongo()}

    @staticmethod
    def create_pass_for_days(
        days: int, guest_name: str, valid_from: datetime, reason: str, house_id: str
    ):
        valid_until = valid_from + timedelta(days=days)
        new_pass = Passes(
            pass_type="visit",
            enabled=False,
            status="pending",
            guest_name=guest_name,
            valid_from=valid_from,
            valid_until=valid_until,
            reason=reason,
            house_id=house_id,
        )
        new_pass.save()
        return {
            "message": "Pass created successfully, pending approval",
            "pass_id": new_pass.id,
        }

    @staticmethod
    def get_passes_for_user(house_id: str):
        passes = Passes.objects(house_id=house_id)
        passes_mongo = [pass_obj.to_mongo() for pass_obj in passes]
        if not passes_mongo:
            raise HTTPException(status_code=404, detail="No passes found for this user")
        return {"passes": passes_mongo}

    @staticmethod
    def get_pass_qr(pass_id: str, house_id: str):
        try:
            pass_obj = Passes.objects.get(id=pass_id, house_id=house_id)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail="Pass not found")
        if not pass_obj.enabled:
            raise HTTPException(status_code=400, detail="Pass is not enabled")
        qr_code = generate_qr_base64(pass_obj.id)
        return {"qr_jpg_code_base64": qr_code}

    @staticmethod
    def get_all_passes(cursor_id: str | None = None, limit: int = 15):
        query = Q()
        if cursor_id:
            query &= Q(id__gt=cursor_id)
        passes = list(Passes.objects(query).order_by("id").limit(limit + 1))
        if not passes:
            return {
                "passes": [],
                "next_cursor": None,
                "has_next": False,
            }

        has_next = len(passes) > limit
        passes_mongo = [pass_obj.to_mongo() for pass_obj in passes[:limit]]
        return {
            "passes": passes_mongo,
            "next_cursor": passes_mongo[-1]["_id"] if has_next else None,
            "has_next": has_next,
        }

    @staticmethod
    def search_pass_by_id(pass_id: str):
        try:
            pass_obj = Passes.objects.get(id=pass_id)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail="Pass not found")
        return pass_obj.to_mongo()

    @staticmethod
    def count_pending_passes():
        return {"pending_passes": Passes.objects(status="pending").count()}

    @staticmethod
    def get_pending_passes():
        passes = Passes.objects(status="pending")
        if not passes:
            raise HTTPException(status_code=404, detail="No pending passes found")
        return [pass_obj.to_mongo() for pass_obj in passes]

    @staticmethod
    def approve_pass(pass_id: str):
        try:
            pass_obj = Passes.objects.get(id=pass_id)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail="Pass not found")
        if pass_obj.status != "pending":
            raise HTTPException(
                status_code=400, detail="Only pending passes can be approved"
            )
        pass_obj.enabled = True
        pass_obj.status = "approved"
        pass_obj.save()
        return {"message": "Pass approved successfully"}

    @staticmethod
    def reject_pass(pass_id: str):
        try:
            pass_obj = Passes.objects.get(id=pass_id)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail="Pass not found")
        pass_obj.enabled = False
        pass_obj.status = "rejected"
        pass_obj.save()
        return {"message": "Pass rejected successfully"}


async def update_passes_status():
    while True:
        _LOG.info("Checking for expired passes...")
        now = datetime.now(UTC)
        Passes.objects(valid_until__lte=now, enabled=True).update(
            enabled=False, status="expired"
        )
        await asyncio.sleep(3600)
