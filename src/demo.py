from collections import deque
from pathlib import Path
import argparse

import cv2
import numpy as np
from ultralytics import YOLO


PROJECT_ROOT = Path(__file__).resolve().parents[1]

MODEL_PATH = (
    PROJECT_ROOT
    / "models"
    / "flood_segmentation"
    / "best.pt"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "demo_output"
)

CONFIDENCE_THRESHOLD = 0.25
INFERENCE_SIZE = 960

SAMPLE_INTERVAL_SECONDS = 1.0
TEMPORAL_WINDOW = 5
MIN_POSITIVE_SAMPLES = 3


def calculate_flooded_area(
    result,
    image_shape,
):
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

        points = polygon.astype(
            np.int32
        )

        cv2.fillPoly(
            combined_mask,
            [points],
            255,
        )

    flooded_pixels = cv2.countNonZero(
        combined_mask
    )

    total_pixels = height * width

    if total_pixels == 0:
        return 0.0

    return (
        flooded_pixels
        / total_pixels
    ) * 100


def analyze_frame(
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

    detection_count = 0
    max_confidence = 0.0

    if (
        result.boxes is not None
        and len(result.boxes) > 0
    ):
        detection_count = len(
            result.boxes
        )

        max_confidence = float(
            result.boxes.conf
            .max()
            .cpu()
            .item()
        )

    flooded_area = (
        calculate_flooded_area(
            result,
            frame.shape,
        )
    )

    return {
        "result": result,
        "detected": detection_count > 0,
        "detections": detection_count,
        "confidence": max_confidence,
        "flooded_area": flooded_area,
    }


def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            "Model not found: "
            f"{MODEL_PATH}"
        )

    print("Loading YOLO11-seg model...")

    return YOLO(
        str(MODEL_PATH)
    )


def run_image_demo(
    model,
    image_path,
):
    image_path = Path(
        image_path
    ).resolve()

    if not image_path.exists():
        raise FileNotFoundError(
            "Image not found: "
            f"{image_path}"
        )

    image = cv2.imread(
        str(image_path)
    )

    if image is None:
        raise ValueError(
            "Could not open image."
        )

    print()
    print("FloodLens AI - Image Analysis")
    print("=" * 56)
    print(
        f"Image: {image_path.name}"
    )
    print(
        "Model: YOLO11-seg"
    )
    print(
        f"Inference size: {INFERENCE_SIZE}"
    )
    print(
        f"Confidence threshold: "
        f"{CONFIDENCE_THRESHOLD:.2f}"
    )
    print("=" * 56)

    analysis = analyze_frame(
        model,
        image,
    )

    predicted_class = (
        "FLOOD"
        if analysis["detected"]
        else "DRY"
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        OUTPUT_DIR
        / (
            f"{image_path.stem}"
            "_prediction.jpg"
        )
    )

    annotated = (
        analysis["result"].plot()
    )

    cv2.imwrite(
        str(output_path),
        annotated,
    )

    print()
    print("RESULT")
    print("=" * 56)
    print(
        f"Prediction: {predicted_class}"
    )
    print(
        f"Detections: "
        f"{analysis['detections']}"
    )
    print(
        f"Max confidence: "
        f"{analysis['confidence']:.2f}"
    )
    print(
        f"Visual flooded area: "
        f"{analysis['flooded_area']:.2f}%"
    )
    print(
        f"Annotated image: "
        f"{output_path}"
    )
    print("=" * 56)


def run_video_demo(
    model,
    video_path,
):
    video_path = Path(
        video_path
    ).resolve()

    if not video_path.exists():
        raise FileNotFoundError(
            "Video not found: "
            f"{video_path}"
        )

    capture = cv2.VideoCapture(
        str(video_path)
    )

    if not capture.isOpened():
        raise ValueError(
            "Could not open video."
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
        raise ValueError(
            "Invalid video FPS."
        )

    duration = (
        frame_count / fps
    )

    print()
    print("FloodLens AI - Video Analysis")
    print("=" * 72)
    print(
        f"Video: {video_path.name}"
    )
    print(
        "Model: YOLO11-seg"
    )
    print(
        f"Inference size: {INFERENCE_SIZE}"
    )
    print(
        f"Confidence threshold: "
        f"{CONFIDENCE_THRESHOLD:.2f}"
    )
    print(
        f"Sampling: "
        f"1 frame every "
        f"{SAMPLE_INTERVAL_SECONDS:.0f} second"
    )
    print(
        f"Temporal rule: "
        f"{MIN_POSITIVE_SAMPLES}/"
        f"{TEMPORAL_WINDOW}"
    )
    print(
        f"Video duration: "
        f"{duration:.2f}s"
    )
    print("=" * 72)
    print()

    window = deque(
        maxlen=TEMPORAL_WINDOW
    )

    current_time = 0.0
    sample_count = 0
    raw_positive_count = 0
    confirmed_count = 0
    first_confirmation = None

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

        analysis = analyze_frame(
            model,
            frame,
        )

        raw_positive = bool(
            analysis["detected"]
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

        if raw_positive:
            raw_positive_count += 1

        if confirmed:
            confirmed_count += 1

            if first_confirmation is None:
                first_confirmation = (
                    current_time
                )

        sample_count += 1

        raw_label = (
            "FLOOD"
            if raw_positive
            else "DRY"
        )

        if not window_ready:
            temporal_status = "WAITING"
        elif confirmed:
            temporal_status = "CONFIRMED"
        else:
            temporal_status = (
                "NOT CONFIRMED"
            )

        confidence_text = (
            f"{analysis['confidence']:.2f}"
            if raw_positive
            else "--"
        )

        print(
            f"{current_time:5.1f}s | "
            f"{raw_label:<5} | "
            f"Conf: {confidence_text:<4} | "
            f"Area: "
            f"{analysis['flooded_area']:6.2f}% | "
            f"Window: "
            f"{positive_count}/"
            f"{len(window)} | "
            f"{temporal_status}"
        )

        current_time += (
            SAMPLE_INTERVAL_SECONDS
        )

    capture.release()

    video_flood = (
        confirmed_count > 0
    )

    print()
    print("=" * 72)
    print("FINAL RESULT")
    print("=" * 72)

    if video_flood:
        print(
            "Status: FLOOD DETECTED"
        )
        print(
            "First temporal confirmation: "
            f"{first_confirmation:.1f}s"
        )
    else:
        print(
            "Status: NO FLOOD CONFIRMED"
        )

    print(
        f"Samples analyzed: "
        f"{sample_count}"
    )
    print(
        f"Raw positive samples: "
        f"{raw_positive_count}/"
        f"{sample_count}"
    )
    print(
        f"Temporal confirmations: "
        f"{confirmed_count}"
    )
    print(
        f"Temporal rule: "
        f"{MIN_POSITIVE_SAMPLES}/"
        f"{TEMPORAL_WINDOW}"
    )
    print("=" * 72)


def main():
    parser = argparse.ArgumentParser(
        description=(
            "FloodLens AI local "
            "demonstration."
        )
    )

    parser.add_argument(
        "mode",
        choices=[
            "image",
            "video",
        ],
        help=(
            "Analyze one image "
            "or one video."
        ),
    )

    parser.add_argument(
        "path",
        help=(
            "Path to the image "
            "or video file."
        ),
    )

    args = parser.parse_args()

    model = load_model()

    if args.mode == "image":
        run_image_demo(
            model,
            args.path,
        )
    else:
        run_video_demo(
            model,
            args.path,
        )


if __name__ == "__main__":
    main()
