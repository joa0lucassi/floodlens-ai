from pathlib import Path

import cv2
import numpy as np


DATASET_DIR = Path("data/datasets/rualivreia")
IMAGES_DIR = DATASET_DIR / "train" / "images"
LABELS_DIR = DATASET_DIR / "train" / "labels"

OUTPUT_DIR = Path("data/label_inspection")

NUMBER_OF_IMAGES = 10

IMAGE_EXTENSIONS = [
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
]


def find_image(label_path: Path):
    """
    Procura a imagem correspondente ao arquivo de anotação.
    """

    for extension in IMAGE_EXTENSIONS:
        image_path = IMAGES_DIR / f"{label_path.stem}{extension}"

        if image_path.exists():
            return image_path

    return None


def load_polygons(label_path: Path, width: int, height: int):
    """
    Lê anotações YOLO segmentation.

    Formato:
    class_id x1 y1 x2 y2 x3 y3 ...
    """

    polygons = []

    with open(label_path, "r", encoding="utf-8") as file:
        for line in file:
            values = line.strip().split()

            if len(values) < 7:
                continue

            class_id = int(float(values[0]))

            coordinates = list(map(float, values[1:]))

            points = []

            for index in range(0, len(coordinates), 2):
                x_normalized = coordinates[index]
                y_normalized = coordinates[index + 1]

                x = int(x_normalized * width)
                y = int(y_normalized * height)

                points.append([x, y])

            polygon = np.array(points, dtype=np.int32)

            polygons.append(
                {
                    "class_id": class_id,
                    "polygon": polygon,
                }
            )

    return polygons


def draw_annotations(image, polygons):
    """
    Desenha as máscaras originais do dataset sobre a imagem.
    """

    overlay = image.copy()

    for item in polygons:
        polygon = item["polygon"]

        cv2.fillPoly(
            overlay,
            [polygon],
            (255, 0, 0),
        )

        cv2.polylines(
            image,
            [polygon],
            isClosed=True,
            color=(255, 255, 255),
            thickness=2,
        )

    result = cv2.addWeighted(
        overlay,
        0.45,
        image,
        0.55,
        0,
    )

    return result


def main():
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    label_files = sorted(
        LABELS_DIR.glob("*.txt")
    )

    if not label_files:
        print(
            "Erro: nenhuma anotação encontrada em "
            f"{LABELS_DIR}"
        )
        return

    processed = 0

    for label_path in label_files:
        if processed >= NUMBER_OF_IMAGES:
            break

        image_path = find_image(label_path)

        if image_path is None:
            continue

        image = cv2.imread(
            str(image_path)
        )

        if image is None:
            continue

        height, width = image.shape[:2]

        polygons = load_polygons(
            label_path,
            width,
            height,
        )

        if not polygons:
            continue

        annotated = draw_annotations(
            image,
            polygons,
        )

        output_path = (
            OUTPUT_DIR
            / f"annotated_{processed + 1}.jpg"
        )

        cv2.imwrite(
            str(output_path),
            annotated,
        )

        print(
            f"Salvo: {output_path}"
        )

        processed += 1

    print()
    print(
        f"Concluído: {processed} imagens anotadas geradas."
    )


if __name__ == "__main__":
    main()