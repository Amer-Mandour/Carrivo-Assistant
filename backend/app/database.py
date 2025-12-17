"""
اتصال بـ Supabase - Singleton Pattern
"""

from supabase import create_client, Client
from typing import Optional
from .config import settings

_supabase_client: Optional[Client] = None

def get_supabase() -> Client:
    """الحصول على عميل Supabase (Singleton)"""
    global _supabase_client
    
    if _supabase_client is None:
        _supabase_client = create_client(
            settings.supabase_url,
            settings.supabase_anon_key
        )
    
    return _supabase_client

def execute_query(query: str, params: dict = None):
    """تنفيذ استعلام SQL مباشر (للمشرفين)"""
    client = get_supabase()
    return client.postgrest.rpc('exec_sql', {'sql': query}).execute()