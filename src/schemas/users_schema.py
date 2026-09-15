import re
import unicodedata
from datetime import date

from pydantic import BaseModel, EmailStr, Field, field_validator

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PHONE_RE = re.compile(r"^\+\d{10,12}$")
PASSWORD_WHITELIST = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*])(?!.*[\s~\\])[a-zA-Z\d!@#$%^&*]+$"
)
PASSWORD_REJECT = "Password must contain uppercase letters, lowercase letters, numbers, and special characters !@#$%^&*."
NAME_REJECT = "Name must contain only Latin alphabetic characters"
PHONE_REJECT = "Phone number must be in the format that begins with '+' followed by 10 to 12 digits"

PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 72


def _is_latin(char: str) -> bool:
    try:
        return "LATIN" in unicodedata.name(char)
    except ValueError:
        return False


def _validate_password(value: str) -> str:
    if not PASSWORD_WHITELIST.fullmatch(value):
        raise ValueError(PASSWORD_REJECT)
    return value


def _validate_name(value: str) -> str:
    if not value or not value.strip():
        raise ValueError(NAME_REJECT)
    if all(char.isspace() or _is_latin(char) for char in value):
        return value
    raise ValueError(NAME_REJECT)


def _validate_phone(value: str) -> str:
    if not PHONE_RE.fullmatch(value.strip()):
        raise ValueError(PHONE_REJECT)
    return value


class LogInUser(BaseModel):
    email: EmailStr
    password: str = Field(
        ..., min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH
    )


class SignUpUser(BaseModel):
    email: EmailStr
    password: str = Field(
        ..., min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH
    )
    first_name: str = Field(..., min_length=2, max_length=50)
    last_name: str = Field(..., min_length=2, max_length=50)
    birthdate: date
    phone_number: str = Field(..., min_length=11, max_length=13)

    @field_validator("password")
    def password_must_have(cls, v: str):
        return _validate_password(v)

    @field_validator("first_name", "last_name")
    def name_must_be_alpha(cls, v: str):
        return _validate_name(v)

    @field_validator("phone_number")
    def phone_must_be_polish_format(cls, v: str):
        return _validate_phone(v)

    @field_validator("birthdate", mode="before")
    def date_must_be_iso_format(cls, v):
        if isinstance(v, str) and not DATE_RE.fullmatch(v):
            raise ValueError("date must be in 'YYYY-MM-DD' ISO format")
        return v

    @field_validator("birthdate")
    def check_age(cls, v: date):
        today = date.today()
        month_day_passed = (today.month, today.day) < (v.month, v.day)
        age = today.year - v.year - (1 if month_day_passed else 0)
        if age < 18:
            raise ValueError("User must be at least 18 years old")
        if age > 120:
            raise ValueError("User age seems invalid (greater than 120 years)")
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
    def name_must_be_alpha(cls, v: str | None):
        return v if v is None else _validate_name(v)

    @field_validator("phone_number")
    def phone_must_be_polish_format(cls, v: str | None):
        return v if v is None else _validate_phone(v)


class UserPasswordUpdate(BaseModel):
    old_password: str = Field(
        ..., min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH
    )
    new_password: str = Field(
        ..., min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH
    )

    @field_validator("new_password")
    def password_must_have(cls, v: str):
        return _validate_password(v)


class SignUpResponse(BaseModel):
    message: str


class LoginResponse(BaseModel):
    access_token: str
    user_full_name: str


class UserProfileResponse(BaseModel):
    Hi: str
    email: EmailStr
    role: str | None
    house_id: str | None


class UserProfileUpdateResponse(BaseModel):
    message: str
    full_name: str
    phone_number: str


class PasswordUpdatedResponse(BaseModel):
    message: str


class UserListItem(BaseModel):
    email: EmailStr
    full_name: str
    enabled: bool
    house_id: str | None = None
    role: str | None = None


class UserListResponse(BaseModel):
    users: list[UserListItem]
    has_next: bool
    next_page: int | None = None


class UserByHouseResponse(BaseModel):
    user: UserListItem


class UserPagesResponse(BaseModel):
    total_pages: int
    total_users: int


class MessageResponse(BaseModel):
    message: str
