"""Small independent tests for the demo authentication and request gate."""
import base64
import os
import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.demo_security import (
    DemoSecurityMiddleware,
    MAX_IMAGE_BYTES,
)


def make_app():
    app = FastAPI()
    app.add_middleware(DemoSecurityMiddleware)

    @app.get("/")
    def home():
        return {"ready": True}

    @app.get("/health")
    def health():
        return {"status": "healthy"}

    @app.post("/analyze/image")
    def image():
        return {"ok": True}

    return app


class DemoSecurityTests(unittest.TestCase):
    def test_password_protects_dashboard_but_not_health(self):
        with patch.dict(os.environ, {
            "FLOODLENS_DEMO_REQUIRE_AUTH": "1",
            "FLOODLENS_DEMO_USERNAME": "judge",
            "FLOODLENS_DEMO_PASSWORD": "correct-horse-battery-123",
        }):
            with TestClient(make_app()) as client:
                self.assertEqual(client.get("/").status_code, 401)
                self.assertEqual(client.get("/health").status_code, 200)
                token = base64.b64encode(
                    b"judge:correct-horse-battery-123"
                ).decode()
                response = client.get(
                    "/", headers={"Authorization": "Basic " + token}
                )
                self.assertEqual(response.status_code, 200)

    def test_public_mode_requires_password(self):
        with patch.dict(os.environ, {
            "FLOODLENS_DEMO_REQUIRE_AUTH": "1",
            "FLOODLENS_DEMO_PASSWORD": "",
        }):
            with self.assertRaisesRegex(RuntimeError, "no password"):
                with TestClient(make_app()) as client:
                    client.get("/")

    def test_declared_oversized_upload(self):
        with patch.dict(os.environ, {
            "FLOODLENS_DEMO_REQUIRE_AUTH": "",
            "FLOODLENS_DEMO_PASSWORD": "",
        }):
            with TestClient(make_app()) as client:
                response = client.post(
                    "/analyze/image",
                    headers={"Content-Length": str(MAX_IMAGE_BYTES + 2*1024*1024)},
                    content=b"small",
                )
                self.assertEqual(response.status_code, 413)

    def test_default_local_mode_still_works(self):
        with patch.dict(os.environ, {
            "FLOODLENS_DEMO_REQUIRE_AUTH": "",
            "FLOODLENS_DEMO_PASSWORD": "",
        }):
            with TestClient(make_app()) as client:
                self.assertEqual(client.get("/").status_code, 200)


if __name__ == "__main__":
    unittest.main()
