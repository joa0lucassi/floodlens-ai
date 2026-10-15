
from collections import deque
from pathlib import Path
import math
import time

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
        include_visualization: bool = False,
        max_duration_seconds: float | None = None,
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

        try:
            fps = video.get(cv2.CAP_PROP_FPS)
            frame_count = video.get(cv2.CAP_PROP_FRAME_COUNT)
            width = video.get(cv2.CAP_PROP_FRAME_WIDTH)
            height = video.get(cv2.CAP_PROP_FRAME_HEIGHT)
            if not all(math.isfinite(v) and v > 0 for v in (fps, frame_count, width, height)):
                raise ValueError("Invalid video metadata.")
            total_frames = int(frame_count)
            duration_seconds = total_frames / fps
            if max_duration_seconds is not None:
                if not math.isfinite(max_duration_seconds) or max_duration_seconds <= 0:
                    raise ValueError("Invalid duration limit.")
                if duration_seconds > max_duration_seconds:
                    raise ValueError(f"Video exceeds {max_duration_seconds:g} seconds.")
                if width * height > 1920 * 1080:
                    raise ValueError("Demo video resolution exceeds 1920x1080 pixels.")
        except Exception:
            video.release()
            raise

        window = deque(maxlen=TEMPORAL_WINDOW)
        records = []
        timeline = []

        current_time = 0.0
        preview_frame = None
        preview_time = None
        preview_area = -1.0

        started = time.monotonic()
        try:
            while current_time < duration_seconds:
                if max_duration_seconds is not None and time.monotonic() - started > 180:
                    raise ValueError("Demo processing time budget exceeded.")
                video.set(
                    cv2.CAP_PROP_POS_MSEC,
                    current_time * 1000,
                )

                success, frame = video.read()

                if not success:
                    break

                if max_duration_seconds is not None and frame.shape[0] * frame.shape[1] > 1920 * 1080:
                    raise ValueError("Decoded frame exceeds demo resolution limit.")
                analysis = self.flood_analyzer.analyze(
                    frame
                )

                # Keep just one representative sampled frame.
                # Re-infer that frame for its overlay only when requested.
                if (
                    include_visualization
                    and analysis["flooded_area_percent"] > preview_area
                ):
                    preview_frame = frame.copy()
                    preview_time = current_time
                    preview_area = analysis["flooded_area_percent"]

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

        response = {
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

        if include_visualization and preview_frame is not None:
            # Only one additional model prediction; none when visualization
            # is disabled. This cannot affect the video's temporal verdict.
            preview = self.flood_analyzer.analyze(
                preview_frame,
                include_visualization=True,
            )["visualization"]
            preview["time_seconds"] = round(preview_time, 3)
            preview["selection_method"] = "largest_segmented_area"
            response["visualization"] = preview

        return response
