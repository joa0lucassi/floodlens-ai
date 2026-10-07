from pathlib import Path
import csv
import json

from src.vision.inference import FloodAnalyzer
from src.vision.inference_spatial import SpatialFloodAnalyzer

import cv2


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATASET_DIR = (
    PROJECT_ROOT
    / "data"
    / "regression_set"
    / "images"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "model_comparison"
    / "spatial_experiment"
)

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp",
}


def calculate_metrics(records, key):
    tp = 0
    tn = 0
    fp = 0
    fn = 0

    failures = []

    for record in records:
        expected = record["expected"]
        predicted = record[key]["predicted"]

        if expected == "flood" and predicted == "flood":
            tp += 1

        elif expected == "dry" and predicted == "dry":
            tn += 1

        elif expected == "dry" and predicted == "flood":
            fp += 1
            failures.append(record)

        elif expected == "flood" and predicted == "dry":
            fn += 1
            failures.append(record)

    total = tp + tn + fp + fn

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
        2 * precision * recall
        / (precision + recall)
        if (precision + recall)
        else 0.0
    )

    return {
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "specificity": specificity,
        "f1": f1,
        "failures": failures,
    }


def main():
    print()
    print("FLOODLENS AI")
    print("BASELINE VS SPATIAL PIPELINE")
    print("============================")
    print()

    if not DATASET_DIR.exists():
        raise FileNotFoundError(
            f"Regression set não encontrado: {DATASET_DIR}"
        )

    baseline_analyzer = FloodAnalyzer()
    spatial_analyzer = SpatialFloodAnalyzer()

    image_records = []

    for expected in ["flood", "dry"]:
        folder = DATASET_DIR / expected

        if not folder.exists():
            raise FileNotFoundError(
                f"Pasta não encontrada: {folder}"
            )

        images = sorted(
            [
                path
                for path in folder.iterdir()
                if path.is_file()
                and path.suffix.lower()
                in IMAGE_EXTENSIONS
            ]
        )

        for image_path in images:
            image_records.append(
                {
                    "path": image_path,
                    "filename": image_path.name,
                    "expected": expected,
                }
            )

    print(
        f"Imagens encontradas: {len(image_records)}"
    )
    print()

    results = []

    for index, item in enumerate(
        image_records,
        start=1,
    ):
        image = cv2.imread(
            str(item["path"])
        )

        if image is None:
            raise RuntimeError(
                f"Não foi possível abrir: {item['path']}"
            )

        baseline = baseline_analyzer.analyze(
            image
        )

        spatial = spatial_analyzer.analyze(
            image
        )

        baseline_predicted = (
            "flood"
            if baseline["flood_detected"]
            else "dry"
        )

        spatial_predicted = (
            "flood"
            if spatial["flood_detected"]
            else "dry"
        )

        record = {
            "filename": item["filename"],
            "expected": item["expected"],

            "baseline": {
                "predicted": baseline_predicted,
                "flooded_area_percent": baseline[
                    "flooded_area_percent"
                ],
                "detections": baseline[
                    "detections"
                ],
                "max_confidence": baseline[
                    "max_confidence"
                ],
            },

            "spatial": {
                "predicted": spatial_predicted,
                "raw_flooded_area_percent": spatial[
                    "raw_flooded_area_percent"
                ],
                "filtered_flooded_area_percent": spatial[
                    "filtered_flooded_area_percent"
                ],
                "roi_flooded_area_percent": spatial[
                    "roi_flooded_area_percent"
                ],
                "raw_detections": spatial[
                    "raw_detections"
                ],
                "kept_components": spatial[
                    "kept_components"
                ],
                "removed_components": spatial[
                    "removed_components"
                ],
                "max_confidence": spatial[
                    "max_confidence"
                ],
            },
        }

        results.append(record)

        changed = (
            baseline_predicted
            != spatial_predicted
        )

        change_marker = (
            "CHANGED"
            if changed
            else ""
        )

        print(
            f"[{index:02d}/{len(image_records)}] "
            f"{item['filename']:12} "
            f"expected={item['expected']:5} "
            f"baseline={baseline_predicted:5} "
            f"spatial={spatial_predicted:5} "
            f"{change_marker}"
        )

    baseline_metrics = calculate_metrics(
        results,
        "baseline",
    )

    spatial_metrics = calculate_metrics(
        results,
        "spatial",
    )

    print()
    print("A/B RESULTS")
    print("===========")
    print()

    print(
        f"{'Metric':<20}"
        f"{'Baseline':>15}"
        f"{'Spatial':>15}"
    )

    print(
        f"{'TP':<20}"
        f"{baseline_metrics['tp']:>15}"
        f"{spatial_metrics['tp']:>15}"
    )

    print(
        f"{'TN':<20}"
        f"{baseline_metrics['tn']:>15}"
        f"{spatial_metrics['tn']:>15}"
    )

    print(
        f"{'FP':<20}"
        f"{baseline_metrics['fp']:>15}"
        f"{spatial_metrics['fp']:>15}"
    )

    print(
        f"{'FN':<20}"
        f"{baseline_metrics['fn']:>15}"
        f"{spatial_metrics['fn']:>15}"
    )

    metric_names = [
        ("Accuracy", "accuracy"),
        ("Precision", "precision"),
        ("Recall", "recall"),
        ("Specificity", "specificity"),
        ("F1-score", "f1"),
    ]

    for label, key in metric_names:
        baseline_value = (
            baseline_metrics[key] * 100
        )

        spatial_value = (
            spatial_metrics[key] * 100
        )

        print(
            f"{label:<20}"
            f"{baseline_value:>14.2f}%"
            f"{spatial_value:>14.2f}%"
        )

    print()
    print("CLASSIFICATIONS CHANGED")
    print("=======================")

    changed_records = []

    for record in results:
        old = record[
            "baseline"
        ]["predicted"]

        new = record[
            "spatial"
        ]["predicted"]

        if old != new:
            changed_records.append(record)

            print(
                f"{record['filename']:12} "
                f"expected={record['expected']:5} "
                f"{old:5} -> {new:5} "
                f"raw_area="
                f"{record['spatial']['raw_flooded_area_percent']:.2f}% "
                f"filtered_area="
                f"{record['spatial']['filtered_flooded_area_percent']:.2f}% "
                f"kept="
                f"{record['spatial']['kept_components']} "
                f"removed="
                f"{record['spatial']['removed_components']}"
            )

    if not changed_records:
        print(
            "Nenhuma classificação mudou."
        )

    print()
    print("SPATIAL FAILURES")
    print("================")

    for record in spatial_metrics[
        "failures"
    ]:
        spatial = record[
            "spatial"
        ]

        print(
            f"{record['filename']:12} "
            f"expected={record['expected']:5} "
            f"pred={spatial['predicted']:5} "
            f"conf={spatial['max_confidence']:.2f} "
            f"raw_area="
            f"{spatial['raw_flooded_area_percent']:.2f}% "
            f"filtered_area="
            f"{spatial['filtered_flooded_area_percent']:.2f}%"
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    csv_path = (
        OUTPUT_DIR
        / "baseline_vs_spatial.csv"
    )

    with csv_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.writer(file)

        writer.writerow(
            [
                "filename",
                "expected",
                "baseline_predicted",
                "baseline_area",
                "baseline_detections",
                "baseline_confidence",
                "spatial_predicted",
                "spatial_raw_area",
                "spatial_filtered_area",
                "spatial_roi_area",
                "spatial_raw_detections",
                "spatial_kept_components",
                "spatial_removed_components",
                "spatial_confidence",
            ]
        )

        for record in results:
            writer.writerow(
                [
                    record["filename"],
                    record["expected"],

                    record["baseline"][
                        "predicted"
                    ],
                    record["baseline"][
                        "flooded_area_percent"
                    ],
                    record["baseline"][
                        "detections"
                    ],
                    record["baseline"][
                        "max_confidence"
                    ],

                    record["spatial"][
                        "predicted"
                    ],
                    record["spatial"][
                        "raw_flooded_area_percent"
                    ],
                    record["spatial"][
                        "filtered_flooded_area_percent"
                    ],
                    record["spatial"][
                        "roi_flooded_area_percent"
                    ],
                    record["spatial"][
                        "raw_detections"
                    ],
                    record["spatial"][
                        "kept_components"
                    ],
                    record["spatial"][
                        "removed_components"
                    ],
                    record["spatial"][
                        "max_confidence"
                    ],
                ]
            )

    json_path = (
        OUTPUT_DIR
        / "baseline_vs_spatial.json"
    )

    output_data = {
        "experiment": {
            "name": (
                "baseline_vs_spatial_pipeline"
            ),
            "dataset": (
                "regression_set"
            ),
            "final_holdout_used": False,
        },

        "baseline_metrics": {
            key: value
            for key, value
            in baseline_metrics.items()
            if key != "failures"
        },

        "spatial_metrics": {
            key: value
            for key, value
            in spatial_metrics.items()
            if key != "failures"
        },

        "results": results,
    }

    with json_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            output_data,
            file,
            indent=4,
            ensure_ascii=False,
        )

    print()
    print("RESULTADOS SALVOS")
    print("=================")
    print(csv_path)
    print(json_path)


if __name__ == "__main__":
    main()