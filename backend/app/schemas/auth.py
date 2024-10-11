from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.users import UserRead


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=120)

    @field_validator("password")
    @classmethod
    def _password_strength(cls, value: str) -> str:
        if not any(ch.isdigit() for ch in value):
            raise ValueError("Password must contain at least one digit")
        if not any(ch.isalpha() for ch in value):
            raise ValueError("Password must contain at least one letter")
        return value

    @field_validator("name")
    @classmethod
    def _strip_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Name cannot be blank")
        return stripped


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=10)


class LogoutRequest(BaseModel):
    refresh_token: str = Field(min_length=10)


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class AuthResponse(TokenPair):
    user: UserRead
