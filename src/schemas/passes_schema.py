from datetime import UTC, datetime
from enum import StrEnum

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator


class PassTypeSimple(StrEnum):
    TEMPORARY = "temporary"
    TEMPORARY_PARTY = "temporary_party"
    TEMPORARY_GYM = "temporary_gym"


class CreatePassesSimple(BaseModel):
    pass_type: PassTypeSimple
    guest_name: str = Field(min_length=3, max_length=100)
    valid_from: datetime

    @field_validator("valid_from")
    def validate_valid_from(cls, value):
        if value < datetime.now(UTC):
            raise HTTPException(
                status_code=400, detail="valid_from must be in the future"
            )
        return value


class CreatePassesForDays(BaseModel):
    days: int = Field(gt=0, lt=8)
    guest_name: str = Field(min_length=3, max_length=100)
    valid_from: datetime
    reason: str = Field(min_length=10, max_length=200)

    @field_validator("valid_from")
    def validate_valid_from(cls, value):
        if value < datetime.now(UTC):
            raise HTTPException(
                status_code=400, detail="valid_from must be in the future"
            )
        return value


class PassesResponseUser(BaseModel):
    id: str = Field(alias="_id")
    status: str
    enabled: bool
    valid_from: datetime
    valid_until: datetime

    model_config = ConfigDict(populate_by_name=True)


class PassesResponseList(BaseModel):
    passes: list[PassesResponseUser]
