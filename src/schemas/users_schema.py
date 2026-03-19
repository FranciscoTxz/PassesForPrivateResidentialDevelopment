import re
import unicodedata
from datetime import date

from fastapi import HTTPException
from pydantic import BaseModel, EmailStr, Field, field_validator

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PHONE_RE = re.compile(r"^\+\d{10,12}$")
PASSWORD_WHITELIST = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*])(?!.*[\s~\\])[a-zA-Z\d!@#$%^&*]+$"
)
PASSWORD_REJECT = "Password must contain uppercase letters, lowercase letters, numbers, and special characters !@#$%^&*."


class LogInUser(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=16)


class SignUpUser(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=16)
    first_name: str = Field(..., min_length=2, max_length=50)
    last_name: str = Field(..., min_length=2, max_length=50)
    birthdate: date
    phone_number: str = Field(..., min_length=11, max_length=13)

    @field_validator("password")
    def password_must_have(cls, v: str):
        if not PASSWORD_WHITELIST.fullmatch(v):
            raise HTTPException(
                status_code=400,
                detail=PASSWORD_REJECT,
            )
        return v

    @field_validator("first_name", "last_name")
    def name_must_be_alpha(cls, v: str):
        def is_latin(c: str) -> bool:
            try:
                return "LATIN" in unicodedata.name(c)
            except ValueError:
                return False

        if not v or all(c.isspace() or is_latin(c) for c in v):
            return v
        raise HTTPException(
            status_code=400, detail="Name must contain only Latin alphabetic characters"
        )

    @field_validator("phone_number")
    def phone_must_be_polish_format(cls, v: str):
        if not PHONE_RE.fullmatch(v.strip()):
            raise HTTPException(
                status_code=400,
                detail="Phone number must be in the format that begins with '+' followed by 10 to 12 digits",
            )
        return v

    @field_validator("birthdate", mode="before")
    def date_must_be_iso_format(cls, v):
        if isinstance(v, str) and not DATE_RE.fullmatch(v):
            raise HTTPException(
                status_code=400, detail="date must be in 'YYYY-MM-DD' ISO format"
            )
        return v

    @field_validator("birthdate")
    def check_age(cls, v: date):
        today = date.today()
        month_day_passed = (today.month, today.day) < (v.month, v.day)
        age = today.year - v.year - (1 if month_day_passed else 0)
        if age < 18:
            raise HTTPException(
                status_code=400, detail="User must be at least 18 years old"
            )
        if age > 120:
            raise HTTPException(
                status_code=400,
                detail="User age seems invalid (greater than 120 years)",
            )
        return v


class UserInfo(BaseModel):
    email: EmailStr
    full_name: str
    enabled: bool
    house_id: str | None
    role: str | None


class UserNamePhone(BaseModel):
    first_name: str | None = Field(None, min_length=2, max_length=50)
    last_name: str | None = Field(None, min_length=2, max_length=50)
    phone_number: str | None = Field(None, min_length=11, max_length=13)

    @field_validator("first_name", "last_name")
    def name_must_be_alpha(cls, v: str):
        def is_latin(c: str) -> bool:
            try:
                return "LATIN" in unicodedata.name(c)
            except ValueError:
                return False

        if not v or all(c.isspace() or is_latin(c) for c in v):
            return v
        raise HTTPException(
            status_code=400, detail="Name must contain only Latin alphabetic characters"
        )

    @field_validator("phone_number")
    def phone_must_be_polish_format(cls, v: str):
        if not PHONE_RE.fullmatch(v.strip()):
            raise HTTPException(
                status_code=400,
                detail="Phone number must be in the format that begins with '+' followed by 10 to 12 digits",
            )
        return v


class UserPasswordUpdate(BaseModel):
    old_password: str = Field(..., min_length=8, max_length=16)
    new_password: str = Field(..., min_length=8, max_length=16)

    @field_validator("new_password")
    def password_must_have(cls, v: str):
        if not PASSWORD_WHITELIST.fullmatch(v):
            raise HTTPException(
                status_code=400,
                detail=PASSWORD_REJECT,
            )
        return v
