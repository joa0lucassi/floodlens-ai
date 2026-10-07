from collections import deque
from pathlib import Path
import csv
import json

import cv2
from ultralytics import YOLO


PROJECT_ROOT = Path(__file__).resolve().parents[2]

MODEL_PATH = (
    PROJECT_ROOT
    / "models"
    / "flood_segmentation"
    / "best.pt"
)

HOLDOUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "final_holdout_v2"
)

VIDEO_DIR = (
    HOLDOUT_DIR
    / "videos"
)

MANIFEST_PATH = (
    HOLDOUT_DIR
    / "metadata"
    / "manifest.csv"
)

RESULTS_DIR = (
    HOLDOUT_DIR
    / "results"
)

RESULTS_CSV = (
    RESULTS_DIR
    / "final_holdout_v2_results.csv"
)

RESULTS_JSON = (
    RESULTS_DIR
    / "final_holdout_v2_results.json"
)


CONFIDENCE_THRESHOLD = 0.25
INFERENCE_SIZE = 960

SAMPLE_INTERVAL_SECONDS = 1.0

TEMPORAL_WINDOW = 5
MIN_POSITIVE_SAMPLES = 3


def predict_frame(
    model,
    frame,
):
    results = model.predict(
        source=frame,
        imgsz=INFERENCE_SIZE,
        conf=CONFIDENCE_THRESHOLD,
        verbose=False,
    )

    result = results[0]

    if (
        result.boxes is None
        or len(result.boxes) == 0
    ):
        return {
            "detected": False,
            "confidence": 0.0,
            "detections": 0,
        }

    confidence = float(
        result.boxes.conf
        .max()
        .cpu()
        .item()
    )

    return {
        "detected": True,
        "confidence": confidence,
        "detections": len(
            result.boxes
        ),
    }


def load_manifest():
    with open(
        MANIFEST_PATH,
        "r",
        encoding="utf-8-sig",
    ) as file:
        reader = csv.DictReader(
            file
        )

        rows = list(
            reader
        )

    return {
        row["filename"]: row
        for row in rows
    }


def analyze_video(
    model,
    video_path,
):
    capture = cv2.VideoCapture(
        str(video_path)
    )

    if not capture.isOpened():
        raise RuntimeError(
            f"Could not open video: "
            f"{video_path}"
        )

    fps = capture.get(
        cv2.CAP_PROP_FPS
    )

    frame_count = int(
        capture.get(
            cv2.CAP_PROP_FRAME_COUNT
        )
    )

    if fps <= 0:
        capture.release()

        raise RuntimeError(
            f"Invalid FPS: "
            f"{video_path.name}"
        )

    duration = (
        frame_count / fps
    )

    window = deque(
        maxlen=TEMPORAL_WINDOW
    )

    timeline = []

    current_time = 0.0

    while current_time < duration:
        capture.set(
            cv2.CAP_PROP_POS_MSEC,
            current_time * 1000,
        )

        success, frame = (
            capture.read()
        )

        if not success:
            break

        prediction = predict_frame(
            model,
            frame,
        )

        raw_positive = bool(
            prediction[
                "detected"
            ]
        )

        window.append(
            raw_positive
        )

        positive_count = sum(
            window
        )

        window_ready = (
            len(window)
            == TEMPORAL_WINDOW
        )

        confirmed = (
            window_ready
            and positive_count
            >= MIN_POSITIVE_SAMPLES
        )

        timeline.append(
            {
                "time_seconds": round(
                    current_time,
                    3,
                ),
                "raw_positive": (
                    raw_positive
                ),
                "confidence": round(
                    prediction[
                        "confidence"
                    ],
                    4,
                ),
                "detections": (
                    prediction[
                        "detections"
                    ]
                ),
                "positive_samples_in_window": (
                    positive_count
                ),
                "window_size": (
                    len(window)
                ),
                "confirmed": (
                    confirmed
                ),
            }
        )

        current_time += (
            SAMPLE_INTERVAL_SECONDS
        )

    capture.release()

    raw_positives = sum(
        sample[
            "raw_positive"
        ]
        for sample in timeline
    )

    confirmed_samples = sum(
        sample[
            "confirmed"
        ]
        for sample in timeline
    )

    first_confirmation = next(
        (
            sample[
                "time_seconds"
            ]
            for sample in timeline
            if sample[
                "confirmed"
            ]
        ),
        None,
    )

    max_confidence = max(
        (
            sample[
                "confidence"
            ]
            for sample in timeline
        ),
        default=0.0,
    )

    video_prediction = (
        confirmed_samples > 0
    )

    return {
        "duration_seconds": round(
            duration,
            3,
        ),
        "samples": len(
            timeline
        ),
        "raw_positive_samples": (
            raw_positives
        ),
        "confirmed_samples": (
            confirmed_samples
        ),
        "first_confirmation_seconds": (
            first_confirmation
        ),
        "max_confidence": round(
            max_confidence,
            4,
        ),
        "predicted_flood": (
            video_prediction
        ),
        "timeline": timeline,
    }


def calculate_metrics(
    records,
):
    tp = 0
    tn = 0
    fp = 0
    fn = 0

    for record in records:
        expected = (
            record[
                "expected_class"
            ]
        )

        predicted = (
            record[
                "predicted_class"
            ]
        )

        if (
            expected == "flood"
            and predicted == "flood"
        ):
            tp += 1

        elif (
            expected == "dry"
            and predicted == "dry"
        ):
            tn += 1

        elif (
            expected == "dry"
            and predicted == "flood"
        ):
            fp += 1

        elif (
            expected == "flood"
            and predicted == "dry"
        ):
            fn += 1

    total = (
        tp + tn + fp + fn
    )

    accuracy = (
        (tp + tn) / total
        if total
        else 0.0
    )

    precision = (
        tp / (tp + fp)
        if (tp + fp)
        else 0.0
    )

    recall = (
        tp / (tp + fn)
        if (tp + fn)
        else 0.0
    )

    specificity = (
        tn / (tn + fp)
        if (tn + fp)
        else 0.0
    )

    f1 = (
        (
            2
            * precision
            * recall
            / (
                precision
                + recall
            )
        )
        if (
            precision
            + recall
        )
        else 0.0
    )

    return {
        "TP": tp,
        "TN": tn,
        "FP": fp,
        "FN": fn,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "specificity": specificity,
        "f1": f1,
    }


def main():
    print()
    print("FLOODLENS AI")
    print("FINAL HOLDOUT V2 EVALUATION")
    print("===========================")

    if RESULTS_CSV.exists():
        raise RuntimeError(
            "Final Holdout V2 has already "
            "been evaluated. "
            "Existing result file: "
            f"{RESULTS_CSV}"
        )

    if RESULTS_JSON.exists():
        raise RuntimeError(
            "Final Holdout V2 has already "
            "been evaluated. "
            "Existing result file: "
            f"{RESULTS_JSON}"
        )

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model not found: "
            f"{MODEL_PATH}"
        )

    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(
            f"Manifest not found: "
            f"{MANIFEST_PATH}"
        )

    manifest = load_manifest()

    video_samples = []

    for expected_class in [
        "flood",
        "dry",
    ]:
        folder = (
            VIDEO_DIR
            / expected_class
        )

        files = sorted(
            folder.glob(
                "*.mp4"
            )
        )

        for video_path in files:
            video_samples.append(
                {
                    "path": (
                        video_path
                    ),
                    "expected_class": (
                        expected_class
                    ),
                }
            )

    if len(video_samples) != 20:
        raise RuntimeError(
            "Expected exactly 20 videos, "
            f"found {len(video_samples)}."
        )

    print()
    print("FROZEN CONFIGURATION")
    print("====================")

    print(
        f"Model: "
        f"{MODEL_PATH.name}"
    )

    print(
        f"Confidence: "
        f"{CONFIDENCE_THRESHOLD}"
    )

    print(
        f"Inference size: "
        f"{INFERENCE_SIZE}"
    )

    print(
        f"Sampling: "
        f"{SAMPLE_INTERVAL_SECONDS}s"
    )

    print(
        f"Temporal rule: "
        f"{MIN_POSITIVE_SAMPLES}/"
        f"{TEMPORAL_WINDOW}"
    )

    print()
    print(
        "Loading model..."
    )

    model = YOLO(
        str(MODEL_PATH)
    )

    records = []

    for index, sample in enumerate(
        video_samples,
        start=1,
    ):
        video_path = (
            sample["path"]
        )

        expected_class = (
            sample[
                "expected_class"
            ]
        )

        metadata = manifest.get(
            video_path.name,
            {},
        )

        print()
        print(
            f"[{index:02d}/20] "
            f"{video_path.name}"
        )

        analysis = analyze_video(
            model,
            video_path,
        )

        predicted_class = (
            "flood"
            if analysis[
                "predicted_flood"
            ]
            else "dry"
        )

        correct = (
            predicted_class
            == expected_class
        )

        record = {
            "filename": (
                video_path.name
            ),
            "expected_class": (
                expected_class
            ),
            "category": (
                metadata.get(
                    "category",
                    "",
                )
            ),
            "predicted_class": (
                predicted_class
            ),
            "correct": (
                correct
            ),
            "duration_seconds": (
                analysis[
                    "duration_seconds"
                ]
            ),
            "samples": (
                analysis[
                    "samples"
                ]
            ),
            "raw_positive_samples": (
                analysis[
                    "raw_positive_samples"
                ]
            ),
            "confirmed_samples": (
                analysis[
                    "confirmed_samples"
                ]
            ),
            "first_confirmation_seconds": (
                analysis[
                    "first_confirmation_seconds"
                ]
            ),
            "max_confidence": (
                analysis[
                    "max_confidence"
                ]
            ),
            "timeline": (
                analysis[
                    "timeline"
                ]
            ),
        }

        records.append(
            record
        )

        print(
            f"Expected: "
            f"{expected_class}"
        )

        print(
            f"Predicted: "
            f"{predicted_class}"
        )

        print(
            f"Raw positives: "
            f"{record['raw_positive_samples']}/"
            f"{record['samples']}"
        )

        print(
            f"Confirmed samples: "
            f"{record['confirmed_samples']}"
        )

        print(
            f"First confirmation: "
            f"{record['first_confirmation_seconds']}"
        )

        print(
            f"Correct: "
            f"{correct}"
        )

    metrics = calculate_metrics(
        records
    )

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    csv_rows = []

    for record in records:
        csv_rows.append(
            {
                key: value
                for key, value
                in record.items()
                if key != "timeline"
            }
        )

    with open(
        RESULTS_CSV,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=(
                csv_rows[0].keys()
            ),
        )

        writer.writeheader()
        writer.writerows(
            csv_rows
        )

    output = {
        "evaluation": {
            "name": (
                "FloodLens AI Final "
                "Holdout V2"
            ),
            "model": (
                MODEL_PATH.name
            ),
            "confidence_threshold": (
                CONFIDENCE_THRESHOLD
            ),
            "inference_size": (
                INFERENCE_SIZE
            ),
            "sample_interval_seconds": (
                SAMPLE_INTERVAL_SECONDS
            ),
            "temporal_window": (
                TEMPORAL_WINDOW
            ),
            "min_positive_samples": (
                MIN_POSITIVE_SAMPLES
            ),
            "video_decision": (
                "flood if at least one "
                "temporal confirmation occurs"
            ),
        },
        "metrics": metrics,
        "records": records,
    }

    with open(
        RESULTS_JSON,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            output,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print()
    print("FINAL RESULTS")
    print("=============")

    print(
        f"TP: {metrics['TP']}"
    )

    print(
        f"TN: {metrics['TN']}"
    )

    print(
        f"FP: {metrics['FP']}"
    )

    print(
        f"FN: {metrics['FN']}"
    )

    print()
    print(
        f"Accuracy: "
        f"{metrics['accuracy'] * 100:.2f}%"
    )

    print(
        f"Precision: "
        f"{metrics['precision'] * 100:.2f}%"
    )

    print(
        f"Recall: "
        f"{metrics['recall'] * 100:.2f}%"
    )

    print(
        f"Specificity: "
        f"{metrics['specificity'] * 100:.2f}%"
    )

    print(
        f"F1-score: "
        f"{metrics['f1'] * 100:.2f}%"
    )

    print()
    print("FAILURES")
    print("========")

    failures = [
        record
        for record in records
        if not record["correct"]
    ]

    if not failures:
        print(
            "No video-level failures."
        )

    else:
        for record in failures:
            print(
                f"{record['filename']} "
                f"| expected="
                f"{record['expected_class']} "
                f"| predicted="
                f"{record['predicted_class']} "
                f"| category="
                f"{record['category']} "
                f"| raw="
                f"{record['raw_positive_samples']}/"
                f"{record['samples']} "
                f"| confirmed="
                f"{record['confirmed_samples']} "
                f"| max_conf="
                f"{record['max_confidence']:.2f}"
            )

    print()
    print("RESULTS SAVED")
    print("=============")

    print(
        RESULTS_CSV
    )

    print(
        RESULTS_JSON
    )


if __name__ == "__main__":
    main()