from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class RegisterRequestSchema(BaseModel):
    email: EmailStr = Field(..., description="Email address for the user")
    username: str = Field(..., min_length=3, max_length=150, description="Username for login")
    password: str = Field(..., min_length=6, description="Password (hashed in DB)")
    name: Optional[str] = Field(default="", max_length=255)
    invite_token: str = Field(..., min_length=1, description="Invite token required to register")
    cf_turnstile_token: str = Field(
        ...,
        min_length=1,
        description="Cloudflare Turnstile response token",
    )


class LoginRequestSchema(BaseModel):
    email: str = Field(..., description="Email address or username of the user")
    password: str = Field(..., description="User password")
    cf_turnstile_token: str = Field(
        ...,
        min_length=1,
        description="Cloudflare Turnstile response token",
    )


class RefreshTokenRequestSchema(BaseModel):
    refresh: str = Field(..., description="Refresh JWT token")


class UserResponseSchema(BaseModel):
    id: int
    username: str
    email: str
    name: str
    is_active: bool
    is_staff: bool

    class Config:
        from_attributes = True


class TokenResponseSchema(BaseModel):
    access: str
    refresh: str
    user: UserResponseSchema


class CreateInviteRequestSchema(BaseModel):
    email: Optional[EmailStr] = Field(
        default=None,
        description="Lock registration to this email. Omit for an open shareable link.",
    )
    max_uses: int = Field(default=1, ge=1, le=100)
    expires_in_days: int = Field(default=7, ge=1, le=90)


class InviteResponseSchema(BaseModel):
    id: int
    token: str
    email: Optional[str] = None
    expires_at: datetime
    max_uses: int
    uses_count: int
    status: str
    invite_path: str
    created_at: datetime
    revoked_at: Optional[datetime] = None
    created_by_id: int

    class Config:
        from_attributes = True


class InviteValidateResponseSchema(BaseModel):
    valid: bool
    email: Optional[str] = None
    status: str
    expires_at: Optional[datetime] = None
