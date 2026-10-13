from pathlib import Path
import csv
import json

from ultralytics import YOLO


ROOT = Path(__file__).resolve().parents[2]

MODELS = {
    "multidomain": ROOT / "models" / "flood_segmentation" / "best_multidomain.pt",
    "v3": ROOT / "models" / "flood_segmentation" / "best_hardneg_v3.pt",
}

DATASET = ROOT / "data" / "regression_set" / "images"

OUTPUT = ROOT / "data" / "model_comparison" / "multidomain_vs_v3"

IMGSZ = 960
CONF = 0.25

EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def predict(model, image_path):
    result = model.predict(
        source=str(image_path),
        imgsz=IMGSZ,
        conf=CONF,
        verbose=False,
    )[0]

    detections = (
        len(result.boxes)
        if result.boxes is not None
        else 0
    )

    confidence = (
        float(result.boxes.conf.max().item())
        if detections > 0
        else 0.0
    )

    return {
        "predicted": "flood" if detections > 0 else "dry",
        "detections": detections,
        "confidence": round(confidence, 4),
    }


def calculate_metrics(records, model_name):
    tp = tn = fp = fn = 0

    for record in records:
        expected = record["expected"]
        predicted = record[model_name]["predicted"]

        if expected == "flood" and predicted == "flood":
            tp += 1
        elif expected == "dry" and predicted == "dry":
            tn += 1
        elif expected == "dry" and predicted == "flood":
            fp += 1
        elif expected == "flood" and predicted == "dry":
            fn += 1

    total = tp + tn + fp + fn

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0

    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )

    return {
        "TP": tp,
        "TN": tn,
        "FP": fp,
        "FN": fn,
        "accuracy": (tp + tn) / total if total else 0.0,
        "precision": precision,
        "recall": recall,
        "specificity": tn / (tn + fp) if tn + fp else 0.0,
        "f1": f1,
    }


def main():
    print("\nFLOODLENS AI")
    print("MULTIDOMAIN VS HARDNEG V3")
    print("=" * 65)

    for name, path in MODELS.items():
        if not path.is_file():
            raise FileNotFoundError(
                f"Modelo {name} não encontrado: {path}"
            )

    records = []

    for expected in ("flood", "dry"):
        folder = DATASET / expected

        if not folder.is_dir():
            raise FileNotFoundError(
                f"Pasta de desenvolvimento ausente: {folder}"
            )

        for image in sorted(folder.iterdir()):
            if image.is_file() and image.suffix.lower() in EXTENSIONS:
                records.append({
                    "path": image,
                    "filename": image.name,
                    "expected": expected,
                })

    if not records:
        raise RuntimeError("Nenhuma imagem encontrada.")

    print(f"Imagens de desenvolvimento: {len(records)}")
    print(f"Inference imgsz: {IMGSZ}")
    print(f"Confidence: {CONF}")
    print()

    models = {
        name: YOLO(str(path))
        for name, path in MODELS.items()
    }

    results = []

    for index, item in enumerate(records, start=1):
        row = {
            "filename": item["filename"],
            "expected": item["expected"],
        }

        for name, model in models.items():
            row[name] = predict(model, item["path"])

        results.append(row)

        old_pred = row["multidomain"]["predicted"]
        new_pred = row["v3"]["predicted"]

        marker = "CHANGED" if old_pred != new_pred else ""

        print(
            f"[{index:02d}/{len(records):02d}] "
            f"{item['filename']:<25} "
            f"expected={item['expected']:<5} "
            f"multi={old_pred:<5} "
            f"v3={new_pred:<5} "
            f"{marker}"
        )

    baseline = calculate_metrics(results, "multidomain")
    v3 = calculate_metrics(results, "v3")

    print("\nCOMPARAÇÃO FINAL — DEVELOPMENT SET")
    print("=" * 65)

    print(f"{'Métrica':<20}{'MultiDomain':>15}{'V3':>15}")

    for key in ("TP", "TN", "FP", "FN"):
        print(f"{key:<20}{baseline[key]:>15}{v3[key]:>15}")

    for key in (
        "accuracy",
        "precision",
        "recall",
        "specificity",
        "f1",
    ):
        print(
            f"{key:<20}"
            f"{baseline[key] * 100:>14.2f}%"
            f"{v3[key] * 100:>14.2f}%"
        )

    print("\nMUDANÇAS ENTRE MODELOS")
    print("=" * 65)

    changed = 0

    for row in results:
        before = row["multidomain"]["predicted"]
        after = row["v3"]["predicted"]

        if before != after:
            changed += 1

            print(
                f"{row['filename']}: "
                f"expected={row['expected']}, "
                f"{before} -> {after}"
            )

    if changed == 0:
        print("Nenhuma classificação mudou.")

    OUTPUT.mkdir(parents=True, exist_ok=True)

    report = {
        "dataset": "regression_set",
        "final_holdout_used": False,
        "imgsz": IMGSZ,
        "conf": CONF,
        "multidomain": baseline,
        "v3": v3,
        "results": results,
    }

    # Converter caminhos Path em strings, caso presentes.
    json_path = OUTPUT / "comparison.json"

    json_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    csv_path = OUTPUT / "comparison.csv"

    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        writer.writerow([
            "filename",
            "expected",
            "multidomain_predicted",
            "multidomain_confidence",
            "v3_predicted",
            "v3_confidence",
        ])

        for row in results:
            writer.writerow([
                row["filename"],
                row["expected"],
                row["multidomain"]["predicted"],
                row["multidomain"]["confidence"],
                row["v3"]["predicted"],
                row["v3"]["confidence"],
            ])

    print("\nRESULTADOS SALVOS")
    print(json_path)
    print(csv_path)


if __name__ == "__main__":
    main()