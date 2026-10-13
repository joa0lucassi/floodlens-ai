
from collections import deque
from pathlib import Path
import math

import cv2

from src.risk.risk_engine import calculate_risk
from src.vision.inference import FloodAnalyzer


SAMPLE_INTERVAL_SECONDS = 1.0
TEMPORAL_WINDOW = 5
MIN_POSITIVE_SAMPLES = 3


class VideoFloodAnalyzer:
    def __init__(self, flood_analyzer: FloodAnalyzer):
        self.flood_analyzer = flood_analyzer

    def analyze_video(
        self,
        video_path: str | Path,
        sample_interval_seconds: float = SAMPLE_INTERVAL_SECONDS,
    ):
        if (
            not math.isfinite(sample_interval_seconds)
            or sample_interval_seconds <= 0
        ):
            raise ValueError(
                "Sample interval must be positive and finite."
            )

        video = cv2.VideoCapture(str(video_path))

        if not video.isOpened():
            raise ValueError(
                "Could not open the uploaded video."
            )

        fps = video.get(cv2.CAP_PROP_FPS)
        total_frames = int(
            video.get(cv2.CAP_PROP_FRAME_COUNT)
        )

        if fps <= 0 or total_frames <= 0:
            video.release()
            raise ValueError(
                "Invalid video FPS or frame count."
            )

        duration_seconds = total_frames / fps

        window = deque(maxlen=TEMPORAL_WINDOW)
        records = []
        timeline = []

        current_time = 0.0

        try:
            while current_time < duration_seconds:
                video.set(
                    cv2.CAP_PROP_POS_MSEC,
                    current_time * 1000,
                )

                success, frame = video.read()

                if not success:
                    break

                analysis = self.flood_analyzer.analyze(
                    frame
                )

                raw_positive = bool(
                    analysis["flood_detected"]
                )

                window.append(raw_positive)

                window_ready = (
                    len(window) == TEMPORAL_WINDOW
                )

                positive_count = sum(window)

                confirmed = (
                    window_ready
                    and positive_count >= MIN_POSITIVE_SAMPLES
                )

                record = {
                    "time_seconds": round(
                        current_time, 3
                    ),
                    "flooded_area": analysis[
                        "flooded_area_percent"
                    ],
                    "detections": analysis["detections"],
                    "max_confidence": analysis[
                        "max_confidence"
                    ],
                }

                records.append(record)

                timeline.append({
                    "time_seconds": record[
                        "time_seconds"
                    ],
                    "flooded_area_percent": record[
                        "flooded_area"
                    ],
                    "detections": record["detections"],
                    "max_confidence": record[
                        "max_confidence"
                    ],
                    "raw_positive": raw_positive,
                    "positive_samples_in_window": positive_count,
                    "window_size": len(window),
                    "confirmed": confirmed,
                })

                current_time += sample_interval_seconds

        finally:
            video.release()

        if not records:
            raise ValueError(
                "No frames could be analyzed."
            )

        samples_analyzed = len(records)

        raw_positive_samples = sum(
            item["raw_positive"]
            for item in timeline
        )

        confirmed_windows = sum(
            item["confirmed"]
            for item in timeline
        )

        first_confirmation_seconds = next(
            (
                item["time_seconds"]
                for item in timeline
                if item["confirmed"]
            ),
            None,
        )

        enough_data = (
            samples_analyzed >= TEMPORAL_WINDOW
        )

        flood_confirmed = (
            confirmed_windows > 0
        )

        if not enough_data:
            status = "INSUFFICIENT_DATA"
            flood_detected = None
        elif flood_confirmed:
            status = "CONFIRMED"
            flood_detected = True
        else:
            status = "NOT_CONFIRMED"
            flood_detected = False

        # Existing heuristic risk engine.
        # Area and trend remain raw visual estimates.
        risk = calculate_risk(records)

        # Do not present a numerical flood-risk score
        # when the temporal rule has not confirmed flood.
        if not flood_confirmed:
            risk["risk_level"] = "NOT_ASSESSED"
            risk["risk_score"] = None
            risk["reliability"] = "NOT_APPLICABLE"

        risk["temporal_confirmed"] = flood_confirmed
        risk["assessment_status"] = status

        temporal = {
            "status": status,
            "flood_detected": flood_detected,
            "window_size": TEMPORAL_WINDOW,
            "min_positive_samples": MIN_POSITIVE_SAMPLES,
            "raw_positive_samples": raw_positive_samples,
            "confirmed_windows": confirmed_windows,
            "first_confirmation_seconds": first_confirmation_seconds,
        }

        return {
            "flood_detected": flood_detected,
            "video": {
                "fps": round(fps, 2),
                "total_frames": total_frames,
                "duration_seconds": round(
                    duration_seconds, 2
                ),
                "sample_interval_seconds": sample_interval_seconds,
                "samples_analyzed": samples_analyzed,
            },
            "temporal": temporal,
            "risk": risk,
            "timeline": timeline,
        }
