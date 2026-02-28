"""Error handling middleware for consistent error responses."""

import logging
import traceback
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Global error handler for FastAPI."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with error handling.

        Args:
            request: Incoming request
            call_next: Next middleware/route handler

        Returns:
            Response
        """
        try:
            response = await call_next(request)
            return response

        except ValueError as e:
            # Validation errors (400)
            logger.warning(f"Validation error: {str(e)}")
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Validation Error",
                    "message": str(e),
                    "type": "validation_error",
                },
            )

        except PermissionError as e:
            # Permission/authorization errors (403)
            logger.warning(f"Permission denied: {str(e)}")
            return JSONResponse(
                status_code=403,
                content={
                    "error": "Permission Denied",
                    "message": str(e),
                    "type": "permission_error",
                },
            )

        except FileNotFoundError as e:
            # Not found errors (404)
            logger.info(f"Resource not found: {str(e)}")
            return JSONResponse(
                status_code=404,
                content={
                    "error": "Not Found",
                    "message": str(e),
                    "type": "not_found_error",
                },
            )

        except TimeoutError as e:
            # Timeout errors (504)
            logger.error(f"Request timeout: {str(e)}")
            return JSONResponse(
                status_code=504,
                content={
                    "error": "Timeout",
                    "message": "Request timed out. Please try again.",
                    "type": "timeout_error",
                },
            )

        except ConnectionError as e:
            # External service errors (502)
            logger.error(f"Connection error: {str(e)}")
            return JSONResponse(
                status_code=502,
                content={
                    "error": "Service Unavailable",
                    "message": "Unable to connect to external service. Please try again later.",
                    "type": "connection_error",
                },
            )

        except Exception as e:
            # Unexpected errors (500)
            logger.error(f"Unhandled exception: {str(e)}\n{traceback.format_exc()}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "message": "An unexpected error occurred. Please try again later.",
                    "type": "internal_error",
                    # Include error details in development
                    "details": str(e) if logger.level <= logging.DEBUG else None,
                },
            )
