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
    version="0.3.0",
)


flood_analyzer = FloodAnalyzer()

video_analyzer = VideoFloodAnalyzer(
    flood_analyzer
)


@app.get("/")
def root():
    return {
        "name": "FloodLens AI",
        "status": "running",
        "version": "0.3.0",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "model_loaded": True,
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

    return {
        "filename": file.filename,
        **analysis,
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