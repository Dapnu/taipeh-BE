"""
Database connection and client initialization
"""

from supabase import create_client, Client
from app.core.config import settings


class SupabaseClient:
    """Supabase client wrapper for database operations"""
    
    _client: Client | None = None
    
    @classmethod
    def get_client(cls) -> Client:
        """
        Get or create Supabase client instance
        
        Returns:
            Client: Supabase client instance
        """
        if cls._client is None:
            cls._client = create_client(
                supabase_url=settings.SUPABASE_URL,
                supabase_key=settings.SUPABASE_KEY
            )
        return cls._client
    
    @classmethod
    async def health_check(cls) -> bool:
        """
        Check if the database connection is healthy
        
        Returns:
            bool: True if connection is healthy, False otherwise
        """
        try:
            client = cls.get_client()
            # Simple query to test connection
            # This will fail gracefully if connection is not available
            response = client.table('_health_check').select("*").limit(1).execute()
            return True
        except Exception:
            # Even if table doesn't exist, if we can connect, that's good enough
            # A connection error will be caught here
            return False


# Convenience function to get the client
def get_db() -> Client:
    """
    Dependency function to get database client
    
    Returns:
        Client: Supabase client instance
    """
    return SupabaseClient.get_client()
