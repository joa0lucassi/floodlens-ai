from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO


MODEL_PATH = "models/flood_segmentation/best.pt"
FRAMES_DIR = Path("data/frames")
OUTPUT_DIR = Path("data/model_tests/30epochs")

CONFIDENCE = 0.25


def calculate_flooded_area(result, image_shape):
    """
    Combina todas as máscaras detectadas e calcula
    o percentual da imagem classificado como flood.
    """

    height, width = image_shape[:2]

    combined_mask = np.zeros(
        (height, width),
        dtype=np.uint8
    )

    if result.masks is None:
        return 0.0

    for polygon in result.masks.xy:
        if len(polygon) < 3:
            continue

        points = polygon.astype(np.int32)

        cv2.fillPoly(
            combined_mask,
            [points],
            255
        )

    flooded_pixels = cv2.countNonZero(
        combined_mask
    )

    total_pixels = height * width

    flooded_percentage = (
        flooded_pixels / total_pixels
    ) * 100

    return flooded_percentage


def main():
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    model = YOLO(MODEL_PATH)

    print()
    print("FloodLens - Teste do modelo")
    print("=" * 50)

    for index in range(1, 6):

        image_path = (
            FRAMES_DIR
            / f"frame_{index}.jpg"
        )

        if not image_path.exists():
            print(
                f"Frame não encontrado: {image_path}"
            )
            continue

        image = cv2.imread(
            str(image_path)
        )

        if image is None:
            print(
                f"Erro ao abrir: {image_path}"
            )
            continue

        results = model.predict(
            source=str(image_path),
            imgsz=640,
            conf=CONFIDENCE,
            verbose=False
        )

        result = results[0]

        detection_count = (
            len(result.boxes)
            if result.boxes is not None
            else 0
        )

        if (
            result.boxes is not None
            and len(result.boxes) > 0
        ):
            confidences = (
                result.boxes.conf
                .cpu()
                .numpy()
            )

            max_confidence = float(
                np.max(confidences)
            )

        else:
            max_confidence = 0.0

        flooded_percentage = (
            calculate_flooded_area(
                result,
                image.shape
            )
        )

        annotated = result.plot()

        output_path = (
            OUTPUT_DIR
            / f"frame_{index}_prediction.jpg"
        )

        cv2.imwrite(
            str(output_path),
            annotated
        )

        print()
        print(f"Frame {index}")
        print(
            f"Detecções: {detection_count}"
        )
        print(
            f"Maior confiança: "
            f"{max_confidence:.2f}"
        )
        print(
            f"Área visual detectada: "
            f"{flooded_percentage:.2f}%"
        )
        print(
            f"Salvo em: {output_path}"
        )

    print()
    print("=" * 50)
    print("Teste concluído.")


if __name__ == "__main__":
    main()