"""Supabase client initialization and connection management."""

import os
from typing import Optional

from dotenv import load_dotenv
from supabase import Client, create_client

# Load environment variables
load_dotenv()


class SupabaseClient:
    """Singleton Supabase client manager."""

    _instance: Optional[Client] = None

    @classmethod
    def get_client(cls) -> Client:
        """Get or create Supabase client instance."""
        if cls._instance is None:
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_KEY")

            if not url or not key:
                raise ValueError(
                    "SUPABASE_URL and SUPABASE_KEY must be set in environment variables"
                )

            cls._instance = create_client(url, key)

        return cls._instance

    @classmethod
    def get_service_client(cls) -> Client:
        """Get Supabase client with service role key (bypasses RLS)."""
        url = os.getenv("SUPABASE_URL")
        service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not url or not service_key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set for service client"
            )

        return create_client(url, service_key)


# Convenience function for getting client
def get_supabase() -> Client:
    """Get Supabase client instance."""
    return SupabaseClient.get_client()


def get_supabase_service() -> Client:
    """Get Supabase service client (bypasses RLS)."""
    return SupabaseClient.get_service_client()
