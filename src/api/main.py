import json
import shutil
import tempfile
from pathlib import Path

import cv2
import numpy as np

from fastapi import (
    FastAPI,
    File,
    HTTPException,
    UploadFile,
)

from src.storage.s3_storage import (
    S3Storage,
)

from src.vision.inference import (
    FloodAnalyzer,
)

from src.vision.video_inference import (
    VideoFloodAnalyzer,
)


RISK_ASSESSMENT_PATH = Path(
    "data/temporal_analysis/"
    "risk_assessment.json"
)


app = FastAPI(
    title="FloodLens AI API",
    description=(
        "API for urban flood monitoring "
        "using computer vision and AI."
    ),
    version="0.4.0",
)


flood_analyzer = FloodAnalyzer()

video_analyzer = VideoFloodAnalyzer(
    flood_analyzer
)

storage = S3Storage()


@app.get("/")
def root():
    return {
        "name": "FloodLens AI",
        "status": "running",
        "version": "0.4.0",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "model_loaded": True,
        "s3_enabled": storage.enabled,
    }


@app.get("/risk/latest")
def latest_risk():
    if not RISK_ASSESSMENT_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                "Risk assessment not found. "
                "Run the temporal analyzer "
                "and risk engine first."
            ),
        )

    try:
        with open(
            RISK_ASSESSMENT_PATH,
            "r",
            encoding="utf-8",
        ) as file:
            assessment = json.load(
                file
            )

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail=(
                "Invalid risk assessment file."
            ),
        )

    return assessment


@app.post("/analyze/image")
async def analyze_image(
    file: UploadFile = File(...)
):
    allowed_types = {
        "image/jpeg",
        "image/png",
        "image/webp",
    }

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported image type. "
                "Use JPEG, PNG or WebP."
            ),
        )

    image_bytes = await file.read()

    numpy_buffer = np.frombuffer(
        image_bytes,
        dtype=np.uint8
    )

    image = cv2.imdecode(
        numpy_buffer,
        cv2.IMREAD_COLOR
    )

    if image is None:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file.",
        )

    analysis = flood_analyzer.analyze(
        image
    )

    analysis_id = (
        storage.create_analysis_id()
    )

    response = {
        "analysis_id": analysis_id,
        "filename": file.filename,
        **analysis,
    }

    storage_result = {
        "enabled": storage.enabled,
        "saved": False,
        "bucket": (
            storage.bucket_name
            if storage.enabled
            else None
        ),
        "image_key": None,
        "result_key": None,
    }

    if storage.enabled:
        try:
            image_key = storage.build_key(
                category="uploads/images",
                analysis_id=analysis_id,
                filename=(
                    file.filename
                    or "image"
                ),
            )

            result_key = storage.build_key(
                category="results/images",
                analysis_id=analysis_id,
                filename="analysis.json",
            )

            storage.upload_bytes(
                data=image_bytes,
                key=image_key,
                content_type=(
                    file.content_type
                    or "application/octet-stream"
                ),
            )

            result_document = {
                **response,
                "storage": {
                    "image_key": image_key,
                },
            }

            storage.upload_json(
                data=result_document,
                key=result_key,
            )

            storage_result.update(
                {
                    "saved": True,
                    "image_key": image_key,
                    "result_key": result_key,
                }
            )

        except RuntimeError as error:
            storage_result[
                "error"
            ] = str(error)

    return {
        **response,
        "storage": storage_result,
    }


@app.post("/analyze/video")
def analyze_video(
    file: UploadFile = File(...)
):
    allowed_types = {
        "video/mp4",
        "video/quicktime",
        "video/x-msvideo",
    }

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported video type. "
                "Use MP4, MOV or AVI."
            ),
        )

    original_name = (
        file.filename
        or "uploaded_video.mp4"
    )

    suffix = Path(
        original_name
    ).suffix

    if not suffix:
        suffix = ".mp4"

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
        ) as temporary_file:

            shutil.copyfileobj(
                file.file,
                temporary_file,
            )

            temp_path = Path(
                temporary_file.name
            )

        analysis = (
            video_analyzer
            .analyze_video(
                temp_path
            )
        )

        return {
            "filename": original_name,
            **analysis,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    finally:
        if (
            temp_path is not None
            and temp_path.exists()
        ):
            temp_path.unlink()