"""Security/API integration tests: synthetic media, stub inference, no weights."""
import asyncio
import base64
import importlib
import io
import os
from pathlib import Path
import sys
import tempfile
import threading
import types
import unittest
from unittest.mock import patch

import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile
from fastapi.testclient import TestClient
from PIL import Image
from src.api.demo_security import DemoSecurityMiddleware, MAX_IMAGE_BYTES

SECRET = 'test-only-password-not-for-deployment'
ENV = {'FLOODLENS_DEMO_REQUIRE_AUTH': '1', 'FLOODLENS_DEMO_PASSWORD': SECRET,
       'FLOODLENS_DEMO_REQUIRE_HTTPS': '1', 'FLOODLENS_S3_BUCKET': 'must-not-be-used'}


class Gates(unittest.TestCase):
    def make(self):
        app = FastAPI()
        app.add_middleware(DemoSecurityMiddleware)
        @app.post('/analyze/image')
        async def upload(file: UploadFile = File(...)):
            return {'bytes': len(await file.read())}
        @app.get('/')
        def home():
            return {'ok': True}
        return app

    def test_unicode_credentials_do_not_crash(self):
        with patch.dict(os.environ, ENV), TestClient(self.make(), base_url='https://testserver') as c:
            token = base64.b64encode('juíz:sênha'.encode()).decode()
            self.assertEqual(c.get('/', headers={'Authorization': 'Basic '+token}).status_code, 401)

    def test_http_rejected_even_with_spoofed_forwarded_header(self):
        with patch.dict(os.environ, ENV), TestClient(self.make()) as c:
            self.assertEqual(c.get('/', headers={'X-Forwarded-Proto': 'https'}, auth=('judge',SECRET)).status_code,403)

    def test_stream_without_content_length_is_bounded(self):
        with patch.dict(os.environ, ENV), TestClient(self.make(), base_url='https://testserver') as c:
            def body():
                yield b'--x\r\nContent-Disposition: form-data; name="file"; filename="x.png"\r\n\r\n'
                for _ in range(10):
                    yield b'x' * (1024*1024)
                yield b'\r\n--x--\r\n'
            r=c.post('/analyze/image',content=body(),headers={'Content-Type':'multipart/form-data; boundary=x'},auth=('judge',SECRET))
            self.assertEqual(r.status_code,413)

    def test_cross_origin_form_upload_rejected(self):
        with patch.dict(os.environ, ENV), TestClient(self.make(), base_url='https://testserver') as c:
            response=c.post('/analyze/image',headers={'Origin':'https://other.example'},auth=('judge',SECRET))
            self.assertEqual(response.status_code,403)

    def test_rate_limit(self):
        with patch.dict(os.environ, ENV), TestClient(self.make(), base_url='https://testserver') as c:
            for _ in range(60):
                self.assertEqual(c.get('/').status_code,401)
            self.assertEqual(c.get('/').status_code,429)

    def test_concurrent_analysis_rejected_and_gate_released(self):
        entered=threading.Event(); release=threading.Event()
        app=self.make()
        @app.post('/analyze/video')
        def slow():
            entered.set(); release.wait(5); return {'ok':True}
        with patch.dict(os.environ, ENV), TestClient(app,base_url='https://testserver') as c:
            t=threading.Thread(target=lambda:c.post('/analyze/video',auth=('judge',SECRET)))
            t.start()
            try:
                self.assertTrue(entered.wait(3))
                self.assertEqual(c.post('/analyze/video',auth=('judge',SECRET)).status_code,503)
            finally:
                release.set();t.join(5)
            self.assertEqual(c.post('/analyze/video',auth=('judge',SECRET)).status_code,200)


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Only the model constructor is stubbed. Decoding, temporal logic,
        # endpoint handling and preview encoding remain real.
        fake=types.ModuleType('ultralytics');fake.YOLO=lambda _:None
        cls.modules=patch.dict(sys.modules,{'ultralytics':fake});cls.modules.start()
        cls.addClassCleanup(cls.modules.stop)
        inference=importlib.import_module('src.vision.inference')
        cls.inference=inference
        def analyze(self,image,include_visualization=False):
            result={'flood_detected':False,'flooded_area_percent':0.0,'detections':0,'max_confidence':0.0}
            if include_visualization:
                result['visualization']={'image_data_url':inference.FloodAnalyzer.visualization_data_url(image,np.zeros(image.shape[:2],np.uint8)), 'has_segmented_pixels':False}
            return result
        cls.env=patch.dict(os.environ,ENV);cls.env.start();cls.addClassCleanup(cls.env.stop)
        cls.init=patch.object(inference.FloodAnalyzer,'__init__',lambda self:None);cls.init.start()
        cls.analyze=patch.object(inference.FloodAnalyzer,'analyze',analyze);cls.analyze.start()
        cls.main=importlib.import_module('src.api.main')

    @classmethod
    def tearDownClass(cls):
        cls.analyze.stop();cls.init.stop();cls.env.stop()

    def setUp(self):
        self.client=TestClient(self.main.app,base_url='https://testserver')
        self.client.auth=('judge',SECRET)

    def test_dashboard_and_history_protection(self):
        self.assertIn('See beyond the surface',self.client.get('/').text)
        self.assertEqual(self.client.get('/analyses/history').status_code,403)
        self.assertEqual(self.client.get('/risk/latest').status_code,403)
        self.assertFalse(self.main.storage.enabled)

    def test_password_only_configuration_denies_shared_history(self):
        with patch.dict(os.environ, {'FLOODLENS_DEMO_REQUIRE_AUTH': ''}):
            self.assertEqual(self.client.get('/analyses/history').status_code, 403)
            self.assertEqual(self.client.get('/risk/latest').status_code, 403)

    def test_image_response_and_preview(self):
        b=io.BytesIO();Image.new('RGB',(32,32)).save(b,format='PNG')
        r=self.client.post('/analyze/image?include_visualization=true',files={'file':('owned.png',b.getvalue(),'image/png')})
        self.assertEqual(r.status_code,200,r.text)
        self.assertTrue(r.json()['visualization']['image_data_url'].startswith('data:image/jpeg;base64,'))
        self.assertEqual(r.headers['cache-control'],'no-store')

    def test_empty_image_is_client_error(self):
        self.assertEqual(self.client.post('/analyze/image',files={'file':('empty.png',b'','image/png')}).status_code,400)

    def test_video_temporal_and_temp_cleanup(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'owned.avi'
            w=cv2.VideoWriter(str(path),cv2.VideoWriter_fourcc(*'MJPG'),10,(32,32))
            self.assertTrue(w.isOpened())
            for _ in range(60):w.write(np.zeros((32,32,3),np.uint8))
            w.release()
            original=self.main.video_analyzer.analyze_video
            seen=[]
            def record(path,**kwargs):seen.append(path);return original(path,**kwargs)
            with patch.object(self.main.video_analyzer,'analyze_video',side_effect=record):
                r=self.client.post('/analyze/video?include_visualization=true',files={'file':('owned.avi',path.read_bytes(),'video/x-msvideo')})
            self.assertEqual(r.status_code,200,r.text)
            self.assertEqual(r.json()['temporal']['status'],'NOT_CONFIRMED')
            self.assertEqual(r.json()['temporal']['window_size'],5)
            self.assertEqual(r.json()['temporal']['min_positive_samples'],3)
            self.assertTrue(seen);self.assertFalse(seen[0].exists())

    def test_video_duration_rejected_and_capture_released(self):
        from unittest.mock import MagicMock
        capture=MagicMock()
        capture.isOpened.return_value=True
        capture.get.side_effect=lambda key: {cv2.CAP_PROP_FPS:10,cv2.CAP_PROP_FRAME_COUNT:610,cv2.CAP_PROP_FRAME_WIDTH:32,cv2.CAP_PROP_FRAME_HEIGHT:32}[key]
        with patch('src.vision.video_inference.cv2.VideoCapture',return_value=capture):
            with self.assertRaisesRegex(ValueError,'exceeds 60'):
                self.main.video_analyzer.analyze_video('synthetic.avi',max_duration_seconds=60)
        capture.release.assert_called_once()
        capture.read.assert_not_called()

    def test_nonfinite_video_metadata_rejected(self):
        from unittest.mock import MagicMock
        capture=MagicMock();capture.isOpened.return_value=True
        capture.get.return_value=float('nan')
        with patch('src.vision.video_inference.cv2.VideoCapture',return_value=capture):
            with self.assertRaisesRegex(ValueError,'metadata'):
                self.main.video_analyzer.analyze_video('synthetic.avi',max_duration_seconds=60)
        capture.release.assert_called_once()

    def test_image_resolution_checked_before_opencv_decode(self):
        b=io.BytesIO();Image.new('RGB',(4001,4000)).save(b,format='PNG')
        with patch.object(self.main.cv2,'imdecode') as decode:
            response=self.client.post('/analyze/image',files={'file':('large.png',b.getvalue(),'image/png')})
        self.assertEqual(response.status_code,413)
        decode.assert_not_called()

    def test_official_parameters(self):
        self.assertEqual(self.inference.INFERENCE_SIZE,960)
        self.assertEqual(self.inference.CONFIDENCE_THRESHOLD,0.25)
