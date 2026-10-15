"""Small-scope safeguards for a temporary, HTTPS-only judge demo.

This is not a substitute for edge rate limits, concurrency controls, or
AWS/network security configuration.
"""
import base64
import binascii
import os
import secrets

from starlette.responses import PlainTextResponse


MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_VIDEO_BYTES = 48 * 1024 * 1024
MAX_IMAGE_PIXELS = 16_000_000
MAX_VIDEO_SECONDS = 60.0


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

    def _authorized(self, authorization):
        if not authorization.startswith(b"Basic "):
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
            and secrets.compare_digest(username, self.username)
            and secrets.compare_digest(password, self.password)
        )

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        headers = dict(scope.get("headers", []))

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

        await self.app(scope, receive, send)
