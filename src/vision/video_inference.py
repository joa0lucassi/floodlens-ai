from pathlib import Path

import cv2

from src.risk.risk_engine import calculate_risk
from src.vision.inference import FloodAnalyzer


SAMPLE_INTERVAL_SECONDS = 1.0


class VideoFloodAnalyzer:
    def __init__(self, flood_analyzer: FloodAnalyzer):
        self.flood_analyzer = flood_analyzer

    def analyze_video(
        self,
        video_path: str | Path,
        sample_interval_seconds: float = SAMPLE_INTERVAL_SECONDS,
    ):
        video = cv2.VideoCapture(
            str(video_path)
        )

        if not video.isOpened():
            raise ValueError(
                "Could not open the uploaded video."
            )

        fps = video.get(
            cv2.CAP_PROP_FPS
        )

        total_frames = int(
            video.get(
                cv2.CAP_PROP_FRAME_COUNT
            )
        )

        if fps <= 0:
            video.release()

            raise ValueError(
                "Invalid video FPS."
            )

        duration_seconds = (
            total_frames / fps
        )

        frame_interval = max(
            1,
            int(
                fps
                * sample_interval_seconds
            )
        )

        records = []

        frame_index = 0

        while True:
            success, frame = video.read()

            if not success:
                break

            if (
                frame_index
                % frame_interval
                != 0
            ):
                frame_index += 1
                continue

            time_seconds = (
                frame_index / fps
            )

            analysis = (
                self.flood_analyzer
                .analyze(frame)
            )

            records.append(
                {
                    "time_seconds": round(
                        time_seconds,
                        2,
                    ),
                    "flooded_area": (
                        analysis[
                            "flooded_area_percent"
                        ]
                    ),
                    "detections": (
                        analysis[
                            "detections"
                        ]
                    ),
                    "max_confidence": (
                        analysis[
                            "max_confidence"
                        ]
                    ),
                }
            )

            frame_index += 1

        video.release()

        if not records:
            raise ValueError(
                "No frames could be analyzed."
            )

        risk = calculate_risk(
            records
        )

        timeline = []

        for record in records:
            timeline.append(
                {
                    "time_seconds": (
                        record[
                            "time_seconds"
                        ]
                    ),
                    "flooded_area_percent": (
                        record[
                            "flooded_area"
                        ]
                    ),
                    "detections": (
                        record[
                            "detections"
                        ]
                    ),
                    "max_confidence": (
                        record[
                            "max_confidence"
                        ]
                    ),
                }
            )

        return {
            "video": {
                "fps": round(
                    fps,
                    2,
                ),
                "total_frames": (
                    total_frames
                ),
                "duration_seconds": round(
                    duration_seconds,
                    2,
                ),
                "sample_interval_seconds": (
                    sample_interval_seconds
                ),
                "samples_analyzed": len(
                    records
                ),
            },
            "risk": risk,
            "timeline": timeline,
        }