from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO


MODEL_PATH = Path(
    "models/flood_segmentation/best.pt"
)

CONFIDENCE_THRESHOLD = 0.25

# Experimento:
# remove componentes segmentados muito pequenos.
MIN_COMPONENT_AREA_PERCENT = 0.50

# ROI genérica experimental.
# Mantém uma área ampla da região inferior da cena,
# onde normalmente está a via.
ROI_TOP_Y_RATIO = 0.20
ROI_TOP_LEFT_X_RATIO = 0.05
ROI_TOP_RIGHT_X_RATIO = 0.95


class SpatialFloodAnalyzer:
    def __init__(self):
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Modelo não encontrado em: {MODEL_PATH}"
            )

        self.model = YOLO(
            str(MODEL_PATH)
        )

    @staticmethod
    def create_roi_mask(image_shape):
        height, width = image_shape[:2]

        roi_mask = np.zeros(
            (height, width),
            dtype=np.uint8
        )

        points = np.array(
            [
                [
                    int(
                        width
                        * ROI_TOP_LEFT_X_RATIO
                    ),
                    int(
                        height
                        * ROI_TOP_Y_RATIO
                    ),
                ],
                [
                    int(
                        width
                        * ROI_TOP_RIGHT_X_RATIO
                    ),
                    int(
                        height
                        * ROI_TOP_Y_RATIO
                    ),
                ],
                [
                    width - 1,
                    height - 1,
                ],
                [
                    0,
                    height - 1,
                ],
            ],
            dtype=np.int32,
        )

        cv2.fillPoly(
            roi_mask,
            [points],
            255,
        )

        return roi_mask

    @staticmethod
    def create_raw_flood_mask(
        result,
        image_shape,
    ):
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

            points = polygon.astype(
                np.int32
            )

            cv2.fillPoly(
                combined_mask,
                [points],
                255,
            )

        return combined_mask

    @staticmethod
    def remove_small_components(
        mask,
        image_shape,
    ):
        height, width = image_shape[:2]

        total_pixels = height * width

        minimum_pixels = int(
            total_pixels
            * (
                MIN_COMPONENT_AREA_PERCENT
                / 100
            )
        )

        number_labels, labels, stats, _ = (
            cv2.connectedComponentsWithStats(
                mask,
                connectivity=8,
            )
        )

        filtered_mask = np.zeros_like(
            mask
        )

        kept_components = 0
        removed_components = 0

        for label_index in range(
            1,
            number_labels,
        ):
            component_area = stats[
                label_index,
                cv2.CC_STAT_AREA,
            ]

            if component_area >= minimum_pixels:
                filtered_mask[
                    labels == label_index
                ] = 255

                kept_components += 1

            else:
                removed_components += 1

        return (
            filtered_mask,
            kept_components,
            removed_components,
        )

    @staticmethod
    def calculate_area_percent(
        mask,
        reference_mask=None,
    ):
        if reference_mask is None:
            total_pixels = mask.size

        else:
            total_pixels = cv2.countNonZero(
                reference_mask
            )

        if total_pixels == 0:
            return 0.0

        flooded_pixels = cv2.countNonZero(
            mask
        )

        return (
            flooded_pixels
            / total_pixels
        ) * 100

    def analyze(self, image):
        results = self.model.predict(
            source=image,
            imgsz=640,
            conf=CONFIDENCE_THRESHOLD,
            verbose=False,
        )

        result = results[0]

        raw_mask = (
            self.create_raw_flood_mask(
                result,
                image.shape,
            )
        )

        raw_area_percent = (
            self.calculate_area_percent(
                raw_mask
            )
        )

        roi_mask = (
            self.create_roi_mask(
                image.shape
            )
        )

        roi_flood_mask = cv2.bitwise_and(
            raw_mask,
            roi_mask,
        )

        (
            filtered_mask,
            kept_components,
            removed_components,
        ) = self.remove_small_components(
            roi_flood_mask,
            image.shape,
        )

        filtered_area_percent = (
            self.calculate_area_percent(
                filtered_mask
            )
        )

        roi_area_percent = (
            self.calculate_area_percent(
                filtered_mask,
                roi_mask,
            )
        )

        raw_detection_count = 0
        max_confidence = 0.0

        if (
            result.boxes is not None
            and len(result.boxes) > 0
        ):
            raw_detection_count = len(
                result.boxes
            )

            confidences = (
                result.boxes.conf
                .cpu()
                .numpy()
            )

            max_confidence = float(
                np.max(confidences)
            )

        flood_detected = (
            kept_components > 0
        )

        return {
            "flood_detected": (
                flood_detected
            ),

            "raw_flood_detected": (
                raw_detection_count > 0
            ),

            "raw_flooded_area_percent": round(
                raw_area_percent,
                2,
            ),

            "filtered_flooded_area_percent": round(
                filtered_area_percent,
                2,
            ),

            "roi_flooded_area_percent": round(
                roi_area_percent,
                2,
            ),

            "raw_detections": (
                raw_detection_count
            ),

            "kept_components": (
                kept_components
            ),

            "removed_components": (
                removed_components
            ),

            "max_confidence": round(
                max_confidence,
                2,
            ),

            "image_width": image.shape[1],
            "image_height": image.shape[0],
        }