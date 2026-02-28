"""Tool executor for running AI tools with audit logging."""

import json
import logging
import time
from typing import Any, Dict, Optional
from uuid import UUID

from ...services.audit.audit_logger import get_audit_logger
from .tool_registry import get_tool_registry

logger = logging.getLogger(__name__)


class ToolExecutor:
    """Executor for AI tools with automatic audit logging."""

    def __init__(self) -> None:
        """Initialize tool executor."""
        self.registry = get_tool_registry()
        self.audit_logger = get_audit_logger()

    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        user_id: Optional[UUID] = None,
        farm_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Execute a tool and log the call.

        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments
            user_id: User triggering the call
            farm_id: Related farm

        Returns:
            Tool execution result

        Raises:
            ValueError: If tool not found or execution fails
        """
        # Get tool handler
        handler = self.registry.get_handler(tool_name)
        if not handler:
            raise ValueError(f"Tool not found: {tool_name}")

        # Start timing
        start_time = time.time()
        status = "success"
        error_message = None
        result = None

        try:
            # Execute tool
            logger.info(f"Executing tool: {tool_name} with args: {arguments}")
            result = await handler(**arguments)

            # Calculate execution time
            execution_time_ms = int((time.time() - start_time) * 1000)

            # Create response summary (exclude large data)
            response_summary = self._create_summary(result)

            # Log to audit trail
            await self.audit_logger.log_tool_call(
                user_id=user_id,
                farm_id=farm_id,
                tool_name=tool_name,
                request_payload=arguments,
                response_summary=response_summary,
                execution_time_ms=execution_time_ms,
                cost_estimate_usd=0.0,  # Tool calls are free (API costs tracked separately)
                status=status,
            )

            return {
                "success": True,
                "data": result,
                "execution_time_ms": execution_time_ms,
            }

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            status = "error"
            error_message = str(e)

            logger.error(f"Tool execution failed: {tool_name} - {error_message}")

            # Log failure
            await self.audit_logger.log_tool_call(
                user_id=user_id,
                farm_id=farm_id,
                tool_name=tool_name,
                request_payload=arguments,
                response_summary={},
                execution_time_ms=execution_time_ms,
                cost_estimate_usd=0.0,
                status=status,
                error_message=error_message,
            )

            return {
                "success": False,
                "error": error_message,
                "execution_time_ms": execution_time_ms,
            }

    async def execute_tool_calls(
        self,
        tool_calls: list[Dict[str, Any]],
        user_id: Optional[UUID] = None,
        farm_id: Optional[UUID] = None,
    ) -> list[Dict[str, Any]]:
        """
        Execute multiple tool calls from LLM response.

        Args:
            tool_calls: List of tool calls from LLM
            user_id: User ID
            farm_id: Farm ID

        Returns:
            List of tool results
        """
        results = []

        for tool_call in tool_calls:
            tool_name = tool_call["function"]["name"]
            arguments_str = tool_call["function"]["arguments"]

            # Parse arguments
            try:
                arguments = json.loads(arguments_str)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON arguments for {tool_name}: {e}")
                results.append(
                    {
                        "tool_call_id": tool_call["id"],
                        "success": False,
                        "error": f"Invalid JSON arguments: {str(e)}",
                    }
                )
                continue

            # Execute tool
            result = await self.execute_tool(
                tool_name=tool_name,
                arguments=arguments,
                user_id=user_id,
                farm_id=farm_id,
            )

            results.append(
                {
                    "tool_call_id": tool_call["id"],
                    **result,
                }
            )

        return results

    def _create_summary(self, data: Any, max_items: int = 10) -> Dict[str, Any]:
        """
        Create a summary of tool output for audit logging.

        Args:
            data: Tool output data
            max_items: Max array items to include

        Returns:
            Summarized data
        """
        if isinstance(data, dict):
            summary = {}
            for key, value in data.items():
                if isinstance(value, list):
                    summary[key] = f"[{len(value)} items]"
                elif isinstance(value, str) and len(value) > 200:
                    summary[key] = value[:200] + "..."
                else:
                    summary[key] = value
            return summary

        elif isinstance(data, list):
            return {
                "type": "array",
                "count": len(data),
                "sample": data[:max_items] if len(data) > max_items else data,
            }

        else:
            return {"value": str(data)}


# Singleton instance
_tool_executor: Optional[ToolExecutor] = None


def get_tool_executor() -> ToolExecutor:
    """Get tool executor singleton instance."""
    global _tool_executor
    if _tool_executor is None:
        _tool_executor = ToolExecutor()
    return _tool_executor
