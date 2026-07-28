from __future__ import annotations

from functools import lru_cache
from typing import Any, Dict, Optional

from supabase import Client, create_client

from app.core.config import settings


class SupabaseNotConfiguredError(RuntimeError):
    pass


@lru_cache(maxsize=1)
def get_supabase_service_client() -> Client:
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise SupabaseNotConfiguredError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


@lru_cache(maxsize=1)
def get_supabase_auth_client() -> Client:
    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        raise SupabaseNotConfiguredError("SUPABASE_URL and SUPABASE_ANON_KEY are required")
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)


def ping_supabase() -> Dict[str, Any]:
    client = get_supabase_service_client()
    response = client.table("warga").select("id").limit(1).execute()
    return {
        "connected": True,
        "rows_sampled": len(response.data or []),
    }
