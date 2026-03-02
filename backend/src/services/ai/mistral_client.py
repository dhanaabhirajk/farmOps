"""Mistral AI client for LLM interactions (OpenAI-compatible API)."""

import logging
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from openai import AsyncOpenAI

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class MistralClient:
    """Client for Mistral AI using OpenAI-compatible API."""

    def __init__(self) -> None:
        """Initialize Mistral client."""
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            raise ValueError("MISTRAL_API_KEY must be set in environment variables")

        # Mistral uses OpenAI-compatible API
        self.client = AsyncOpenAI(
            timeout=90,
            api_key=api_key,
            base_url="https://api.mistral.ai/v1",
        )

        # Default model
        self.default_model = os.getenv("MISTRAL_MODEL", "mistral-large-latest")

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: str = "auto",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send chat completion request to Mistral.

        Args:
            messages: List of message dicts with 'role' and 'content'
            tools: List of tool definitions in OpenAI format
            tool_choice: 'auto', 'none', or specific tool name
            temperature: Sampling temperature (0-1)
            max_tokens: Max tokens in response
            model: Model to use (defaults to MISTRAL_MODEL env var)

        Returns:
            Response dict with 'content', 'tool_calls', and 'finish_reason'
        """
        try:
            response = await self.client.chat.completions.create(
                model=model or self.default_model,
                messages=messages,
                tools=tools,
                tool_choice=tool_choice,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            message = response.choices[0].message
            result = {
                "content": message.content,
                "tool_calls": [],
                "finish_reason": response.choices[0].finish_reason,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
            }

            # Parse tool calls if present
            if message.tool_calls:
                result["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in message.tool_calls
                ]

            return result

        except Exception as e:
            logger.error(f"Mistral API error: {str(e)}")
            raise

    async def stream_chat_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: str = "auto",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        model: Optional[str] = None,
    ):
        """
        Stream chat completion from Mistral.

        Args:
            messages: List of message dicts
            tools: Tool definitions
            tool_choice: Tool selection strategy
            temperature: Sampling temperature
            max_tokens: Max tokens
            model: Model to use

        Yields:
            Chunks of the response
        """
        try:
            stream = await self.client.chat.completions.create(
                model=model or self.default_model,
                messages=messages,
                tools=tools,
                tool_choice=tool_choice,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"Mistral streaming error: {str(e)}")
            raise

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Estimate cost of API call in USD.

        Args:
            prompt_tokens: Input tokens
            completion_tokens: Output tokens

        Returns:
            Estimated cost in USD
        """
        # Mistral Large pricing (as of 2024)
        # Input: $4 per 1M tokens, Output: $12 per 1M tokens
        input_cost = (prompt_tokens / 1_000_000) * 4.0
        output_cost = (completion_tokens / 1_000_000) * 12.0
        return input_cost + output_cost


# Singleton instance
_mistral_client: Optional[MistralClient] = None


def get_mistral_client() -> MistralClient:
    """Get Mistral client singleton instance."""
    global _mistral_client
    if _mistral_client is None:
        _mistral_client = MistralClient()
    return _mistral_client
