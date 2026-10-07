from collections import deque
from pathlib import Path
from statistics import median
import argparse

import cv2

from src.vision.inference import FloodAnalyzer


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_VIDEO_PATH = (
    PROJECT_ROOT
    / "data"
    / "flood_sample.mp4"
)

SAMPLE_INTERVAL_SECONDS = 1.0

TEMPORAL_WINDOW = 5
MIN_POSITIVE_SAMPLES = 3


class TemporalVideoFloodAnalyzer:
    def __init__(
        self,
        flood_analyzer: FloodAnalyzer,
    ):
        self.flood_analyzer = flood_analyzer

    def analyze_video(
        self,
        video_path: str | Path,
        sample_interval_seconds: float = SAMPLE_INTERVAL_SECONDS,
    ):
        video_path = Path(video_path)

        video = cv2.VideoCapture(
            str(video_path)
        )

        if not video.isOpened():
            raise ValueError(
                f"Could not open video: {video_path}"
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
                fps * sample_interval_seconds
            ),
        )

        window = deque(
            maxlen=TEMPORAL_WINDOW
        )

        timeline = []

        frame_index = 0

        raw_positive_samples = 0
        temporal_confirmed_samples = 0

        first_confirmation_time = None

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

            raw_detected = bool(
                analysis[
                    "flood_detected"
                ]
            )

            if raw_detected:
                raw_positive_samples += 1

            sample = {
                "time_seconds": round(
                    time_seconds,
                    2,
                ),
                "raw_detected": raw_detected,
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

            window.append(sample)

            positive_samples = sum(
                1
                for item in window
                if item["raw_detected"]
            )

            window_ready = (
                len(window)
                == TEMPORAL_WINDOW
            )

            temporal_confirmed = (
                window_ready
                and positive_samples
                >= MIN_POSITIVE_SAMPLES
            )

            positive_areas = [
                item["flooded_area"]
                for item in window
                if item["raw_detected"]
            ]

            positive_confidences = [
                item["max_confidence"]
                for item in window
                if item["raw_detected"]
            ]

            if (
                temporal_confirmed
                and positive_areas
            ):
                temporal_area = float(
                    median(
                        positive_areas
                    )
                )
            else:
                temporal_area = 0.0

            if (
                temporal_confirmed
                and positive_confidences
            ):
                temporal_confidence = float(
                    median(
                        positive_confidences
                    )
                )
            else:
                temporal_confidence = 0.0

            if temporal_confirmed:
                temporal_confirmed_samples += 1

                if (
                    first_confirmation_time
                    is None
                ):
                    first_confirmation_time = round(
                        time_seconds,
                        2,
                    )

            timeline.append(
                {
                    **sample,
                    "window_size": len(
                        window
                    ),
                    "positive_samples_in_window": (
                        positive_samples
                    ),
                    "window_ready": (
                        window_ready
                    ),
                    "temporal_confirmed": (
                        temporal_confirmed
                    ),
                    "temporal_area_percent": round(
                        temporal_area,
                        2,
                    ),
                    "temporal_confidence": round(
                        temporal_confidence,
                        2,
                    ),
                }
            )

            frame_index += 1

        video.release()

        if not timeline:
            raise ValueError(
                "No frames could be analyzed."
            )

        temporal_flood_detected = any(
            record[
                "temporal_confirmed"
            ]
            for record in timeline
        )

        return {
            "video": {
                "path": str(video_path),
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
                    timeline
                ),
            },
            "temporal_config": {
                "window": (
                    TEMPORAL_WINDOW
                ),
                "minimum_positive_samples": (
                    MIN_POSITIVE_SAMPLES
                ),
            },
            "summary": {
                "raw_positive_samples": (
                    raw_positive_samples
                ),
                "raw_negative_samples": (
                    len(timeline)
                    - raw_positive_samples
                ),
                "temporal_confirmed_samples": (
                    temporal_confirmed_samples
                ),
                "temporal_flood_detected": (
                    temporal_flood_detected
                ),
                "first_confirmation_time_seconds": (
                    first_confirmation_time
                ),
            },
            "timeline": timeline,
        }


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "FloodLens AI temporal "
            "consistency experiment"
        )
    )

    parser.add_argument(
        "video",
        nargs="?",
        default=str(
            DEFAULT_VIDEO_PATH
        ),
        help=(
            "Path to the video file"
        ),
    )

    return parser.parse_args()


def main():
    args = parse_args()

    video_path = Path(
        args.video
    )

    analyzer = FloodAnalyzer()

    temporal_analyzer = (
        TemporalVideoFloodAnalyzer(
            analyzer
        )
    )

    result = (
        temporal_analyzer
        .analyze_video(
            video_path
        )
    )

    print()
    print("FLOODLENS AI")
    print("TEMPORAL CONSISTENCY EXPERIMENT")
    print("===============================")

    print()
    print(
        f"Video: "
        f"{video_path.name}"
    )

    print(
        f"Duration: "
        f"{result['video']['duration_seconds']:.2f}s"
    )

    print(
        f"Samples: "
        f"{result['video']['samples_analyzed']}"
    )

    print()
    print(
        "Temporal rule: "
        f"{MIN_POSITIVE_SAMPLES}/"
        f"{TEMPORAL_WINDOW}"
    )

    print()
    print("TIMELINE")
    print("========")

    for record in result["timeline"]:
        status = (
            "CONFIRMED"
            if record[
                "temporal_confirmed"
            ]
            else "NOT CONFIRMED"
        )

        print(
            f"{record['time_seconds']:5.1f}s | "
            f"raw="
            f"{str(record['raw_detected']):5} | "
            f"window="
            f"{record['positive_samples_in_window']}/"
            f"{record['window_size']} | "
            f"area="
            f"{record['flooded_area']:6.2f}% | "
            f"conf="
            f"{record['max_confidence']:.2f} | "
            f"{status}"
        )

    print()
    print("SUMMARY")
    print("=======")

    summary = result[
        "summary"
    ]

    print(
        "Raw positive samples:",
        summary[
            "raw_positive_samples"
        ],
    )

    print(
        "Raw negative samples:",
        summary[
            "raw_negative_samples"
        ],
    )

    print(
        "Confirmed samples:",
        summary[
            "temporal_confirmed_samples"
        ],
    )

    print(
        "Temporal flood detected:",
        summary[
            "temporal_flood_detected"
        ],
    )

    print(
        "First confirmation:",
        summary[
            "first_confirmation_time_seconds"
        ],
    )


if __name__ == "__main__":
    main()