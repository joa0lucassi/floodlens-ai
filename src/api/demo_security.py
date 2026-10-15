"""Small-scope safeguards for a temporary, HTTPS-only judge demo.

This is not a substitute for edge rate limits, concurrency controls, or
AWS/network security configuration.
"""
import asyncio
import base64
import binascii
import os
import secrets
import time
from collections import deque
from urllib.parse import urlsplit

from starlette.exceptions import HTTPException

from starlette.responses import PlainTextResponse


MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_VIDEO_BYTES = 48 * 1024 * 1024
MAX_IMAGE_PIXELS = 16_000_000
MAX_VIDEO_SECONDS = 60.0
MAX_UPLOAD_SECONDS = 60.0


def private_demo_enabled():
    """Use the same privacy policy for every authenticated demo configuration."""
    return bool(os.getenv("FLOODLENS_DEMO_PASSWORD")) or os.getenv("FLOODLENS_DEMO_REQUIRE_AUTH") == "1"


class DemoSecurityMiddleware:
    """Protect browser and API with HTTP Basic when configured.

    Set FLOODLENS_DEMO_REQUIRE_AUTH=1 in the public ECS task and provide
    FLOODLENS_DEMO_PASSWORD from AWS Secrets Manager (never commit it).
    Without these settings, the existing localhost workflow is preserved.
    """

    def __init__(self, app):
        self.app = app
        self.username = os.getenv("FLOODLENS_DEMO_USERNAME", "judge")
        self.password = os.getenv("FLOODLENS_DEMO_PASSWORD", "")
        required = os.getenv("FLOODLENS_DEMO_REQUIRE_AUTH", "") == "1"
        if required and not self.password:
            raise RuntimeError(
                "Demo authentication is required but no password is configured."
            )
        if self.password and len(self.password) < 16:
            raise RuntimeError(
                "FLOODLENS_DEMO_PASSWORD must contain at least 16 characters."
            )
        self.protected = bool(self.password)
        self.require_https = os.getenv("FLOODLENS_DEMO_REQUIRE_HTTPS", "") == "1"
        if self.require_https and not self.protected:
            raise RuntimeError("HTTPS demo mode requires authentication.")
        self.attempts = deque()
        self.analyses = deque()
        self.busy = False

    def _authorized(self, authorization):
        if authorization[:6].lower() != b"basic ":
            return False
        try:
            decoded = base64.b64decode(
                authorization[6:], validate=True
            ).decode("utf-8")
            username, separator, password = decoded.partition(":")
        except (binascii.Error, UnicodeDecodeError, ValueError):
            return False
        return (
            bool(separator)
            and secrets.compare_digest(username.encode("utf-8"), self.username.encode("utf-8"))
            and secrets.compare_digest(password.encode("utf-8"), self.password.encode("utf-8"))
        )

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        headers = dict(scope.get("headers", []))

        async def reject(status, message):
            await PlainTextResponse(message, status_code=status)(scope, receive, send)

        # Trust only ASGI scheme; Uvicorn must trust only the local TLS proxy.
        if self.require_https and path != "/health" and scope.get("scheme") != "https":
            await reject(403, "HTTPS required.")
            return

        now = time.monotonic()
        for queue in (self.attempts, self.analyses):
            while queue and queue[0] <= now - 60:
                queue.popleft()
        if self.protected and path != "/health":
            if len(self.attempts) >= 60:
                await reject(429, "Request limit reached. Retry in one minute.")
                return
            self.attempts.append(now)

        # Keep a minimal health endpoint for ECS health checks.
        # No personal info or credentials should ever be returned here.
        if (
            self.protected
            and path != "/health"
            and not self._authorized(headers.get(b"authorization", b""))
        ):
            response = PlainTextResponse(
                "Authentication required.",
                status_code=401,
                headers={"WWW-Authenticate": 'Basic realm="FloodLens AI"'},
            )
            await response(scope, receive, send)
            return

        if self.protected and scope.get("method") == "POST":
            origin = headers.get(b"origin")
            if origin is not None:
                try:
                    parsed = urlsplit(origin.decode("ascii"))
                    same_origin = (
                        parsed.scheme == scope.get("scheme")
                        and parsed.netloc.encode("ascii") == headers.get(b"host")
                    )
                except (ValueError, UnicodeError):
                    same_origin = False
                if not same_origin:
                    await reject(403, "Cross-origin uploads are not allowed.")
                    return

        # Reject advertised oversized uploads before multipart parsing.
        # Actual uploaded file size is ALSO checked by each endpoint.
        limits = {
            "/analyze/image": MAX_IMAGE_BYTES,
            "/analyze/video": MAX_VIDEO_BYTES,
        }
        if scope.get("method") == "POST" and path in limits:
            declared = headers.get(b"content-length")
            if declared is not None:
                try:
                    length = int(declared)
                    if length < 0:
                        raise ValueError("negative Content-Length")
                except ValueError:
                    response = PlainTextResponse(
                        "Invalid Content-Length.", status_code=400
                    )
                    await response(scope, receive, send)
                    return
                # Reserve room for multipart boundaries and metadata.
                if length > limits[path] + 1024 * 1024:
                    response = PlainTextResponse(
                        "Upload too large.", status_code=413
                    )
                    await response(scope, receive, send)
                    return

        # Count bytes at ASGI receive, before multipart can spool to disk.
        # Include slash aliases, since the router may redirect those paths.
        upload_limit = limits.get(path.rstrip("/"))
        is_analysis = scope.get("method") == "POST" and upload_limit is not None
        if is_analysis:
            if self.busy:
                await reject(503, "An analysis is running. Please retry later.")
                return
            if len(self.analyses) >= 6:
                await reject(429, "Analysis limit reached. Retry in one minute.")
                return
            self.analyses.append(now)
            self.busy = True
        received = 0
        upload_started = time.monotonic()

        async def bounded_receive():
            nonlocal received
            if is_analysis:
                remaining = MAX_UPLOAD_SECONDS - (time.monotonic() - upload_started)
                if remaining <= 0:
                    raise HTTPException(408, "Upload deadline exceeded.")
                try:
                    message = await asyncio.wait_for(receive(), timeout=remaining)
                except TimeoutError:
                    raise HTTPException(408, "Upload deadline exceeded.") from None
            else:
                message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                limit = (upload_limit or MAX_IMAGE_BYTES) + 1024 * 1024
                if received > limit:
                    # Starlette closes multipart temporary files on HTTPException.
                    raise HTTPException(413, "Upload too large.")
            return message

        async def safe_send(message):
            if message["type"] == "http.response.start":
                message["headers"] = list(message.get("headers", [])) + [
                    (b"cache-control", b"no-store"),
                    (b"x-content-type-options", b"nosniff"),
                    (b"x-frame-options", b"DENY"),
                    (b"referrer-policy", b"no-referrer"),
                ]
            await send(message)

        try:
            await self.app(scope, bounded_receive, safe_send)
        finally:
            if is_analysis:
                self.busy = False
