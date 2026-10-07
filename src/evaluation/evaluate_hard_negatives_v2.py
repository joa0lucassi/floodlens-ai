from pathlib import Path
import csv
import json

import cv2
import numpy as np
from ultralytics import YOLO


PROJECT_ROOT = Path(__file__).resolve().parents[2]

MODEL_PATH = PROJECT_ROOT / "models" / "flood_segmentation" / "best_multidomain.pt"

IMAGES_DIR = (
    PROJECT_ROOT
    / "data"
    / "negative_training_v2"
    / "images"
    / "train"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "negative_training_v2"
    / "model_mining"
)

FALSE_POSITIVE_DIR = OUTPUT_DIR / "false_positives"

CONF_THRESHOLD = 0.25
IMAGE_SIZE = 640


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


def main():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Modelo não encontrado: {MODEL_PATH}"
        )

    if not IMAGES_DIR.exists():
        raise FileNotFoundError(
            f"Pasta de imagens não encontrada: {IMAGES_DIR}"
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FALSE_POSITIVE_DIR.mkdir(parents=True, exist_ok=True)

    print()
    print("FLOODLENS AI - HARD NEGATIVE MINING V2")
    print("======================================")
    print(f"Modelo: {MODEL_PATH.name}")
    print(f"Conf threshold: {CONF_THRESHOLD}")
    print()

    model = YOLO(str(MODEL_PATH))

    image_paths = sorted(IMAGES_DIR.rglob("*.jpg"))

    if not image_paths:
        raise RuntimeError("Nenhuma imagem JPG encontrada.")

    results_data = []

    category_stats = {}

    for index, image_path in enumerate(image_paths, start=1):
        category = image_path.parent.name

        if category not in category_stats:
            category_stats[category] = {
                "total": 0,
                "false_positives": 0,
            }

        category_stats[category]["total"] += 1

        prediction = model.predict(
            source=str(image_path),
            conf=CONF_THRESHOLD,
            imgsz=IMAGE_SIZE,
            verbose=False,
        )[0]

        detections = 0
        max_confidence = 0.0

        if prediction.boxes is not None:
            detections = len(prediction.boxes)

            if detections > 0:
                confidences = prediction.boxes.conf.cpu().numpy()
                max_confidence = float(np.max(confidences))

        flooded_area = calculate_flood_area(prediction)

        is_false_positive = detections > 0

        if is_false_positive:
            category_stats[category]["false_positives"] += 1

            annotated = prediction.plot()

            output_name = f"{category}__{image_path.name}"

            cv2.imwrite(
                str(FALSE_POSITIVE_DIR / output_name),
                annotated,
            )

        results_data.append(
            {
                "filename": image_path.name,
                "category": category,
                "expected": "dry",
                "predicted": "flood" if is_false_positive else "dry",
                "detections": detections,
                "max_confidence": round(max_confidence, 4),
                "flooded_area_percent": round(flooded_area, 2),
            }
        )

        status = "FP" if is_false_positive else "OK"

        print(
            f"[{index:02d}/{len(image_paths)}] "
            f"{category:20} "
            f"{image_path.name:25} "
            f"{status:3} "
            f"det={detections} "
            f"conf={max_confidence:.2f} "
            f"area={flooded_area:.2f}%"
        )

    csv_path = OUTPUT_DIR / "hard_negative_results.csv"

    with csv_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "filename",
                "category",
                "expected",
                "predicted",
                "detections",
                "max_confidence",
                "flooded_area_percent",
            ],
        )

        writer.writeheader()
        writer.writerows(results_data)

    total_images = len(results_data)

    total_false_positives = sum(
        1
        for item in results_data
        if item["predicted"] == "flood"
    )

    total_correct = total_images - total_false_positives

    specificity = (
        total_correct / total_images
        if total_images > 0
        else 0
    )

    false_positive_rate = (
        total_false_positives / total_images
        if total_images > 0
        else 0
    )

    false_positives_sorted = sorted(
        [
            item
            for item in results_data
            if item["predicted"] == "flood"
        ],
        key=lambda item: item["max_confidence"],
        reverse=True,
    )

    summary = {
        "model": MODEL_PATH.name,
        "confidence_threshold": CONF_THRESHOLD,
        "total_images": total_images,
        "true_negatives": total_correct,
        "false_positives": total_false_positives,
        "specificity": round(specificity, 4),
        "false_positive_rate": round(
            false_positive_rate,
            4,
        ),
        "categories": category_stats,
        "false_positive_cases": false_positives_sorted,
    }

    json_path = OUTPUT_DIR / "hard_negative_summary.json"

    with json_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            summary,
            file,
            indent=4,
            ensure_ascii=False,
        )

    print()
    print("RESULTADO")
    print("=========")
    print(f"Imagens:          {total_images}")
    print(f"True negatives:   {total_correct}")
    print(f"False positives:  {total_false_positives}")
    print(f"Specificity:      {specificity * 100:.2f}%")
    print(f"FP rate:          {false_positive_rate * 100:.2f}%")

    print()
    print("POR CATEGORIA")
    print("=============")

    for category, stats in category_stats.items():
        total = stats["total"]
        fp = stats["false_positives"]
        tn = total - fp

        print(
            f"{category:20} "
            f"total={total:2} "
            f"TN={tn:2} "
            f"FP={fp:2}"
        )

    print()
    print("FALSOS POSITIVOS")
    print("================")

    if not false_positives_sorted:
        print("Nenhum falso positivo encontrado.")
    else:
        for item in false_positives_sorted:
            print(
                f"{item['category']:20} "
                f"{item['filename']:25} "
                f"conf={item['max_confidence']:.2f} "
                f"area={item['flooded_area_percent']:.2f}% "
                f"det={item['detections']}"
            )

    print()
    print(f"CSV:  {csv_path}")
    print(f"JSON: {json_path}")
    print(f"Visualizações: {FALSE_POSITIVE_DIR}")


if __name__ == "__main__":
    main()