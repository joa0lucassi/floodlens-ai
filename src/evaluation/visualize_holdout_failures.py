import csv
from pathlib import Path

import cv2
from ultralytics import YOLO


MODEL_PATH = Path(
    "models/flood_segmentation/best_hardneg.pt"
)

HOLDOUT_ROOT = Path(
    "data/final_holdout/images"
)

FAILURES_CSV = Path(
    "data/final_holdout/results/"
    "final_holdout_failures.csv"
)

OUTPUT_DIR = Path(
    "data/final_holdout/results/"
    "failure_visualizations"
)


def find_image(
    filename,
    expected_label,
):
    folder = (
        HOLDOUT_ROOT
        / expected_label
    )

    image_path = (
        folder
        / filename
    )

    if image_path.exists():
        return image_path

    return None


def main():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Modelo não encontrado: "
            f"{MODEL_PATH}"
        )

    if not FAILURES_CSV.exists():
        raise FileNotFoundError(
            f"CSV não encontrado: "
            f"{FAILURES_CSV}"
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    model = YOLO(
        str(MODEL_PATH)
    )

    with open(
        FAILURES_CSV,
        "r",
        encoding="utf-8",
    ) as file:

        failures = list(
            csv.DictReader(file)
        )

    print()
    print(
        "FloodLens AI - Holdout Failure Visualization"
    )

    print("=" * 70)

    for failure in failures:
        filename = failure[
            "filename"
        ]

        expected = failure[
            "expected_label"
        ]

        predicted = failure[
            "predicted_label"
        ]

        image_path = find_image(
            filename,
            expected,
        )

        if image_path is None:
            print(
                f"Imagem não encontrada: "
                f"{filename}"
            )

            continue

        results = model.predict(
            source=str(image_path),
            imgsz=640,
            conf=0.25,
            verbose=False,
        )

        result = results[0]

        # A própria Ultralytics desenha
        # masks, boxes e labels.
        plotted = result.plot()

        title = (
            f"Expected: {expected.upper()} | "
            f"Predicted: {predicted.upper()}"
        )

        cv2.rectangle(
            plotted,
            (0, 0),
            (
                plotted.shape[1],
                55,
            ),
            (0, 0, 0),
            -1,
        )

        cv2.putText(
            plotted,
            title,
            (15, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )

        output_name = (
            f"{expected}_"
            f"{filename}"
        )

        output_path = (
            OUTPUT_DIR
            / output_name
        )

        cv2.imwrite(
            str(output_path),
            plotted,
        )

        print(
            f"{filename:<10} "
            f"| Expected: {expected:<5} "
            f"| Predicted: {predicted:<5} "
            f"| Saved: {output_path}"
        )

    print()
    print(
        "Visualizações concluídas."
    )


if __name__ == "__main__":
    main()