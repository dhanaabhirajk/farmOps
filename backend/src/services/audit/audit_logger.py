"""Audit logging service for tracking all external API calls and AI tool executions."""

import time
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from ..db.supabase_client import get_supabase_service


class AuditLogger:
    """Service for logging all external data fetches and AI tool calls."""

    def __init__(self) -> None:
        """Initialize audit logger."""
        self.supabase = get_supabase_service()  # Use service role to bypass RLS

    async def log_tool_call(
        self,
        user_id: Optional[UUID],
        farm_id: Optional[UUID],
        tool_name: str,
        request_payload: Dict[str, Any],
        response_summary: Dict[str, Any],
        execution_time_ms: int,
        cost_estimate_usd: float = 0.0,
        status: str = "success",
        error_message: Optional[str] = None,
    ) -> str:
        """
        Log an LLM tool call.

        Args:
            user_id: User who triggered the call
            farm_id: Related farm (if applicable)
            tool_name: Name of the tool (e.g., 'get_market_prices')
            request_payload: Input parameters
            response_summary: Key outputs (not full response)
            execution_time_ms: Execution time in milliseconds
            cost_estimate_usd: Estimated cost
            status: success, error, timeout, rate_limited
            error_message: Error details if status != success

        Returns:
            Log ID
        """
        log_entry = {
            "user_id": str(user_id) if user_id else None,
            "farm_id": str(farm_id) if farm_id else None,
            "source": tool_name,
            "source_type": "llm_tool",
            "request_payload": request_payload,
            "response_summary": response_summary,
            "execution_time_ms": execution_time_ms,
            "cost_estimate_usd": cost_estimate_usd,
            "status": status,
            "error_message": error_message,
        }

        result = self.supabase.table("data_audit_logs").insert(log_entry).execute()
        return result.data[0]["id"]

    async def log_external_api_call(
        self,
        user_id: Optional[UUID],
        farm_id: Optional[UUID],
        api_name: str,
        request_payload: Dict[str, Any],
        response_summary: Dict[str, Any],
        execution_time_ms: int,
        cost_estimate_usd: float = 0.0,
        status: str = "success",
        error_message: Optional[str] = None,
    ) -> str:
        """
        Log an external API call (GEE, IMD, OpenWeatherMap, AGMARKNET).

        Args:
            user_id: User who triggered the call
            farm_id: Related farm
            api_name: API identifier (e.g., 'gee_ndvi', 'imd_weather')
            request_payload: Request parameters
            response_summary: Key response data
            execution_time_ms: Execution time
            cost_estimate_usd: Estimated cost
            status: success, error, timeout, rate_limited
            error_message: Error details

        Returns:
            Log ID
        """
        log_entry = {
            "user_id": str(user_id) if user_id else None,
            "farm_id": str(farm_id) if farm_id else None,
            "source": api_name,
            "source_type": "external_api",
            "request_payload": request_payload,
            "response_summary": response_summary,
            "execution_time_ms": execution_time_ms,
            "cost_estimate_usd": cost_estimate_usd,
            "status": status,
            "error_message": error_message,
        }

        result = self.supabase.table("data_audit_logs").insert(log_entry).execute()
        return result.data[0]["id"]

    async def log_computation(
        self,
        user_id: Optional[UUID],
        farm_id: Optional[UUID],
        computation_name: str,
        request_payload: Dict[str, Any],
        response_summary: Dict[str, Any],
        execution_time_ms: int,
        status: str = "success",
        error_message: Optional[str] = None,
    ) -> str:
        """
        Log a deterministic computation (yield calculation, profit estimation, etc.).

        Args:
            user_id: User
            farm_id: Related farm
            computation_name: Name of computation (e.g., 'yield_calculation')
            request_payload: Input parameters
            response_summary: Computed outputs
            execution_time_ms: Execution time
            status: success or error
            error_message: Error details

        Returns:
            Log ID
        """
        log_entry = {
            "user_id": str(user_id) if user_id else None,
            "farm_id": str(farm_id) if farm_id else None,
            "source": computation_name,
            "source_type": "computation",
            "request_payload": request_payload,
            "response_summary": response_summary,
            "execution_time_ms": execution_time_ms,
            "cost_estimate_usd": 0.0,  # Computations are free
            "status": status,
            "error_message": error_message,
        }

        result = self.supabase.table("data_audit_logs").insert(log_entry).execute()
        return result.data[0]["id"]

    async def get_farm_audit_trail(
        self, farm_id: UUID, source: Optional[str] = None, limit: int = 100
    ) -> list[Dict[str, Any]]:
        """
        Get audit trail for a farm.

        Args:
            farm_id: Farm ID
            source: Filter by specific source (optional)
            limit: Max results

        Returns:
            List of audit log entries
        """
        query = (
            self.supabase.table("data_audit_logs")
            .select("*")
            .eq("farm_id", str(farm_id))
            .order("created_at", desc=True)
            .limit(limit)
        )

        if source:
            query = query.eq("source", source)

        result = query.execute()
        return result.data


# Singleton instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get audit logger singleton instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger
