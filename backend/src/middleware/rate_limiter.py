"""Rate limiting middleware for API endpoints."""

import time
from collections import defaultdict
from typing import Callable, Dict

from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimiter:
    """In-memory rate limiter with sliding window."""

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        """
        Initialize rate limiter.

        Args:
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, key: str) -> tuple[bool, int]:
        """
        Check if request is allowed under rate limit.

        Args:
            key: Identifier for rate limiting (e.g., user_id or IP)

        Returns:
            (allowed, remaining_requests)
        """
        now = time.time()
        request_times = self.requests[key]

        # Remove requests outside the window
        cutoff = now - self.window_seconds
        request_times[:] = [t for t in request_times if t > cutoff]

        # Check if under limit
        if len(request_times) < self.max_requests:
            request_times.append(now)
            return True, self.max_requests - len(request_times)

        return False, 0


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting."""

    def __init__(
        self,
        app,
        max_requests: int = 100,
        window_seconds: int = 60,
    ) -> None:
        """
        Initialize rate limit middleware.

        Args:
            app: FastAPI app
            max_requests: Max requests per window (default 100)
            window_seconds: Window size in seconds (default 60)
        """
        super().__init__(app)
        self.limiter = RateLimiter(max_requests, window_seconds)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with rate limiting.

        Args:
            request: Incoming request
            call_next: Next middleware/route handler

        Returns:
            Response
        """
        # Skip rate limiting for health check
        if request.url.path == "/health":
            return await call_next(request)

        # Get user ID from auth or fall back to IP
        user_id = request.state.user_id if hasattr(request.state, "user_id") else None
        rate_limit_key = user_id if user_id else request.client.host

        # Check rate limit
        allowed, remaining = self.limiter.is_allowed(rate_limit_key)

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Maximum {self.limiter.max_requests} requests per {self.limiter.window_seconds} seconds",
                },
                headers={
                    "X-RateLimit-Limit": str(self.limiter.max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time() + self.limiter.window_seconds)),
                },
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.limiter.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response
