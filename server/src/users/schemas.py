from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class RegisterRequestSchema(BaseModel):
    email: EmailStr = Field(..., description="Email address for the user")
    username: str = Field(..., min_length=3, max_length=150, description="Username for login")
    password: str = Field(..., min_length=6, description="Password (hashed in DB)")
    name: Optional[str] = Field(default="", max_length=255)


class LoginRequestSchema(BaseModel):
    email: str = Field(..., description="Email address or username of the user")
    password: str = Field(..., description="User password")


class RefreshTokenRequestSchema(BaseModel):
    refresh: str = Field(..., description="Refresh JWT token")


class UserResponseSchema(BaseModel):
    id: int
    username: str
    email: str
    name: str
    is_active: bool

    class Config:
        from_attributes = True


class TokenResponseSchema(BaseModel):
    access: str
    refresh: str
    user: UserResponseSchema
