"""LLM Agentic Loop - Mistral tool-calling agent implementation.

This is the core AI integration. It runs a multi-turn conversation where:
1. The LLM receives the user prompt + available tools + farm context
2. The LLM decides which tools to call (get_weather, get_market_prices, etc.)
3. We execute those tools and return the results
4. The LLM processes results and either calls more tools or produces final output
5. Loop continues until the LLM says 'stop' (no more tool calls needed)
"""

import json
import logging
from typing import Any
from uuid import UUID

from .mistral_client import MistralClient
from .tool_registry import get_tool_registry

logger = logging.getLogger(__name__)

# Hard limit on tool call rounds to prevent infinite loops
MAX_TOOL_ROUNDS = 8

# Mistral models to use
MISTRAL_LARGE = "mistral-large-latest"
PIXTRAL_MODEL = "pixtral-12b-2409"


class AgentResult:
    """Result from a completed LLM agent run."""

    def __init__(
        self,
        final_response: str,
        tool_calls_made: list[dict[str, Any]],
        rounds: int,
        usage: dict[str, int],
    ) -> None:
        self.final_response = final_response
        self.tool_calls_made = tool_calls_made
        self.rounds = rounds
        self.usage = usage

    def to_dict(self) -> dict[str, Any]:
        return {
            "final_response": self.final_response,
            "tool_calls_made": self.tool_calls_made,
            "rounds": self.rounds,
            "usage": self.usage,
        }


class LLMAgent:
    """Agentic LLM that calls tools iteratively to answer questions about farms."""

    def __init__(self, mistral_client: MistralClient | None = None) -> None:
        self.client = mistral_client or MistralClient()
        self.registry = get_tool_registry()

    async def run(
        self,
        system_prompt: str,
        user_message: str,
        tool_names: list[str] | None = None,
        context: dict[str, Any] | None = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        model: str = MISTRAL_LARGE,
    ) -> AgentResult:
        """
        Run the LLM agentic loop.

        Args:
            system_prompt: System instructions for the LLM
            user_message: The farmer's request or context to analyze
            tool_names: Which tools to expose (None = all registered tools)
            context: Additional context injected into the system prompt
            temperature: Sampling temperature (lower = more deterministic)
            max_tokens: Maximum tokens in any single response
            model: Mistral model to use

        Returns:
            AgentResult with final response and all tool calls made
        """
        # Build tool schemas
        available_tools = self._get_tool_schemas(tool_names)

        # Build initial messages
        messages: list[dict[str, Any]] = [
            {
                "role": "system",
                "content": self._build_system_prompt(system_prompt, context),
            },
            {"role": "user", "content": user_message},
        ]

        all_tool_calls: list[dict[str, Any]] = []
        total_usage: dict[str, int] = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        rounds = 0

        logger.info(f"Starting LLM agent run with {len(available_tools)} tools")

        while rounds < MAX_TOOL_ROUNDS:
            rounds += 1
            logger.info(f"Agent round {rounds}/{MAX_TOOL_ROUNDS}")

            # Call Mistral
            response = await self.client.chat_completion(
                messages=messages,
                tools=available_tools if available_tools else None,
                tool_choice="auto",
                temperature=temperature,
                max_tokens=max_tokens,
                model=model,
            )

            # Track token usage
            if response.get("usage"):
                for k in total_usage:
                    total_usage[k] += response["usage"].get(k, 0)

            finish_reason = response.get("finish_reason", "stop")
            tool_calls = response.get("tool_calls", [])

            # Add assistant message
            messages.append({
                "role": "assistant",
                "content": response.get("content") or "",
                "tool_calls": tool_calls if tool_calls else [],
            })

            # If no tool calls, or finish_reason is stop → we're done
            if not tool_calls or finish_reason == "stop":
                logger.info(
                    f"Agent completed in {rounds} rounds. "
                    f"Total tool calls: {len(all_tool_calls)}"
                )
                return AgentResult(
                    final_response=response.get("content") or "",
                    tool_calls_made=all_tool_calls,
                    rounds=rounds,
                    usage=total_usage,
                )

            # Execute each tool call and add results to messages
            for tc in tool_calls:
                tool_name = tc["function"]["name"]
                raw_args = tc["function"]["arguments"]

                try:
                    args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                except json.JSONDecodeError:
                    args = {}

                logger.info(f"Executing tool: {tool_name} with args: {args}")

                tool_result = await self._execute_tool(tool_name, args)
                all_tool_calls.append({
                    "tool_name": tool_name,
                    "arguments": args,
                    "result": tool_result,
                    "round": rounds,
                })

                # Feed tool result back into conversation
                messages.append({
                    "role": "tool",
                    "content": json.dumps(tool_result, default=str),
                    "tool_call_id": tc["id"],
                })

        # Max rounds hit, return what we have
        logger.warning(f"Agent hit max rounds ({MAX_TOOL_ROUNDS}). Returning last response.")
        last_content = next(
            (m["content"] for m in reversed(messages) if m["role"] == "assistant"),
            "Unable to generate full response within tool call limit.",
        )
        return AgentResult(
            final_response=last_content,
            tool_calls_made=all_tool_calls,
            rounds=rounds,
            usage=total_usage,
        )

    async def run_vision(
        self,
        system_prompt: str,
        image_base64: str,
        image_mime: str = "image/jpeg",
        text_prompt: str = "Analyze this farm image.",
    ) -> str:
        """
        Run Mistral vision model to analyze a farm image.

        Args:
            system_prompt: Instructions for image analysis
            image_base64: Base64-encoded image data
            image_mime: MIME type of image
            text_prompt: Text part of the prompt

        Returns:
            LLM description/analysis of the image
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{image_mime};base64,{image_base64}",
                        },
                    },
                    {"type": "text", "text": text_prompt},
                ],
            },
        ]

        response = await self.client.chat_completion(
            messages=messages,
            tools=None,
            temperature=0.2,
            max_tokens=2048,
            model=PIXTRAL_MODEL,
        )
        return response.get("content") or ""

    async def _execute_tool(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        """Execute a registered tool and return its result."""
        handler = self.registry.get_handler(tool_name)
        if not handler:
            return {"error": f"Tool '{tool_name}' not found in registry", "success": False}

        try:
            result = await handler(**args)
            return result if isinstance(result, dict) else {"result": result, "success": True}
        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {e}")
            return {"error": str(e), "success": False}

    def _get_tool_schemas(self, tool_names: list[str] | None) -> list[dict[str, Any]]:
        """Get OpenAI-format tool schemas for specified tools."""
        if tool_names is None:
            schemas = self.registry.get_all_schemas()
        else:
            schemas = [
                s for name in tool_names
                if (s := self.registry.get_tool_schema(name)) is not None
            ]
        # Strip internal metadata (requires_auth) before sending to LLM
        clean = []
        for s in schemas:
            clean.append({
                "type": s.get("type", "function"),
                "function": s["function"],
            })
        return clean

    def _build_system_prompt(
        self, base_prompt: str, context: dict[str, Any] | None
    ) -> str:
        """Inject context data into the system prompt."""
        if not context:
            return base_prompt

        context_str = "\n\n## Available Farm Context\n"
        for key, value in context.items():
            if value:
                context_str += f"\n### {key}\n```json\n{json.dumps(value, default=str, indent=2)}\n```\n"

        return base_prompt + context_str


# ─── Singleton ────────────────────────────────────────────────────────────────
_agent: LLMAgent | None = None


def get_llm_agent() -> LLMAgent:
    """Get global LLM agent instance."""
    global _agent
    if _agent is None:
        _agent = LLMAgent()
    return _agent
