from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import jwt
from jwt import PyJWTError
from supabase import Client

from app.core.config import settings
from app.db.supabase import get_supabase_auth_client, get_supabase_service_client
from app.schemas.auth import AdminProfile

logger = logging.getLogger(__name__)


class AuthError(RuntimeError):
    pass


class AuthService:
    def __init__(self, auth_client: Optional[Client] = None, service_client: Optional[Client] = None) -> None:
        self.auth_client = auth_client or get_supabase_auth_client()
        self.service_client = service_client or get_supabase_service_client()

    def login(self, username: str, password: str) -> Dict[str, Any]:
        # Lookup email dari admin_profiles berdasarkan username
        email = self._get_email_by_username(username)

        try:
            response = self.auth_client.auth.sign_in_with_password({"email": email, "password": password})
        except Exception as exc:
            logger.warning("Supabase auth login failed: %s", exc)
            raise AuthError("Username atau password tidak valid") from exc

        session = getattr(response, "session", None)
        user = getattr(response, "user", None)
        if not session or not user:
            raise AuthError("Autentikasi gagal")

        self._invalidate_other_sessions(session.access_token)

        admin_profile = self._get_admin_profile(str(user.id))
        return {
            "access_token": self._create_access_token(str(user.id)),
            "refresh_token": session.refresh_token,
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "admin": admin_profile,
        }

    def _get_email_by_username(self, username: str) -> str:
        """Lookup email dari auth.users melalui admin_profiles berdasarkan username."""
        response = (
            self.service_client.table("admin_profiles")
            .select("user_id,active")
            .eq("username", username)
            .limit(1)
            .execute()
        )
        items = response.data or []
        if not items:
            raise AuthError("Username atau password tidak valid")
        if not items[0].get("active", False):
            raise AuthError("Akun tidak aktif")

        user_id = items[0]["user_id"]
        # Ambil email dari Supabase Auth admin API
        try:
            user_response = self.service_client.auth.admin.get_user_by_id(user_id)
            user_obj = getattr(user_response, "user", None)
            if not user_obj or not getattr(user_obj, "email", None):
                raise AuthError("Email pengguna tidak ditemukan")
            return user_obj.email
        except AuthError:
            raise
        except Exception as exc:
            logger.warning("Failed to get user email by id: %s", exc)
            raise AuthError("Username atau password tidak valid") from exc

    def _get_admin_profile(self, user_id: str) -> AdminProfile:
        response = (
            self.service_client.table("admin_profiles")
            .select("id,user_id,username,full_name,role,active")
            .eq("user_id", user_id)
            .eq("active", True)
            .limit(1)
            .execute()
        )
        items = response.data or []
        if not items:
            raise AuthError("Akun admin tidak ditemukan atau tidak aktif")
        return AdminProfile(**items[0])

    def refresh(self, refresh_token: str) -> Dict[str, Any]:
        try:
            response = self.auth_client.auth.refresh_session(refresh_token)
        except Exception as exc:
            logger.warning("Supabase auth refresh failed: %s", exc)
            raise AuthError("Refresh token tidak valid atau kedaluwarsa") from exc

        session = getattr(response, "session", None)
        user = getattr(response, "user", None)
        if not session or not user:
            raise AuthError("Refresh token tidak valid atau kedaluwarsa")

        admin_profile = self._get_admin_profile(str(user.id))
        return {
            "access_token": self._create_access_token(str(user.id)),
            "refresh_token": session.refresh_token,
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "admin": admin_profile,
        }

    def _create_access_token(self, user_id: str) -> str:
        if not settings.SUPABASE_JWT_SECRET:
            raise AuthError("Token secret belum dikonfigurasi")

        payload = {
            "sub": user_id,
            "exp": datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        }
        return jwt.encode(payload, settings.SUPABASE_JWT_SECRET, algorithm="HS256")

    def _decode_access_token(self, access_token: str) -> str:
        if not settings.SUPABASE_JWT_SECRET:
            raise AuthError("Token secret belum dikonfigurasi")

        try:
            payload = jwt.decode(access_token, settings.SUPABASE_JWT_SECRET, algorithms=["HS256"])
            user_id = payload.get("sub")
            if not user_id:
                raise AuthError("Token tidak valid")
            return user_id
        except PyJWTError as exc:
            raise AuthError("Token tidak valid atau kedaluwarsa") from exc

    def _invalidate_other_sessions(self, access_token: str) -> None:
        try:
            self.service_client.auth.admin.sign_out(access_token, scope="others")
        except Exception as exc:
            logger.warning("Failed to revoke other sessions: %s", exc)

    def resolve_admin_from_token(self, access_token: str) -> AdminProfile:
        user_id = self._decode_access_token(access_token)
        return self._get_admin_profile(user_id)

    def logout(self, access_token: str | None = None, refresh_token: str | None = None) -> Dict[str, str]:
        if refresh_token:
            try:
                response = self.auth_client.auth.refresh_session(refresh_token)
                session = getattr(response, "session", None)
                if session and getattr(session, "access_token", None):
                    self.service_client.auth.admin.sign_out(session.access_token, scope="global")
            except Exception as exc:
                logger.warning("Supabase auth logout failed: %s", exc)
        elif access_token:
            try:
                self.service_client.auth.admin.sign_out(access_token, scope="global")
            except Exception as exc:
                logger.warning("Supabase auth logout failed: %s", exc)

        return {
            "message": "Logout berhasil. Hapus token di frontend untuk menutup sesi."
        }


def get_auth_service() -> AuthService:
    return AuthService()
