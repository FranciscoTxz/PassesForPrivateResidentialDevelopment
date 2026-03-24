from datetime import UTC, datetime, timedelta

import jwt
from fastapi import HTTPException
from mongoengine import DoesNotExist

from commons.constants import SECRET_KEY
from models.houses import Houses
from models.passes import Passes


class GatehouseService:
    @staticmethod
    def create_token_for_gatehouse(admin_email: str):
        expire = datetime.now(UTC) + timedelta(days=30)
        payload = {
            "admin_email": admin_email,
            "role": "gatehouse",
            "exp": expire,
        }
        return {
            "gatehouse_token": jwt.encode(payload, SECRET_KEY, algorithm="HS256"),
            "expires_in": expire.isoformat(),
        }

    @staticmethod
    def validate_pass(pass_id: str):
        try:
            pass_obj = Passes.objects.get(id=pass_id)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail="Pass not found")
        try:
            Houses.objects.get(id=pass_obj.house_id)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail="House not found")
        if not pass_obj.enabled:
            raise HTTPException(status_code=400, detail="Pass is not enabled")
        now = datetime.now(UTC).replace(tzinfo=None)
        if pass_obj.valid_from and pass_obj.valid_from > now:
            raise HTTPException(status_code=400, detail="Pass is not valid yet")
        if pass_obj.valid_until and pass_obj.valid_until < now:
            raise HTTPException(status_code=400, detail="Pass has expired")

        pass_obj.used = True
        pass_obj.used_date.append(datetime.now(UTC).replace(tzinfo=None))
        pass_obj.save()

        return {"message": "Pass is valid and has been marked as used"}
