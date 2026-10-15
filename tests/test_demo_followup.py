"""Regression coverage for slow uploads and password-only demo privacy."""
import asyncio
import os
import unittest
from unittest.mock import patch

from fastapi import FastAPI, File, UploadFile
from src.api.demo_security import DemoSecurityMiddleware
from src.storage.s3_storage import S3Storage


class FollowupTests(unittest.TestCase):
    def test_password_alone_disables_s3_without_creating_client(self):
        with patch.dict(os.environ, {
            'FLOODLENS_DEMO_PASSWORD': 'test-password-with-enough-length',
            'FLOODLENS_DEMO_REQUIRE_AUTH': '',
            'FLOODLENS_S3_BUCKET': 'must-never-be-contacted',
        }), patch('src.storage.s3_storage.boto3.client') as client:
            self.assertFalse(S3Storage().enabled)
            client.assert_not_called()

    def test_stalled_multipart_returns_408_and_releases_admission(self):
        async def run():
            app = FastAPI()
            @app.post('/analyze/image')
            async def upload(file: UploadFile = File(...)):
                return {'size': len(await file.read())}
            middleware = DemoSecurityMiddleware(app)
            scope = {'type': 'http', 'asgi': {'version': '3.0'},
                     'http_version': '1.1', 'method': 'POST', 'scheme': 'http',
                     'path': '/analyze/image', 'raw_path': b'/analyze/image',
                     'query_string': b'', 'root_path': '',
                     'headers': [(b'content-type', b'multipart/form-data; boundary=x')],
                     'client': ('127.0.0.1', 1), 'server': ('localhost', 80)}
            sent = []
            async def send(message):
                sent.append(message)
            async def receive():
                await asyncio.sleep(1)
                return {'type': 'http.request', 'body': b'', 'more_body': False}
            with patch('src.api.demo_security.MAX_UPLOAD_SECONDS', 0.01):
                await middleware(scope, receive, send)
            self.assertEqual(sent[0]['status'], 408)
            self.assertFalse(middleware.busy)
        with patch.dict(os.environ, {'FLOODLENS_DEMO_PASSWORD': '',
                                     'FLOODLENS_DEMO_REQUIRE_AUTH': '',
                                     'FLOODLENS_DEMO_REQUIRE_HTTPS': ''}):
            asyncio.run(run())
