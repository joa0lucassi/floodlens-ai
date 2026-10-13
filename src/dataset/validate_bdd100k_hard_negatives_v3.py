from pathlib import Path
import csv
import hashlib

import cv2


PROJECT_ROOT = Path(
    __file__
).resolve().parents[2]

DATASET_DIR = (
    PROJECT_ROOT
    / "data"
    / "bdd100k_hard_negatives_v3"
)

IMAGES_DIR = (
    DATASET_DIR
    / "images"
)

LABELS_DIR = (
    DATASET_DIR
    / "labels"
)

MANIFEST_PATH = (
    DATASET_DIR
    / "manifest.csv"
)

EXPECTED_COUNT = 108


def calculate_sha256(
    file_path,
):
    digest = hashlib.sha256()

    with open(
        file_path,
        "rb",
    ) as file:

        while True:
            chunk = file.read(
                1024 * 1024
            )

            if not chunk:
                break

            digest.update(
                chunk
            )

    return digest.hexdigest()


def load_manifest():
    with open(
        MANIFEST_PATH,
        "r",
        encoding="utf-8",
        newline="",
    ) as file:

        return list(
            csv.DictReader(
                file
            )
        )


def main():
    print()
    print(
        "BDD100K HARD NEGATIVES V3"
    )
    print(
        "FINAL VALIDATION"
    )
    print("=" * 60)

    errors = []

    if not IMAGES_DIR.exists():
        errors.append(
            "Images directory missing."
        )

    if not LABELS_DIR.exists():
        errors.append(
            "Labels directory missing."
        )

    if not MANIFEST_PATH.exists():
        errors.append(
            "Manifest missing."
        )

    if errors:
        for error in errors:
            print(
                f"ERROR: {error}"
            )

        raise RuntimeError(
            "Dataset structure invalid."
        )

    images = sorted(
        path
        for path in IMAGES_DIR.iterdir()
        if path.is_file()
    )

    labels = sorted(
        LABELS_DIR.glob(
            "*.txt"
        )
    )

    manifest = (
        load_manifest()
    )

    print(
        f"Images:   {len(images)}"
    )

    print(
        f"Labels:   {len(labels)}"
    )

    print(
        f"Manifest: {len(manifest)} rows"
    )

    if len(images) != EXPECTED_COUNT:
        errors.append(
            "Unexpected image count."
        )

    if len(labels) != EXPECTED_COUNT:
        errors.append(
            "Unexpected label count."
        )

    if len(manifest) != EXPECTED_COUNT:
        errors.append(
            "Unexpected manifest count."
        )

    image_stems = {
        path.stem
        for path in images
    }

    label_stems = {
        path.stem
        for path in labels
    }

    missing_labels = (
        image_stems
        - label_stems
    )

    extra_labels = (
        label_stems
        - image_stems
    )

    if missing_labels:
        errors.append(
            f"Missing labels: "
            f"{len(missing_labels)}"
        )

    if extra_labels:
        errors.append(
            f"Extra labels: "
            f"{len(extra_labels)}"
        )

    non_empty_labels = []

    for label_path in labels:

        if (
            label_path.stat().st_size
            != 0
        ):
            non_empty_labels.append(
                label_path.name
            )

    if non_empty_labels:
        errors.append(
            "Non-empty negative labels: "
            f"{len(non_empty_labels)}"
        )

    unreadable_images = []

    dimensions = []

    hashes = {}

    duplicate_hashes = []

    for index, image_path in enumerate(
        images,
        start=1,
    ):
        image = cv2.imread(
            str(image_path)
        )

        if image is None:
            unreadable_images.append(
                image_path.name
            )

            continue

        height, width = (
            image.shape[:2]
        )

        dimensions.append(
            (
                width,
                height,
            )
        )

        sha256 = calculate_sha256(
            image_path
        )

        if sha256 in hashes:
            duplicate_hashes.append(
                (
                    hashes[sha256],
                    image_path.name,
                )
            )

        else:
            hashes[sha256] = (
                image_path.name
            )

        print(
            f"[{index:03d}/"
            f"{len(images):03d}] "
            f"OK  "
            f"{image_path.name}  "
            f"{width}x{height}"
        )

    if unreadable_images:
        errors.append(
            "Unreadable images: "
            f"{len(unreadable_images)}"
        )

    if duplicate_hashes:
        errors.append(
            "Exact duplicate images: "
            f"{len(duplicate_hashes)}"
        )

    manifest_filenames = {
        row[
            "output_filename"
        ]
        for row in manifest
    }

    actual_filenames = {
        path.name
        for path in images
    }

    missing_from_manifest = (
        actual_filenames
        - manifest_filenames
    )

    missing_from_folder = (
        manifest_filenames
        - actual_filenames
    )

    if missing_from_manifest:
        errors.append(
            "Images missing from manifest: "
            f"{len(missing_from_manifest)}"
        )

    if missing_from_folder:
        errors.append(
            "Manifest entries without image: "
            f"{len(missing_from_folder)}"
        )

    groups = {}

    for row in manifest:
        group = row[
            "group"
        ]

        groups[group] = (
            groups.get(
                group,
                0,
            )
            + 1
        )

    print()
    print("=" * 60)
    print("GROUP DISTRIBUTION")
    print("=" * 60)

    for group in sorted(
        groups
    ):
        print(
            f"{group:<15} "
            f"{groups[group]}"
        )

    print()
    print("=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)

    print(
        f"Readable images: "
        f"{len(images) - len(unreadable_images)}"
        f"/{len(images)}"
    )

    print(
        f"Empty YOLO labels: "
        f"{len(labels) - len(non_empty_labels)}"
        f"/{len(labels)}"
    )

    print(
        f"Unique SHA-256: "
        f"{len(hashes)}"
        f"/{len(images)}"
    )

    print(
        f"Manifest rows: "
        f"{len(manifest)}"
    )

    print()

    if errors:
        print(
            "STATUS: FAILED"
        )

        print()

        for error in errors:
            print(
                f"- {error}"
            )

        raise RuntimeError(
            "Dataset validation failed."
        )

    print(
        "STATUS: PASSED"
    )

    print()
    print(
        "Dataset is ready for the "
        "next preparation stage."
    )

    print("=" * 60)


if __name__ == "__main__":
    main()