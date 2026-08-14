"""
Pydantic schemas for authentication request/response bodies.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegisterRequest(BaseModel):
    """Registration request schema."""

    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=8, description="Password (min 8 chars)")
    full_name: str = Field(..., min_length=1, description="Full name")


class UserLoginRequest(BaseModel):
    """Login request schema."""

    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., description="Password")


class UserResponse(BaseModel):
    """User response schema (no password)."""

    id: str
    email: str
    full_name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """Auth token response schema."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class AuthResponse(BaseModel):
    """Combined authentication response."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse
