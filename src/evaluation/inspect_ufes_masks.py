from pathlib import Path
import re

import cv2
import numpy as np


BASE_DIR = Path(
    r"C:\Users\joaol\OneDrive\Área de Trabalho"
    r"\FloodLens_UFES\extracted"
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


def imread_unicode(
    path: Path,
    flags=cv2.IMREAD_COLOR,
):
    """
    Lê imagens com segurança em caminhos
    Windows que possuem acentos/caracteres Unicode.
    """

    try:
        data = np.fromfile(
            str(path),
            dtype=np.uint8,
        )

        image = cv2.imdecode(
            data,
            flags,
        )

        return image

    except Exception as error:
        print(
            f"Erro ao abrir {path}: "
            f"{error}"
        )

        return None


def find_folder(
    dataset_root: Path,
    folder_name: str,
):
    candidates = [
        path
        for path in dataset_root.rglob(
            folder_name
        )
        if path.is_dir()
    ]

    if not candidates:
        return None

    return candidates[0]


def get_files(
    folder: Path,
    extensions: set,
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
        key=lambda path: natural_key(
            path.name
        ),
    )


def natural_key(
    text: str,
):
    return [
        int(part)
        if part.isdigit()
        else part.lower()
        for part in re.split(
            r"(\d+)",
            text,
        )
    ]


def canonical_name(
    stem: str,
):
    """
    Normaliza nomes para permitir pares como:

    image_1.jpg
    mask_1.png

    ou:

    Flood_1.jpg
    Flood_1.png
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
        "annotation_",
        "annotations_",
    ]

    for prefix in prefixes:
        if name.startswith(prefix):
            name = name[
                len(prefix):
            ]

            break

    return name


def build_file_map(
    files,
):
    result = {}

    for file in files:
        key = canonical_name(
            file.stem
        )

        result[key] = file

    return result


def print_mask_values(
    mask: np.ndarray,
):
    print(
        f"Mask shape: {mask.shape}"
    )

    print(
        f"Mask dtype: {mask.dtype}"
    )

    if len(mask.shape) == 2:
        values, counts = np.unique(
            mask,
            return_counts=True,
        )

        print(
            f"Valores únicos: "
            f"{len(values)}"
        )

        for value, count in zip(
            values[:20],
            counts[:20],
        ):
            percentage = (
                count
                / mask.size
                * 100
            )

            print(
                f"  valor={value:<4} "
                f"pixels={count:<10} "
                f"({percentage:.2f}%)"
            )

        if len(values) > 20:
            print(
                f"  ... "
                f"{len(values) - 20} "
                f"valores adicionais"
            )

    elif len(mask.shape) == 3:
        pixels = mask.reshape(
            -1,
            mask.shape[2],
        )

        colors, counts = np.unique(
            pixels,
            axis=0,
            return_counts=True,
        )

        total_pixels = (
            pixels.shape[0]
        )

        print(
            f"Cores únicas: "
            f"{len(colors)}"
        )

        for color, count in zip(
            colors[:20],
            counts[:20],
        ):
            percentage = (
                count
                / total_pixels
                * 100
            )

            print(
                f"  cor={color.tolist()} "
                f"pixels={count:<10} "
                f"({percentage:.2f}%)"
            )

        if len(colors) > 20:
            print(
                f"  ... "
                f"{len(colors) - 20} "
                f"cores adicionais"
            )


def inspect_dataset(
    dataset_name: str,
):
    dataset_root = (
        BASE_DIR
        / dataset_name
    )

    print()
    print(
        "=" * 75
    )

    print(
        dataset_name.upper()
    )

    print(
        "=" * 75
    )

    if not dataset_root.exists():
        print(
            "Dataset não encontrado:"
        )

        print(
            dataset_root
        )

        return

    image_dir = find_folder(
        dataset_root,
        "image",
    )

    mask_dir = find_folder(
        dataset_root,
        "mask",
    )

    if image_dir is None:
        print(
            "Pasta image não encontrada."
        )

        return

    if mask_dir is None:
        print(
            "Pasta mask não encontrada."
        )

        return

    images = get_files(
        image_dir,
        IMAGE_EXTENSIONS,
    )

    masks = get_files(
        mask_dir,
        MASK_EXTENSIONS,
    )

    print(
        f"Image directory: "
        f"{image_dir}"
    )

    print(
        f"Mask directory:  "
        f"{mask_dir}"
    )

    print()

    print(
        f"Imagens: "
        f"{len(images)}"
    )

    print(
        f"Masks:   "
        f"{len(masks)}"
    )

    image_map = build_file_map(
        images
    )

    mask_map = build_file_map(
        masks
    )

    common_names = sorted(
        set(image_map)
        & set(mask_map),
        key=natural_key,
    )

    missing_masks = sorted(
        set(image_map)
        - set(mask_map),
        key=natural_key,
    )

    missing_images = sorted(
        set(mask_map)
        - set(image_map),
        key=natural_key,
    )

    print(
        f"Pares imagem/mask: "
        f"{len(common_names)}"
    )

    print(
        f"Imagens sem mask: "
        f"{len(missing_masks)}"
    )

    print(
        f"Masks sem imagem: "
        f"{len(missing_images)}"
    )

    if not common_names:
        print()

        print(
            "Nenhum par encontrado "
            "mesmo após normalização."
        )

        print()

        print(
            "Primeiras imagens:"
        )

        for file in images[:10]:
            print(
                " ",
                file.name,
            )

        print()

        print(
            "Primeiras masks:"
        )

        for file in masks[:10]:
            print(
                " ",
                file.name,
            )

        return

    indexes = {
        0,
        len(common_names) // 2,
        len(common_names) - 1,
    }

    sample_names = [
        common_names[index]
        for index in sorted(
            indexes
        )
    ]

    for sample_number, name in enumerate(
        sample_names,
        start=1,
    ):
        image_path = (
            image_map[name]
        )

        mask_path = (
            mask_map[name]
        )

        image = imread_unicode(
            image_path,
            cv2.IMREAD_COLOR,
        )

        mask = imread_unicode(
            mask_path,
            cv2.IMREAD_UNCHANGED,
        )

        print()
        print(
            "-" * 75
        )

        print(
            f"AMOSTRA "
            f"{sample_number}"
        )

        print(
            "-" * 75
        )

        print(
            f"Image: "
            f"{image_path.name}"
        )

        print(
            f"Mask:  "
            f"{mask_path.name}"
        )

        if image is None:
            print(
                "Erro ao abrir imagem."
            )

            continue

        if mask is None:
            print(
                "Erro ao abrir mask."
            )

            continue

        print(
            f"Image shape: "
            f"{image.shape}"
        )

        same_resolution = (
            image.shape[:2]
            == mask.shape[:2]
        )

        print(
            "Mesma resolução: "
            f"{same_resolution}"
        )

        print_mask_values(
            mask
        )


def main():
    print()
    print(
        "FloodLens AI - "
        "UFES Mask Inspection"
    )

    print(
        f"Base: {BASE_DIR}"
    )

    for dataset in DATASETS:
        inspect_dataset(
            dataset
        )


if __name__ == "__main__":
    main()