from pathlib import Path
import csv
import json

import numpy as np
from ultralytics import YOLO


PROJECT_ROOT = Path(__file__).resolve().parents[2]

MODEL_PATH = (
    PROJECT_ROOT
    / "models"
    / "flood_segmentation"
    / "best_multidomain.pt"
)

HOLDOUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "final_holdout"
    / "images"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "final_holdout"
    / "results"
)

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


def calculate_metrics(records):
    tp = 0
    tn = 0
    fp = 0
    fn = 0

    failures = []

    for record in records:
        expected = record["expected"]
        predicted = record["predicted"]

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
    print("FINAL INDEPENDENT EVALUATION")
    print("============================")
    print()

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Modelo não encontrado: {MODEL_PATH}"
        )

    if not HOLDOUT_DIR.exists():
        raise FileNotFoundError(
            f"Holdout não encontrado: {HOLDOUT_DIR}"
        )

    flood_dir = HOLDOUT_DIR / "flood"
    dry_dir = HOLDOUT_DIR / "dry"

    if not flood_dir.exists():
        raise FileNotFoundError(
            f"Pasta flood não encontrada: {flood_dir}"
        )

    if not dry_dir.exists():
        raise FileNotFoundError(
            f"Pasta dry não encontrada: {dry_dir}"
        )

    flood_images = sorted(
        [
            path
            for path in flood_dir.iterdir()
            if path.is_file()
            and path.suffix.lower()
            in IMAGE_EXTENSIONS
        ]
    )

    dry_images = sorted(
        [
            path
            for path in dry_dir.iterdir()
            if path.is_file()
            and path.suffix.lower()
            in IMAGE_EXTENSIONS
        ]
    )

    print(f"Flood images: {len(flood_images)}")
    print(f"Dry images:   {len(dry_images)}")
    print(f"Total:        {len(flood_images) + len(dry_images)}")
    print()

    if len(flood_images) != 20:
        raise RuntimeError(
            f"Esperado 20 flood, encontrado {len(flood_images)}."
        )

    if len(dry_images) != 20:
        raise RuntimeError(
            f"Esperado 20 dry, encontrado {len(dry_images)}."
        )

    print("Modelo:")
    print(MODEL_PATH)
    print()

    print(f"Confidence threshold: {CONF_THRESHOLD}")
    print(f"Image size:           {IMAGE_SIZE}")
    print()

    model = YOLO(str(MODEL_PATH))

    image_records = []

    for image_path in flood_images:
        image_records.append(
            {
                "path": image_path,
                "filename": image_path.name,
                "expected": "flood",
            }
        )

    for image_path in dry_images:
        image_records.append(
            {
                "path": image_path,
                "filename": image_path.name,
                "expected": "dry",
            }
        )

    results = []

    print("EXECUTANDO AVALIAÇÃO")
    print("====================")
    print()

    for index, item in enumerate(
        image_records,
        start=1,
    ):
        prediction = predict_image(
            model,
            item["path"],
        )

        record = {
            "filename": item["filename"],
            "expected": item["expected"],
            "predicted": prediction["predicted"],
            "detections": prediction["detections"],
            "max_confidence": prediction["max_confidence"],
            "flooded_area_percent": prediction[
                "flooded_area_percent"
            ],
        }

        results.append(record)

        is_correct = (
            record["expected"]
            == record["predicted"]
        )

        status = "OK" if is_correct else "ERRO"

        print(
            f"[{index:02d}/40] "
            f"{record['filename']:15} "
            f"expected={record['expected']:5} "
            f"pred={record['predicted']:5} "
            f"{status:4} "
            f"det={record['detections']} "
            f"conf={record['max_confidence']:.2f} "
            f"area={record['flooded_area_percent']:.2f}%"
        )

    metrics = calculate_metrics(results)

    print()
    print("FINAL HOLDOUT RESULTS")
    print("=====================")
    print()

    print(f"TP: {metrics['tp']}")
    print(f"TN: {metrics['tn']}")
    print(f"FP: {metrics['fp']}")
    print(f"FN: {metrics['fn']}")
    print()

    print(
        f"Accuracy:    "
        f"{metrics['accuracy'] * 100:.2f}%"
    )

    print(
        f"Precision:   "
        f"{metrics['precision'] * 100:.2f}%"
    )

    print(
        f"Recall:      "
        f"{metrics['recall'] * 100:.2f}%"
    )

    print(
        f"Specificity: "
        f"{metrics['specificity'] * 100:.2f}%"
    )

    print(
        f"F1-score:    "
        f"{metrics['f1'] * 100:.2f}%"
    )

    print()
    print("FAILURES")
    print("========")

    if not metrics["failures"]:
        print("Nenhum erro encontrado.")

    else:
        for failure in metrics["failures"]:
            print(
                f"{failure['filename']:15} "
                f"expected={failure['expected']:5} "
                f"pred={failure['predicted']:5} "
                f"det={failure['detections']} "
                f"conf={failure['max_confidence']:.2f} "
                f"area="
                f"{failure['flooded_area_percent']:.2f}%"
            )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    csv_path = (
        OUTPUT_DIR
        / "final_independent_evaluation.csv"
    )

    with csv_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "filename",
                "expected",
                "predicted",
                "detections",
                "max_confidence",
                "flooded_area_percent",
            ],
        )

        writer.writeheader()
        writer.writerows(results)

    json_path = (
        OUTPUT_DIR
        / "final_independent_evaluation.json"
    )

    json_data = {
        "model": MODEL_PATH.name,
        "confidence_threshold": CONF_THRESHOLD,
        "image_size": IMAGE_SIZE,
        "dataset": {
            "total": 40,
            "flood": 20,
            "dry": 20,
        },
        "metrics": {
            "tp": metrics["tp"],
            "tn": metrics["tn"],
            "fp": metrics["fp"],
            "fn": metrics["fn"],
            "accuracy": round(
                metrics["accuracy"],
                4,
            ),
            "precision": round(
                metrics["precision"],
                4,
            ),
            "recall": round(
                metrics["recall"],
                4,
            ),
            "specificity": round(
                metrics["specificity"],
                4,
            ),
            "f1": round(
                metrics["f1"],
                4,
            ),
        },
        "failures": metrics["failures"],
        "results": results,
    }

    with json_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            json_data,
            file,
            indent=4,
            ensure_ascii=False,
        )

    print()
    print("RESULTADOS SALVOS")
    print("=================")
    print(csv_path)
    print(json_path)

    print()
    print(
        "IMPORTANTE: este holdout está congelado. "
        "Não use estes resultados para retreinar "
        "ou ajustar thresholds."
    )


if __name__ == "__main__":
    main()