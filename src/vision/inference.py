import base64
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
PREVIEW_MAX_WIDTH = 960


class FloodAnalyzer:
    def __init__(self):
        if not MODEL_PATH.is_file():
            raise FileNotFoundError(
                f"Modelo não encontrado: {MODEL_PATH}"
            )
        self.model = YOLO(str(MODEL_PATH))

    @staticmethod
    def segmentation_mask(result, image_shape):
        """Union of predicted flood polygons in the original image coordinates."""
        height, width = image_shape[:2]
        combined_mask = np.zeros(
            (height, width),
            dtype=np.uint8,
        )

        if result.masks is None:
            return combined_mask

        for polygon in result.masks.xy:
            if len(polygon) < 3:
                continue
            points = polygon.astype(np.int32)
            cv2.fillPoly(combined_mask, [points], 255)

        return combined_mask

    @staticmethod
    def calculate_flooded_area(result, image_shape):
        mask = FloodAnalyzer.segmentation_mask(
            result, image_shape
        )
        height, width = image_shape[:2]
        return (
            cv2.countNonZero(mask) / (height * width)
        ) * 100

    @staticmethod
    def visualization_data_url(image, mask):
        """Visual explanation of model predictions, NOT verified water depth."""
        preview = image.copy()
        selected = mask > 0

        if np.any(selected):
            tint = np.empty_like(image)
            tint[:] = (255, 210, 30)  # BGR: cyan-blue
            blended = cv2.addWeighted(
                image, 0.53, tint, 0.47, 0.0
            )
            preview[selected] = blended[selected]

            contours, _ = cv2.findContours(
                mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            cv2.drawContours(
                preview, contours, -1, (255, 255, 255), 2
            )

        height, width = preview.shape[:2]
        if width > PREVIEW_MAX_WIDTH:
            new_height = max(
                1, round(height * PREVIEW_MAX_WIDTH / width)
            )
            preview = cv2.resize(
                preview,
                (PREVIEW_MAX_WIDTH, new_height),
                interpolation=cv2.INTER_AREA,
            )

        encoded_ok, encoded = cv2.imencode(
            ".jpg",
            preview,
            [cv2.IMWRITE_JPEG_QUALITY, 80],
        )
        if not encoded_ok:
            raise ValueError(
                "Could not encode segmentation preview."
            )

        return (
            "data:image/jpeg;base64,"
            + base64.b64encode(encoded.tobytes()).decode("ascii")
        )

    def analyze(self, image, include_visualization=False):
        if image is None or image.size == 0:
            raise ValueError("Invalid image.")

        result = self.model.predict(
            source=image,
            imgsz=INFERENCE_SIZE,
            conf=CONFIDENCE_THRESHOLD,
            verbose=False,
        )[0]

        mask = self.segmentation_mask(
            result, image.shape
        )
        height, width = image.shape[:2]
        flooded_area = (
            cv2.countNonZero(mask) / (height * width)
        ) * 100

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

        analysis = {
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

        if include_visualization:
            analysis["visualization"] = {
                "image_data_url": self.visualization_data_url(
                    image, mask
                ),
                "has_segmented_pixels": bool(
                    cv2.countNonZero(mask)
                ),
            }

        return analysis
