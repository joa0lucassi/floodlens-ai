from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO


PROJECT_ROOT = Path(__file__).resolve().parents[2]

MODEL_PATH = (
    PROJECT_ROOT
    / "models"
    / "flood_segmentation"
    / "best.pt"
)

CONFIDENCE_THRESHOLD = 0.25
INFERENCE_SIZE = 960


class FloodAnalyzer:
    def __init__(self):
        if not MODEL_PATH.is_file():
            raise FileNotFoundError(
                f"Modelo não encontrado: {MODEL_PATH}"
            )

        self.model = YOLO(str(MODEL_PATH))

    @staticmethod
    def calculate_flooded_area(result, image_shape):
        height, width = image_shape[:2]

        combined_mask = np.zeros(
            (height, width),
            dtype=np.uint8,
        )

        if result.masks is None:
            return 0.0

        for polygon in result.masks.xy:
            if len(polygon) < 3:
                continue

            points = polygon.astype(np.int32)

            cv2.fillPoly(
                combined_mask,
                [points],
                255,
            )

        flooded_pixels = cv2.countNonZero(
            combined_mask
        )

        total_pixels = height * width

        return (
            flooded_pixels / total_pixels
        ) * 100

    def analyze(self, image):
        if image is None or image.size == 0:
            raise ValueError("Invalid image.")

        result = self.model.predict(
            source=image,
            imgsz=INFERENCE_SIZE,
            conf=CONFIDENCE_THRESHOLD,
            verbose=False,
        )[0]

        flooded_area = self.calculate_flooded_area(
            result,
            image.shape,
        )

        detection_count = 0
        max_confidence = 0.0

        if (
            result.boxes is not None
            and len(result.boxes) > 0
        ):
            detection_count = len(result.boxes)

            max_confidence = float(
                result.boxes.conf.max().item()
            )

        return {
            "flood_detected": detection_count > 0,
            "flooded_area_percent": round(
                flooded_area, 2
            ),
            "detections": detection_count,
            "max_confidence": round(
                max_confidence, 2
            ),
            "image_width": image.shape[1],
            "image_height": image.shape[0],
        }