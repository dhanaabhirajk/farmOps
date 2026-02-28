"""Tool registry for managing available AI tools and their schemas."""

import inspect
import logging
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry for AI tools with OpenAI function calling schema."""

    def __init__(self) -> None:
        """Initialize tool registry."""
        self.tools: Dict[str, Dict[str, Any]] = {}
        self.handlers: Dict[str, Callable] = {}

    def register(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: Callable,
        requires_auth: bool = True,
    ) -> None:
        """
        Register a tool with the registry.

        Args:
            name: Tool name (must be unique)
            description: Human-readable description
            parameters: JSON Schema for parameters
            handler: Async function to execute the tool
            requires_auth: Whether tool requires authentication
        """
        if name in self.tools:
            logger.warning(f"Tool {name} already registered, overwriting")

        # Store OpenAI function schema
        self.tools[name] = {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters,
            },
            "requires_auth": requires_auth,
        }

        # Store handler
        self.handlers[name] = handler
        logger.info(f"Registered tool: {name}")

    def register_decorator(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        requires_auth: bool = True,
    ) -> Callable:
        """
        Decorator for registering tools.

        Usage:
            @tool_registry.register_decorator(
                name="get_weather",
                description="Get weather forecast",
                parameters={...}
            )
            async def get_weather(location: str, days: int):
                ...

        Args:
            name: Tool name
            description: Tool description
            parameters: JSON Schema for parameters
            requires_auth: Requires authentication

        Returns:
            Decorator function
        """

        def decorator(func: Callable) -> Callable:
            self.register(name, description, parameters, func, requires_auth)
            return func

        return decorator

    def get_tool_schema(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get OpenAI function schema for a tool.

        Args:
            name: Tool name

        Returns:
            Tool schema or None if not found
        """
        return self.tools.get(name)

    def get_all_schemas(self) -> List[Dict[str, Any]]:
        """
        Get all tool schemas for LLM.

        Returns:
            List of tool schemas
        """
        return list(self.tools.values())

    def get_handler(self, name: str) -> Optional[Callable]:
        """
        Get handler function for a tool.

        Args:
            name: Tool name

        Returns:
            Handler function or None if not found
        """
        return self.handlers.get(name)

    def list_tools(self) -> List[str]:
        """
        List all registered tool names.

        Returns:
            List of tool names
        """
        return list(self.tools.keys())

    def remove_tool(self, name: str) -> bool:
        """
        Remove a tool from the registry.

        Args:
            name: Tool name

        Returns:
            True if removed, False if not found
        """
        if name in self.tools:
            del self.tools[name]
            del self.handlers[name]
            logger.info(f"Removed tool: {name}")
            return True
        return False


# Global tool registry
_tool_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Get global tool registry instance."""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
    return _tool_registry
