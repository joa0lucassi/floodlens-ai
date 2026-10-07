from pathlib import Path
import re

import cv2
import numpy as np


BASE_DIR = Path(
    r"C:\Users\joaol\OneDrive\Área de Trabalho"
    r"\FloodLens_UFES\extracted"
)

OUTPUT_DIR = Path(
    "data/ufes_mask_checks"
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


def natural_key(text):
    return [
        int(part)
        if part.isdigit()
        else part.lower()
        for part in re.split(
            r"(\d+)",
            text,
        )
    ]


def canonical_name(stem):
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


def imread_unicode(
    path,
    flags=cv2.IMREAD_COLOR,
):
    data = np.fromfile(
        str(path),
        dtype=np.uint8,
    )

    return cv2.imdecode(
        data,
        flags,
    )


def imwrite_unicode(
    path,
    image,
):
    extension = (
        Path(path).suffix
        or ".jpg"
    )

    success, encoded = cv2.imencode(
        extension,
        image,
    )

    if not success:
        return False

    encoded.tofile(
        str(path)
    )

    return True


def find_folder(
    root,
    name,
):
    folders = [
        folder
        for folder in root.rglob(name)
        if folder.is_dir()
    ]

    if not folders:
        return None

    return folders[0]


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
            natural_key(file.name),
    )


def build_map(files):
    return {
        canonical_name(
            file.stem
        ): file
        for file in files
    }


def prepare_binary_mask(mask):
    if mask.ndim == 3:
        mask = mask[
            :,
            :,
            0
        ]

    return (
        mask > 0
    ).astype(
        np.uint8
    )


def create_overlay(
    image,
    binary_mask,
):
    overlay = image.copy()

    red_layer = np.zeros_like(
        image
    )

    red_layer[
        binary_mask == 1
    ] = (
        0,
        0,
        255,
    )

    result = cv2.addWeighted(
        image,
        0.65,
        red_layer,
        0.35,
        0,
    )

    return result


def inspect_dataset(
    dataset_name,
):
    dataset_root = (
        BASE_DIR
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

    images = get_files(
        image_dir,
        IMAGE_EXTENSIONS,
    )

    masks = get_files(
        mask_dir,
        MASK_EXTENSIONS,
    )

    image_map = build_map(
        images
    )

    mask_map = build_map(
        masks
    )

    common = sorted(
        set(image_map)
        & set(mask_map),
        key=natural_key,
    )

    indexes = [
        0,
        len(common) // 2,
        len(common) - 1,
    ]

    dataset_output = (
        OUTPUT_DIR
        / dataset_name
    )

    dataset_output.mkdir(
        parents=True,
        exist_ok=True,
    )

    print()
    print(
        "=" * 60
    )
    print(
        dataset_name.upper()
    )
    print(
        "=" * 60
    )

    for position, index in enumerate(
        indexes,
        start=1,
    ):
        key = common[index]

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

        if (
            image is None
            or mask is None
        ):
            print(
                "Erro ao abrir:",
                key,
            )
            continue

        binary_mask = (
            prepare_binary_mask(
                mask
            )
        )

        overlay = create_overlay(
            image,
            binary_mask,
        )

        flood_percent = (
            binary_mask.mean()
            * 100
        )

        cv2.putText(
            overlay,
            (
                f"Mask=1: "
                f"{flood_percent:.2f}%"
            ),
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )

        output_path = (
            dataset_output
            / f"sample_{position}.jpg"
        )

        imwrite_unicode(
            output_path,
            overlay,
        )

        print(
            f"{image_path.name}"
            f" -> "
            f"{output_path}"
        )


def main():
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print()
    print(
        "FloodLens AI - "
        "UFES Mask Visualization"
    )

    for dataset in DATASETS:
        inspect_dataset(
            dataset
        )

    print()
    print(
        "Concluído."
    )


if __name__ == "__main__":
    main()