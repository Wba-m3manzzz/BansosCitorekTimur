from __future__ import annotations

from typing import Optional

from pydantic import Field
from app.schemas.common import CamelModel


class LoginRequest(CamelModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class LogoutRequest(CamelModel):
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None


class RefreshRequest(CamelModel):
    refresh_token: str


class AdminProfile(CamelModel):
    id: str
    user_id: str
    username: Optional[str] = None
    full_name: str
    role: str
    active: bool


class LoginResponse(CamelModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: Optional[int] = None
    admin: AdminProfile


class CurrentAdminResponse(CamelModel):
    authenticated: bool
    admin: Optional[AdminProfile] = None
