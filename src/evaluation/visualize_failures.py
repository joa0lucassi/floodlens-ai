from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO


MODEL_PATH = Path(
    "models/flood_segmentation/best_hardneg.pt"
)

DRY_IMAGES_DIR = Path(
    "data/evaluation/images/dry"
)

OUTPUT_DIR = Path(
    "data/evaluation/results/failure_visualizations"
)

FAILURE_IMAGES = [
    "05.jpg",
    "06.jpg",
    "07.jpg",
    "10.jpg",
]


def create_overlay(
    image,
    masks,
):
    overlay = image.copy()

    if masks is None:
        return overlay

    height, width = image.shape[:2]

    combined_mask = np.zeros(
        (height, width),
        dtype=np.uint8,
    )

    for mask_tensor in masks.data:
        mask = (
            mask_tensor
            .cpu()
            .numpy()
        )

        mask = cv2.resize(
            mask,
            (width, height),
            interpolation=cv2.INTER_NEAREST,
        )

        combined_mask[
            mask > 0.5
        ] = 1

    mask_layer = np.zeros_like(
        image
    )

    mask_layer[
        combined_mask == 1
    ] = (
        0,
        0,
        255,
    )

    overlay = cv2.addWeighted(
        image,
        0.65,
        mask_layer,
        0.35,
        0,
    )

    return overlay


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

    model = YOLO(
        str(MODEL_PATH)
    )

    print()
    print(
        "FloodLens AI - Failure Visualization"
    )

    print("=" * 60)

    for filename in FAILURE_IMAGES:
        image_path = (
            DRY_IMAGES_DIR
            / filename
        )

        if not image_path.exists():
            print(
                f"Imagem não encontrada: "
                f"{filename}"
            )

            continue

        image = cv2.imread(
            str(image_path)
        )

        if image is None:
            print(
                f"Erro ao abrir: "
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

        overlay = create_overlay(
            image,
            result.masks,
        )

        detections = len(
            result.boxes
        )

        max_confidence = 0.0

        if detections > 0:
            max_confidence = float(
                result.boxes.conf.max()
            )

        cv2.putText(
            overlay,
            (
                f"False Positive | "
                f"Conf: {max_confidence:.2f}"
            ),
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )

        output_path = (
            OUTPUT_DIR
            / filename
        )

        cv2.imwrite(
            str(output_path),
            overlay,
        )

        print(
            f"{filename} -> "
            f"{output_path}"
        )

    print()
    print(
        "Visualizações concluídas."
    )


if __name__ == "__main__":
    main()