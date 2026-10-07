import csv
import json
from pathlib import Path

import cv2

from src.vision.inference import FloodAnalyzer


EVALUATION_DIR = Path(
    "data/evaluation/images"
)

FLOOD_DIR = (
    EVALUATION_DIR / "flood"
)

DRY_DIR = (
    EVALUATION_DIR / "dry"
)

OUTPUT_DIR = Path(
    "data/evaluation/results"
)

REPORT_PATH = (
    OUTPUT_DIR
    / "evaluation_report.csv"
)

FAILURES_PATH = (
    OUTPUT_DIR
    / "failure_cases.csv"
)

SUMMARY_PATH = (
    OUTPUT_DIR
    / "evaluation_summary.json"
)

SUPPORTED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}


def get_images(
    directory: Path,
):
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


def evaluate_image(
    analyzer,
    image_path,
    expected_label,
):
    image = cv2.imread(
        str(image_path)
    )

    if image is None:
        print(
            f"Erro ao abrir: "
            f"{image_path}"
        )

        return None

    analysis = analyzer.analyze(
        image
    )

    predicted_flood = bool(
        analysis["flood_detected"]
    )

    expected_flood = (
        expected_label == "flood"
    )

    predicted_label = (
        "flood"
        if predicted_flood
        else "dry"
    )

    correct = (
        predicted_flood
        == expected_flood
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

        "flood_detected":
            predicted_flood,

        "flooded_area_percent":
            analysis[
                "flooded_area_percent"
            ],

        "detections":
            analysis[
                "detections"
            ],

        "max_confidence":
            analysis[
                "max_confidence"
            ],

        "image_width":
            analysis[
                "image_width"
            ],

        "image_height":
            analysis[
                "image_height"
            ],
    }


def main():
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
        "FloodLens AI - Evaluation"
    )

    print("=" * 65)

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

    print("=" * 65)
    print()

    if (
        not flood_images
        and not dry_images
    ):
        print(
            "Nenhuma imagem encontrada."
        )

        return

    analyzer = FloodAnalyzer()

    records = []

    test_groups = [
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
    ) in test_groups:

        print(
            f"Testing: "
            f"{expected_label.upper()}"
        )

        print("-" * 65)

        for image_path in images:
            record = evaluate_image(
                analyzer=analyzer,
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

            confidence = (
                record[
                    "max_confidence"
                ]
            )

            if confidence is None:
                confidence = 0.0

            print(
                f"{status:<5} | "
                f"{image_path.name:<30} | "
                f"Expected: "
                f"{expected_label:<5} | "
                f"Predicted: "
                f"{record['predicted_label']:<5} | "
                f"Area: "
                f"{record['flooded_area_percent']:>6.2f}% | "
                f"Conf: "
                f"{confidence:.2f}"
            )

        print()

    if not records:
        print(
            "Nenhuma imagem foi "
            "analisada com sucesso."
        )

        return

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

    with open(
        REPORT_PATH,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=(
                records[0].keys()
            ),
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
            fieldnames=(
                records[0].keys()
            ),
        )

        writer.writeheader()

        writer.writerows(
            failures
        )

    summary = {
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

    print("=" * 65)

    print(
        "RESULTS"
    )

    print("=" * 65)

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
        f"Full report: "
        f"{REPORT_PATH}"
    )

    print(
        f"Failures:    "
        f"{FAILURES_PATH}"
    )

    print(
        f"Summary:     "
        f"{SUMMARY_PATH}"
    )


if __name__ == "__main__":
    main()