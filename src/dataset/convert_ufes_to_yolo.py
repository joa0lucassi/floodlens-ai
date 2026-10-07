import csv
import json
import re
import shutil
from pathlib import Path

import cv2
import numpy as np


# ============================================================
# CONFIGURAÇÃO
# ============================================================

SOURCE_ROOT = Path(
    r"C:\Users\joaol\OneDrive\Área de Trabalho"
    r"\FloodLens_UFES\extracted"
)

OUTPUT_ROOT = Path(
    "data/ufes_yolo"
)

DATASETS = [
    "Deepflood",
    "Sazara",
    "WebCOOS",
]

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}

MASK_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
}

# Remove componentes minúsculos da máscara.
# 0.0001 = 0.01% da imagem.
MIN_REGION_AREA_RATIO = 0.0001

# Simplificação do contorno.
# Quanto menor, mais fiel e mais pontos.
POLYGON_EPSILON_RATIO = 0.001


# ============================================================
# UTILIDADES
# ============================================================

def natural_key(text):
    return [
        int(part)
        if part.isdigit()
        else part.lower()
        for part in re.split(
            r"(\d+)",
            str(text),
        )
    ]


def canonical_name(stem):
    """
    Permite parear:

    image_1.jpg
    label_1.png

    e também pares que já usam o mesmo nome.
    """

    name = stem.lower()

    prefixes = [
        "image_",
        "images_",
        "img_",
        "mask_",
        "masks_",
        "label_",
        "labels_",
    ]

    for prefix in prefixes:
        if name.startswith(prefix):
            name = name[
                len(prefix):
            ]
            break

    return name


def safe_filename(text):
    text = re.sub(
        r"[^a-zA-Z0-9_-]+",
        "_",
        text,
    )

    return text.strip("_")


def imread_unicode(
    path,
    flags=cv2.IMREAD_COLOR,
):
    """
    cv2.imread pode falhar com caminhos contendo
    acentos no Windows. Este método evita o problema.
    """

    data = np.fromfile(
        str(path),
        dtype=np.uint8,
    )

    return cv2.imdecode(
        data,
        flags,
    )


def find_folder(
    root,
    folder_name,
):
    candidates = [
        folder
        for folder in root.rglob(
            folder_name
        )
        if folder.is_dir()
    ]

    if not candidates:
        return None

    return candidates[0]


def get_files(
    folder,
    extensions,
):
    return sorted(
        [
            file
            for file in folder.iterdir()
            if (
                file.is_file()
                and file.suffix.lower()
                in extensions
            )
        ],
        key=lambda file:
            natural_key(
                file.name
            ),
    )


def build_file_map(files):
    result = {}

    for file in files:
        key = canonical_name(
            file.stem
        )

        if key in result:
            raise ValueError(
                f"Chave duplicada: {key}"
            )

        result[key] = file

    return result


# ============================================================
# MÁSCARAS
# ============================================================

def prepare_binary_mask(mask):
    """
    Os datasets usam:
      0 = background
      1 = flood

    Deepflood possui 3 canais iguais.
    Sazara e WebCOOS possuem máscara 2D.
    """

    if mask.ndim == 3:
        mask = mask[
            :,
            :,
            0
        ]

    binary = (
        mask > 0
    ).astype(
        np.uint8
    )

    return binary


def mask_to_polygons(
    binary_mask,
):
    """
    Converte regiões positivas da máscara
    para polígonos compatíveis com YOLO-seg.
    """

    height, width = (
        binary_mask.shape
    )

    total_pixels = (
        height * width
    )

    minimum_area = max(
        3.0,
        total_pixels
        * MIN_REGION_AREA_RATIO,
    )

    contours, _ = cv2.findContours(
        binary_mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )

    contours = sorted(
        contours,
        key=cv2.contourArea,
        reverse=True,
    )

    polygons = []

    for contour in contours:
        area = cv2.contourArea(
            contour
        )

        if area < minimum_area:
            continue

        perimeter = cv2.arcLength(
            contour,
            closed=True,
        )

        epsilon = (
            POLYGON_EPSILON_RATIO
            * perimeter
        )

        polygon = cv2.approxPolyDP(
            contour,
            epsilon,
            closed=True,
        )

        polygon = polygon.reshape(
            -1,
            2,
        )

        if len(polygon) < 3:
            continue

        normalized = []

        for x, y in polygon:
            x_normalized = (
                float(x)
                / float(width)
            )

            y_normalized = (
                float(y)
                / float(height)
            )

            x_normalized = min(
                max(
                    x_normalized,
                    0.0,
                ),
                1.0,
            )

            y_normalized = min(
                max(
                    y_normalized,
                    0.0,
                ),
                1.0,
            )

            normalized.append(
                (
                    x_normalized,
                    y_normalized,
                )
            )

        polygons.append(
            normalized
        )

    return polygons


def polygons_to_mask(
    polygons,
    width,
    height,
):
    """
    Reconstrói uma máscara usando os polígonos
    YOLO para validar a conversão.
    """

    reconstructed = np.zeros(
        (
            height,
            width,
        ),
        dtype=np.uint8,
    )

    for polygon in polygons:
        points = []

        for x, y in polygon:
            pixel_x = round(
                x * width
            )

            pixel_y = round(
                y * height
            )

            pixel_x = min(
                max(
                    pixel_x,
                    0,
                ),
                width - 1,
            )

            pixel_y = min(
                max(
                    pixel_y,
                    0,
                ),
                height - 1,
            )

            points.append(
                [
                    pixel_x,
                    pixel_y,
                ]
            )

        points = np.array(
            points,
            dtype=np.int32,
        )

        if len(points) >= 3:
            cv2.fillPoly(
                reconstructed,
                [points],
                1,
            )

    return reconstructed


def calculate_iou(
    original,
    reconstructed,
):
    original_bool = (
        original > 0
    )

    reconstructed_bool = (
        reconstructed > 0
    )

    intersection = np.logical_and(
        original_bool,
        reconstructed_bool,
    ).sum()

    union = np.logical_or(
        original_bool,
        reconstructed_bool,
    ).sum()

    if union == 0:
        return 1.0

    return float(
        intersection / union
    )


# ============================================================
# LABEL YOLO
# ============================================================

def write_yolo_label(
    output_path,
    polygons,
):
    lines = []

    for polygon in polygons:
        coordinates = []

        for x, y in polygon:
            coordinates.append(
                f"{x:.6f}"
            )

            coordinates.append(
                f"{y:.6f}"
            )

        # Classe única:
        # 0 = flood
        line = (
            "0 "
            + " ".join(
                coordinates
            )
        )

        lines.append(
            line
        )

    output_path.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


# ============================================================
# CONVERSÃO
# ============================================================

def convert_dataset(
    dataset_name,
):
    dataset_root = (
        SOURCE_ROOT
        / dataset_name
    )

    image_dir = find_folder(
        dataset_root,
        "image",
    )

    mask_dir = find_folder(
        dataset_root,
        "mask",
    )

    if image_dir is None:
        raise FileNotFoundError(
            f"image/ não encontrada: "
            f"{dataset_name}"
        )

    if mask_dir is None:
        raise FileNotFoundError(
            f"mask/ não encontrada: "
            f"{dataset_name}"
        )

    images = get_files(
        image_dir,
        IMAGE_EXTENSIONS,
    )

    masks = get_files(
        mask_dir,
        MASK_EXTENSIONS,
    )

    image_map = build_file_map(
        images
    )

    mask_map = build_file_map(
        masks
    )

    common_keys = sorted(
        set(image_map)
        & set(mask_map),
        key=natural_key,
    )

    missing_masks = (
        set(image_map)
        - set(mask_map)
    )

    missing_images = (
        set(mask_map)
        - set(image_map)
    )

    if missing_masks:
        raise ValueError(
            f"{dataset_name}: "
            f"{len(missing_masks)} "
            f"imagens sem máscara."
        )

    if missing_images:
        raise ValueError(
            f"{dataset_name}: "
            f"{len(missing_images)} "
            f"máscaras sem imagem."
        )

    dataset_slug = (
        dataset_name.lower()
    )

    output_images = (
        OUTPUT_ROOT
        / dataset_name
        / "images"
    )

    output_labels = (
        OUTPUT_ROOT
        / dataset_name
        / "labels"
    )

    output_images.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_labels.mkdir(
        parents=True,
        exist_ok=True,
    )

    records = []

    print()
    print(
        "=" * 70
    )

    print(
        dataset_name.upper()
    )

    print(
        "=" * 70
    )

    print(
        f"Pares: {len(common_keys)}"
    )

    for index, key in enumerate(
        common_keys,
        start=1,
    ):
        image_path = (
            image_map[key]
        )

        mask_path = (
            mask_map[key]
        )

        image = imread_unicode(
            image_path,
            cv2.IMREAD_COLOR,
        )

        mask = imread_unicode(
            mask_path,
            cv2.IMREAD_UNCHANGED,
        )

        if image is None:
            raise RuntimeError(
                f"Erro ao abrir imagem: "
                f"{image_path}"
            )

        if mask is None:
            raise RuntimeError(
                f"Erro ao abrir máscara: "
                f"{mask_path}"
            )

        if (
            image.shape[:2]
            != mask.shape[:2]
        ):
            raise ValueError(
                f"Resoluções diferentes: "
                f"{image_path.name}"
            )

        binary_mask = (
            prepare_binary_mask(
                mask
            )
        )

        height, width = (
            binary_mask.shape
        )

        polygons = mask_to_polygons(
            binary_mask
        )

        reconstructed = (
            polygons_to_mask(
                polygons,
                width,
                height,
            )
        )

        conversion_iou = (
            calculate_iou(
                binary_mask,
                reconstructed,
            )
        )

        flood_percent = (
            binary_mask.mean()
            * 100
        )

        original_stem = (
            safe_filename(
                image_path.stem
            )
        )

        output_stem = (
            f"{dataset_slug}_"
            f"{original_stem}"
        )

        output_image = (
            output_images
            / (
                output_stem
                + image_path.suffix.lower()
            )
        )

        output_label = (
            output_labels
            / (
                output_stem
                + ".txt"
            )
        )

        shutil.copy2(
            image_path,
            output_image,
        )

        write_yolo_label(
            output_label,
            polygons,
        )

        records.append(
            {
                "dataset":
                    dataset_name,

                "original_image":
                    image_path.name,

                "original_mask":
                    mask_path.name,

                "output_image":
                    str(output_image),

                "output_label":
                    str(output_label),

                "width":
                    width,

                "height":
                    height,

                "flood_percent":
                    round(
                        float(
                            flood_percent
                        ),
                        4,
                    ),

                "polygon_count":
                    len(polygons),

                "conversion_iou":
                    round(
                        conversion_iou,
                        6,
                    ),
            }
        )

        if (
            index % 100 == 0
            or index == len(
                common_keys
            )
        ):
            print(
                f"{index}/"
                f"{len(common_keys)}"
                f" convertidas"
            )

    ious = [
        record[
            "conversion_iou"
        ]
        for record in records
    ]

    print()
    print(
        f"IoU média: "
        f"{np.mean(ious):.4f}"
    )

    print(
        f"IoU mínima: "
        f"{np.min(ious):.4f}"
    )

    return records


# ============================================================
# MAIN
# ============================================================

def main():
    print()
    print(
        "FloodLens AI - "
        "UFES -> YOLO11-seg"
    )

    print(
        f"Origem: {SOURCE_ROOT}"
    )

    print(
        f"Destino: {OUTPUT_ROOT}"
    )

    # Apaga apenas a saída derivada anterior.
    # Os datasets originais NÃO são modificados.
    if OUTPUT_ROOT.exists():
        shutil.rmtree(
            OUTPUT_ROOT
        )

    OUTPUT_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    all_records = []

    for dataset_name in DATASETS:
        records = convert_dataset(
            dataset_name
        )

        all_records.extend(
            records
        )

    # --------------------------------------------------------
    # Manifest
    # --------------------------------------------------------

    manifest_path = (
        OUTPUT_ROOT
        / "manifest.csv"
    )

    fieldnames = [
        "dataset",
        "original_image",
        "original_mask",
        "output_image",
        "output_label",
        "width",
        "height",
        "flood_percent",
        "polygon_count",
        "conversion_iou",
    ]

    with open(
        manifest_path,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        writer.writerows(
            all_records
        )

    # --------------------------------------------------------
    # Resumo
    # --------------------------------------------------------

    summary = {}

    for dataset_name in DATASETS:
        dataset_records = [
            record
            for record in all_records
            if (
                record["dataset"]
                == dataset_name
            )
        ]

        ious = [
            record[
                "conversion_iou"
            ]
            for record in dataset_records
        ]

        summary[
            dataset_name
        ] = {
            "samples":
                len(
                    dataset_records
                ),

            "mean_conversion_iou":
                round(
                    float(
                        np.mean(ious)
                    ),
                    6,
                ),

            "min_conversion_iou":
                round(
                    float(
                        np.min(ious)
                    ),
                    6,
                ),
        }

    all_ious = [
        record[
            "conversion_iou"
        ]
        for record in all_records
    ]

    summary[
        "total"
    ] = {
        "samples":
            len(all_records),

        "mean_conversion_iou":
            round(
                float(
                    np.mean(
                        all_ious
                    )
                ),
                6,
            ),

        "min_conversion_iou":
            round(
                float(
                    np.min(
                        all_ious
                    )
                ),
                6,
            ),
    }

    summary_path = (
        OUTPUT_ROOT
        / "conversion_summary.json"
    )

    summary_path.write_text(
        json.dumps(
            summary,
            indent=4,
        ),
        encoding="utf-8",
    )

    print()
    print(
        "=" * 70
    )

    print(
        "CONVERSÃO CONCLUÍDA"
    )

    print(
        "=" * 70
    )

    print(
        f"Total: "
        f"{len(all_records)}"
    )

    print(
        f"IoU média geral: "
        f"{np.mean(all_ious):.4f}"
    )

    print(
        f"IoU mínima geral: "
        f"{np.min(all_ious):.4f}"
    )

    print()

    print(
        f"Manifest:"
    )

    print(
        manifest_path
    )

    print()

    print(
        f"Resumo:"
    )

    print(
        summary_path
    )


if __name__ == "__main__":
    main()