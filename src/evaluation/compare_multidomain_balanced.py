from pathlib import Path
import csv
import json

import numpy as np
from ultralytics import YOLO


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATASET_DIR = (
    PROJECT_ROOT
    / "data"
    / "final_holdout"
    / "images"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "model_comparison"
)

MODELS = {
    "multidomain": (
        PROJECT_ROOT
        / "models"
        / "flood_segmentation"
        / "best_multidomain.pt"
    ),
    "balanced": (
        PROJECT_ROOT
        / "models"
        / "flood_segmentation"
        / "best_balanced.pt"
    ),
}

CONF_THRESHOLD = 0.25
IMAGE_SIZE = 640

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp",
}


def calculate_flood_area(result):
    if result.masks is None or result.masks.data is None:
        return 0.0

    masks = result.masks.data.cpu().numpy()

    if len(masks) == 0:
        return 0.0

    union_mask = np.any(masks > 0.5, axis=0)

    flooded_pixels = np.count_nonzero(union_mask)
    total_pixels = union_mask.size

    if total_pixels == 0:
        return 0.0

    return (flooded_pixels / total_pixels) * 100


def predict_image(model, image_path):
    result = model.predict(
        source=str(image_path),
        conf=CONF_THRESHOLD,
        imgsz=IMAGE_SIZE,
        verbose=False,
    )[0]

    detections = 0
    max_confidence = 0.0

    if result.boxes is not None:
        detections = len(result.boxes)

        if detections > 0:
            confidences = (
                result.boxes.conf
                .cpu()
                .numpy()
            )

            max_confidence = float(
                np.max(confidences)
            )

    flooded_area = calculate_flood_area(result)

    predicted = (
        "flood"
        if detections > 0
        else "dry"
    )

    return {
        "predicted": predicted,
        "detections": detections,
        "max_confidence": round(
            max_confidence,
            4,
        ),
        "flooded_area_percent": round(
            flooded_area,
            2,
        ),
    }


def calculate_metrics(records, model_name):
    tp = 0
    tn = 0
    fp = 0
    fn = 0

    failures = []

    for record in records:
        expected = record["expected"]
        predicted = record[model_name]["predicted"]

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
    print("MULTIDOMAIN VS BALANCED")
    print("=======================")
    print()

    for name, path in MODELS.items():
        if not path.exists():
            raise FileNotFoundError(
                f"Modelo não encontrado: {path}"
            )

    if not DATASET_DIR.exists():
        raise FileNotFoundError(
            f"Regression set não encontrado: "
            f"{DATASET_DIR}"
        )

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

        for image in images:
            image_records.append(
                {
                    "filename": image.name,
                    "path": image,
                    "expected": expected,
                }
            )

    print(
        f"Imagens encontradas: "
        f"{len(image_records)}"
    )
    print()

    loaded_models = {
        name: YOLO(str(path))
        for name, path in MODELS.items()
    }

    results = []

    for index, item in enumerate(
        image_records,
        start=1,
    ):
        record = {
            "filename": item["filename"],
            "expected": item["expected"],
        }

        print(
            f"[{index:02d}/{len(image_records)}] "
            f"{item['filename']}"
        )

        for model_name, model in loaded_models.items():
            prediction = predict_image(
                model,
                item["path"],
            )

            record[model_name] = prediction

            print(
                f"    {model_name:12} "
                f"pred={prediction['predicted']:5} "
                f"det={prediction['detections']} "
                f"conf={prediction['max_confidence']:.2f} "
                f"area="
                f"{prediction['flooded_area_percent']:.2f}%"
            )

        results.append(record)

    multidomain_metrics = calculate_metrics(
        results,
        "multidomain",
    )

    balanced_metrics = calculate_metrics(
        results,
        "balanced",
    )

    print()
    print("MODEL COMPARISON")
    print("================")
    print()

    print(
        f"{'Metric':<20}"
        f"{'MultiDomain':>15}"
        f"{'Balanced':>15}"
    )

    print(
        f"{'TP':<20}"
        f"{multidomain_metrics['tp']:>15}"
        f"{balanced_metrics['tp']:>15}"
    )

    print(
        f"{'TN':<20}"
        f"{multidomain_metrics['tn']:>15}"
        f"{balanced_metrics['tn']:>15}"
    )

    print(
        f"{'FP':<20}"
        f"{multidomain_metrics['fp']:>15}"
        f"{balanced_metrics['fp']:>15}"
    )

    print(
        f"{'FN':<20}"
        f"{multidomain_metrics['fn']:>15}"
        f"{balanced_metrics['fn']:>15}"
    )

    metrics_to_print = [
        ("Accuracy", "accuracy"),
        ("Precision", "precision"),
        ("Recall", "recall"),
        ("Specificity", "specificity"),
        ("F1-score", "f1"),
    ]

    for label, key in metrics_to_print:
        multi = (
            multidomain_metrics[key]
            * 100
        )

        balanced = (
            balanced_metrics[key]
            * 100
        )

        print(
            f"{label:<20}"
            f"{multi:>14.2f}%"
            f"{balanced:>14.2f}%"
        )

    print()
    print("BALANCED FAILURES")
    print("=================")

    if not balanced_metrics["failures"]:
        print(
            "Nenhum erro encontrado."
        )

    else:
        for record in balanced_metrics["failures"]:
            pred = record["balanced"]

            print(
                f"{record['filename']:12} "
                f"expected={record['expected']:5} "
                f"pred={pred['predicted']:5} "
                f"det={pred['detections']} "
                f"conf={pred['max_confidence']:.2f} "
                f"area="
                f"{pred['flooded_area_percent']:.2f}%"
            )

    print()
    print("MUDANÇAS ENTRE MODELOS")
    print("======================")

    changes = []

    for record in results:
        old_prediction = (
            record["multidomain"]["predicted"]
        )

        new_prediction = (
            record["balanced"]["predicted"]
        )

        if old_prediction != new_prediction:
            changes.append(record)

            print(
                f"{record['filename']:12} "
                f"expected={record['expected']:5} "
                f"{old_prediction:5} -> "
                f"{new_prediction:5}"
            )

    if not changes:
        print(
            "Nenhuma classificação mudou."
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    json_output = {
        "confidence_threshold": CONF_THRESHOLD,
        "image_size": IMAGE_SIZE,
        "multidomain": multidomain_metrics,
        "balanced": balanced_metrics,
        "results": results,
    }

    # Remove objetos não serializáveis
    for model_metrics in [
        json_output["multidomain"],
        json_output["balanced"],
    ]:
        model_metrics["failures"] = [
            {
                "filename": item["filename"],
                "expected": item["expected"],
                "prediction": item[
                    "balanced"
                    if model_metrics
                    is json_output["balanced"]
                    else "multidomain"
                ],
            }
            for item in model_metrics[
                "failures"
            ]
        ]

    json_path = (
        OUTPUT_DIR
        / "multidomain_vs_balanced.json"
    )

    with json_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            json_output,
            file,
            indent=4,
            ensure_ascii=False,
        )

    csv_path = (
        OUTPUT_DIR
        / "multidomain_vs_balanced.csv"
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
                "multidomain_predicted",
                "multidomain_detections",
                "multidomain_confidence",
                "multidomain_area",
                "balanced_predicted",
                "balanced_detections",
                "balanced_confidence",
                "balanced_area",
            ]
        )

        for record in results:
            writer.writerow(
                [
                    record["filename"],
                    record["expected"],
                    record["multidomain"][
                        "predicted"
                    ],
                    record["multidomain"][
                        "detections"
                    ],
                    record["multidomain"][
                        "max_confidence"
                    ],
                    record["multidomain"][
                        "flooded_area_percent"
                    ],
                    record["balanced"][
                        "predicted"
                    ],
                    record["balanced"][
                        "detections"
                    ],
                    record["balanced"][
                        "max_confidence"
                    ],
                    record["balanced"][
                        "flooded_area_percent"
                    ],
                ]
            )

    print()
    print("Resultados salvos em:")
    print(json_path)
    print(csv_path)


if __name__ == "__main__":
    main()