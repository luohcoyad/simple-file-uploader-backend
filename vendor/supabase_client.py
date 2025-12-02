from functools import lru_cache

from supabase import Client, create_client

from config import settings


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    if not settings.supabase_url or not settings.supabase_access_key:
        raise RuntimeError("Supabase credentials are not configured.")
    return create_client(settings.supabase_url, settings.supabase_access_key)
