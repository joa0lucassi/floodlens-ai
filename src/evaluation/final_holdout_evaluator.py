import csv
import json
from pathlib import Path

import cv2
from ultralytics import YOLO


MODEL_PATH = Path(
    "models/flood_segmentation/best_hardneg.pt"
)

HOLDOUT_ROOT = Path(
    "data/final_holdout/images"
)

FLOOD_DIR = (
    HOLDOUT_ROOT / "flood"
)

DRY_DIR = (
    HOLDOUT_ROOT / "dry"
)

OUTPUT_DIR = Path(
    "data/final_holdout/results"
)

REPORT_PATH = (
    OUTPUT_DIR
    / "final_holdout_report.csv"
)

FAILURES_PATH = (
    OUTPUT_DIR
    / "final_holdout_failures.csv"
)

SUMMARY_PATH = (
    OUTPUT_DIR
    / "final_holdout_summary.json"
)

SUPPORTED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}


def get_images(directory):
    if not directory.exists():
        return []

    return sorted(
        file
        for file in directory.iterdir()
        if (
            file.is_file()
            and file.suffix.lower()
            in SUPPORTED_EXTENSIONS
        )
    )


def safe_divide(
    numerator,
    denominator,
):
    if denominator == 0:
        return 0.0

    return numerator / denominator


def analyze_image(
    model,
    image_path,
    expected_label,
):
    image = cv2.imread(
        str(image_path)
    )

    if image is None:
        print(
            f"Erro ao abrir: "
            f"{image_path.name}"
        )

        return None

    height, width = (
        image.shape[:2]
    )

    results = model.predict(
        source=str(image_path),
        imgsz=640,
        conf=0.25,
        verbose=False,
    )

    result = results[0]

    detections = len(
        result.boxes
    )

    predicted_flood = (
        detections > 0
    )

    max_confidence = 0.0

    if detections > 0:
        max_confidence = float(
            result.boxes.conf.max()
        )

    flooded_area_percent = 0.0

    if (
        result.masks is not None
        and detections > 0
    ):
        import numpy as np

        combined_mask = np.zeros(
            (height, width),
            dtype=np.uint8,
        )

        for mask_tensor in (
            result.masks.data
        ):
            mask = (
                mask_tensor
                .cpu()
                .numpy()
            )

            mask = cv2.resize(
                mask,
                (width, height),
                interpolation=(
                    cv2.INTER_NEAREST
                ),
            )

            combined_mask[
                mask > 0.5
            ] = 1

        flooded_pixels = int(
            combined_mask.sum()
        )

        total_pixels = (
            width * height
        )

        flooded_area_percent = (
            flooded_pixels
            / total_pixels
        ) * 100

    predicted_label = (
        "flood"
        if predicted_flood
        else "dry"
    )

    correct = (
        predicted_label
        == expected_label
    )

    return {
        "filename":
            image_path.name,

        "expected_label":
            expected_label,

        "predicted_label":
            predicted_label,

        "correct":
            correct,

        "flooded_area_percent":
            round(
                flooded_area_percent,
                2,
            ),

        "detections":
            detections,

        "max_confidence":
            round(
                max_confidence,
                4,
            ),

        "image_width":
            width,

        "image_height":
            height,
    }


def main():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Modelo não encontrado: "
            f"{MODEL_PATH}"
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    flood_images = get_images(
        FLOOD_DIR
    )

    dry_images = get_images(
        DRY_DIR
    )

    print()
    print(
        "FloodLens AI - FINAL HOLDOUT"
    )

    print("=" * 70)

    print(
        f"Flood images: "
        f"{len(flood_images)}"
    )

    print(
        f"Dry images:   "
        f"{len(dry_images)}"
    )

    print(
        f"Total:        "
        f"{len(flood_images) + len(dry_images)}"
    )

    print("=" * 70)
    print()

    if len(flood_images) != 10:
        print(
            "AVISO: esperávamos "
            "10 imagens flood."
        )

    if len(dry_images) != 10:
        print(
            "AVISO: esperávamos "
            "10 imagens dry."
        )

    model = YOLO(
        str(MODEL_PATH)
    )

    records = []

    groups = [
        (
            "flood",
            flood_images,
        ),
        (
            "dry",
            dry_images,
        ),
    ]

    for (
        expected_label,
        images,
    ) in groups:

        print(
            f"Testing: "
            f"{expected_label.upper()}"
        )

        print("-" * 70)

        for image_path in images:
            record = analyze_image(
                model=model,
                image_path=image_path,
                expected_label=expected_label,
            )

            if record is None:
                continue

            records.append(
                record
            )

            status = (
                "OK"
                if record["correct"]
                else "ERROR"
            )

            print(
                f"{status:<5} | "
                f"{image_path.name:<15} | "
                f"Expected: "
                f"{record['expected_label']:<5} | "
                f"Predicted: "
                f"{record['predicted_label']:<5} | "
                f"Area: "
                f"{record['flooded_area_percent']:>6.2f}% | "
                f"Conf: "
                f"{record['max_confidence']:.2f}"
            )

        print()

    true_positive = 0
    true_negative = 0
    false_positive = 0
    false_negative = 0

    for record in records:
        expected = (
            record[
                "expected_label"
            ]
        )

        predicted = (
            record[
                "predicted_label"
            ]
        )

        if (
            expected == "flood"
            and predicted == "flood"
        ):
            true_positive += 1

        elif (
            expected == "dry"
            and predicted == "dry"
        ):
            true_negative += 1

        elif (
            expected == "dry"
            and predicted == "flood"
        ):
            false_positive += 1

        elif (
            expected == "flood"
            and predicted == "dry"
        ):
            false_negative += 1

    total = len(
        records
    )

    accuracy = safe_divide(
        true_positive
        + true_negative,
        total,
    )

    precision = safe_divide(
        true_positive,
        true_positive
        + false_positive,
    )

    recall = safe_divide(
        true_positive,
        true_positive
        + false_negative,
    )

    specificity = safe_divide(
        true_negative,
        true_negative
        + false_positive,
    )

    f1_score = safe_divide(
        2
        * precision
        * recall,
        precision
        + recall,
    )

    failures = [
        record
        for record in records
        if not record[
            "correct"
        ]
    ]

    fieldnames = [
        "filename",
        "expected_label",
        "predicted_label",
        "correct",
        "flooded_area_percent",
        "detections",
        "max_confidence",
        "image_width",
        "image_height",
    ]

    with open(
        REPORT_PATH,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        writer.writerows(
            records
        )

    with open(
        FAILURES_PATH,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        writer.writerows(
            failures
        )

    summary = {
        "evaluation_type":
            "final_holdout",

        "model":
            str(MODEL_PATH),

        "total_images":
            total,

        "flood_images":
            len(flood_images),

        "dry_images":
            len(dry_images),

        "true_positive":
            true_positive,

        "true_negative":
            true_negative,

        "false_positive":
            false_positive,

        "false_negative":
            false_negative,

        "accuracy":
            round(
                accuracy,
                4,
            ),

        "precision":
            round(
                precision,
                4,
            ),

        "recall":
            round(
                recall,
                4,
            ),

        "specificity":
            round(
                specificity,
                4,
            ),

        "f1_score":
            round(
                f1_score,
                4,
            ),

        "failure_count":
            len(failures),
    }

    with open(
        SUMMARY_PATH,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            summary,
            file,
            indent=4,
        )

    print()
    print("=" * 70)

    print(
        "FINAL HOLDOUT RESULTS"
    )

    print("=" * 70)

    print(
        f"TP: {true_positive}"
    )

    print(
        f"TN: {true_negative}"
    )

    print(
        f"FP: {false_positive}"
    )

    print(
        f"FN: {false_negative}"
    )

    print()

    print(
        f"Accuracy:    "
        f"{accuracy * 100:.2f}%"
    )

    print(
        f"Precision:   "
        f"{precision * 100:.2f}%"
    )

    print(
        f"Recall:      "
        f"{recall * 100:.2f}%"
    )

    print(
        f"Specificity: "
        f"{specificity * 100:.2f}%"
    )

    print(
        f"F1-score:    "
        f"{f1_score * 100:.2f}%"
    )

    print()

    print(
        f"Failure cases: "
        f"{len(failures)}"
    )

    print()

    print(
        "Report:"
    )

    print(
        REPORT_PATH
    )

    print(
        "Failures:"
    )

    print(
        FAILURES_PATH
    )

    print(
        "Summary:"
    )

    print(
        SUMMARY_PATH
    )


if __name__ == "__main__":
    main()