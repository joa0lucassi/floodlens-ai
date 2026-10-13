from pathlib import Path
import shutil
import yaml


PROJECT_ROOT = Path(
    __file__
).resolve().parents[2]

SOURCE_DATASET = (
    PROJECT_ROOT
    / "data"
    / "combined_flood_dataset"
)

BDD_NEGATIVES = (
    PROJECT_ROOT
    / "data"
    / "bdd100k_hard_negatives_v3"
)

OUTPUT_DATASET = (
    PROJECT_ROOT
    / "data"
    / "flood_dataset_v3"
)


EXPECTED_BASE_TRAIN = 2346
EXPECTED_BASE_VALID = 134
EXPECTED_BDD_NEGATIVES = 108

EXPECTED_FINAL_TRAIN = (
    EXPECTED_BASE_TRAIN
    + EXPECTED_BDD_NEGATIVES
)

EXPECTED_FINAL_VALID = (
    EXPECTED_BASE_VALID
)


IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".bmp",
}


def get_images(directory):
    return sorted(
        path
        for path in directory.iterdir()
        if (
            path.is_file()
            and path.suffix.lower()
            in IMAGE_EXTENSIONS
        )
    )


def validate_source_dataset():
    print()
    print("VALIDATING BASE DATASET")
    print("=" * 60)

    train_images = (
        SOURCE_DATASET
        / "train"
        / "images"
    )

    train_labels = (
        SOURCE_DATASET
        / "train"
        / "labels"
    )

    valid_images = (
        SOURCE_DATASET
        / "valid"
        / "images"
    )

    valid_labels = (
        SOURCE_DATASET
        / "valid"
        / "labels"
    )

    for directory in [
        train_images,
        train_labels,
        valid_images,
        valid_labels,
    ]:
        if not directory.exists():
            raise FileNotFoundError(
                f"Missing directory: {directory}"
            )

    train_image_count = len(
        get_images(
            train_images
        )
    )

    train_label_count = len(
        list(
            train_labels.glob("*.txt")
        )
    )

    valid_image_count = len(
        get_images(
            valid_images
        )
    )

    valid_label_count = len(
        list(
            valid_labels.glob("*.txt")
        )
    )

    print(
        f"Train images: {train_image_count}"
    )

    print(
        f"Train labels: {train_label_count}"
    )

    print(
        f"Valid images: {valid_image_count}"
    )

    print(
        f"Valid labels: {valid_label_count}"
    )

    if (
        train_image_count
        != EXPECTED_BASE_TRAIN
    ):
        raise RuntimeError(
            "Unexpected number of base "
            "training images."
        )

    if (
        train_label_count
        != EXPECTED_BASE_TRAIN
    ):
        raise RuntimeError(
            "Unexpected number of base "
            "training labels."
        )

    if (
        valid_image_count
        != EXPECTED_BASE_VALID
    ):
        raise RuntimeError(
            "Unexpected number of base "
            "validation images."
        )

    if (
        valid_label_count
        != EXPECTED_BASE_VALID
    ):
        raise RuntimeError(
            "Unexpected number of base "
            "validation labels."
        )


def validate_bdd_negatives():
    print()
    print("VALIDATING BDD100K HARD NEGATIVES")
    print("=" * 60)

    images_dir = (
        BDD_NEGATIVES
        / "images"
    )

    labels_dir = (
        BDD_NEGATIVES
        / "labels"
    )

    if not images_dir.exists():
        raise FileNotFoundError(
            images_dir
        )

    if not labels_dir.exists():
        raise FileNotFoundError(
            labels_dir
        )

    images = get_images(
        images_dir
    )

    labels = list(
        labels_dir.glob("*.txt")
    )

    print(
        f"Images: {len(images)}"
    )

    print(
        f"Labels: {len(labels)}"
    )

    if len(images) != EXPECTED_BDD_NEGATIVES:
        raise RuntimeError(
            "Unexpected BDD100K "
            "image count."
        )

    if len(labels) != EXPECTED_BDD_NEGATIVES:
        raise RuntimeError(
            "Unexpected BDD100K "
            "label count."
        )

    non_empty_labels = [
        label
        for label in labels
        if label.stat().st_size != 0
    ]

    if non_empty_labels:
        raise RuntimeError(
            "BDD100K negative labels "
            "must be empty."
        )

    for image_path in images:
        label_path = (
            labels_dir
            / f"{image_path.stem}.txt"
        )

        if not label_path.exists():
            raise RuntimeError(
                f"Missing label for: "
                f"{image_path.name}"
            )


def copy_base_dataset():
    print()
    print("COPYING BASE DATASET")
    print("=" * 60)

    if OUTPUT_DATASET.exists():
        print(
            "Removing previous V3 dataset:"
        )

        print(
            OUTPUT_DATASET
        )

        shutil.rmtree(
            OUTPUT_DATASET
        )

    shutil.copytree(
        SOURCE_DATASET,
        OUTPUT_DATASET,
    )

    print(
        "Base dataset copied."
    )


def add_bdd_negatives():
    print()
    print(
        "ADDING BDD100K HARD NEGATIVES"
    )
    print("=" * 60)

    source_images = (
        BDD_NEGATIVES
        / "images"
    )

    source_labels = (
        BDD_NEGATIVES
        / "labels"
    )

    destination_images = (
        OUTPUT_DATASET
        / "train"
        / "images"
    )

    destination_labels = (
        OUTPUT_DATASET
        / "train"
        / "labels"
    )

    images = get_images(
        source_images
    )

    copied = 0

    for index, image_path in enumerate(
        images,
        start=1,
    ):
        source_label = (
            source_labels
            / f"{image_path.stem}.txt"
        )

        new_stem = (
            f"bddhnv3_"
            f"{image_path.stem}"
        )

        destination_image = (
            destination_images
            / (
                new_stem
                + image_path.suffix.lower()
            )
        )

        destination_label = (
            destination_labels
            / f"{new_stem}.txt"
        )

        if destination_image.exists():
            raise RuntimeError(
                "Destination image already exists: "
                f"{destination_image}"
            )

        if destination_label.exists():
            raise RuntimeError(
                "Destination label already exists: "
                f"{destination_label}"
            )

        shutil.copy2(
            image_path,
            destination_image,
        )

        shutil.copy2(
            source_label,
            destination_label,
        )

        copied += 1

        print(
            f"[{index:03d}/"
            f"{len(images):03d}] "
            f"{image_path.name}"
        )

    return copied


def create_data_yaml():
    data_yaml = (
        OUTPUT_DATASET
        / "data.yaml"
    )

    config = {
        "path": str(
            OUTPUT_DATASET.resolve()
        ),
        "train": "train/images",
        "val": "valid/images",
        "names": {
            0: "flood",
        },
    }

    with data_yaml.open(
        "w",
        encoding="utf-8",
    ) as file:
        yaml.safe_dump(
            config,
            file,
            sort_keys=False,
            allow_unicode=True,
        )

    return data_yaml


def validate_final_dataset():
    print()
    print("FINAL VALIDATION")
    print("=" * 60)

    train_images_dir = (
        OUTPUT_DATASET
        / "train"
        / "images"
    )

    train_labels_dir = (
        OUTPUT_DATASET
        / "train"
        / "labels"
    )

    valid_images_dir = (
        OUTPUT_DATASET
        / "valid"
        / "images"
    )

    valid_labels_dir = (
        OUTPUT_DATASET
        / "valid"
        / "labels"
    )

    train_images = get_images(
        train_images_dir
    )

    train_labels = list(
        train_labels_dir.glob(
            "*.txt"
        )
    )

    valid_images = get_images(
        valid_images_dir
    )

    valid_labels = list(
        valid_labels_dir.glob(
            "*.txt"
        )
    )

    print(
        f"Train images: {len(train_images)}"
    )

    print(
        f"Train labels: {len(train_labels)}"
    )

    print(
        f"Valid images: {len(valid_images)}"
    )

    print(
        f"Valid labels: {len(valid_labels)}"
    )

    if (
        len(train_images)
        != EXPECTED_FINAL_TRAIN
    ):
        raise RuntimeError(
            "Unexpected final training "
            "image count."
        )

    if (
        len(train_labels)
        != EXPECTED_FINAL_TRAIN
    ):
        raise RuntimeError(
            "Unexpected final training "
            "label count."
        )

    if (
        len(valid_images)
        != EXPECTED_FINAL_VALID
    ):
        raise RuntimeError(
            "Unexpected final validation "
            "image count."
        )

    if (
        len(valid_labels)
        != EXPECTED_FINAL_VALID
    ):
        raise RuntimeError(
            "Unexpected final validation "
            "label count."
        )

    missing_labels = []

    for image_path in train_images:
        label_path = (
            train_labels_dir
            / f"{image_path.stem}.txt"
        )

        if not label_path.exists():
            missing_labels.append(
                image_path.name
            )

    for image_path in valid_images:
        label_path = (
            valid_labels_dir
            / f"{image_path.stem}.txt"
        )

        if not label_path.exists():
            missing_labels.append(
                image_path.name
            )

    if missing_labels:
        raise RuntimeError(
            f"Missing labels: "
            f"{len(missing_labels)}"
        )

    bdd_images = [
        image
        for image in train_images
        if image.stem.startswith(
            "bddhnv3_"
        )
    ]

    bdd_labels = [
        label
        for label in train_labels
        if label.stem.startswith(
            "bddhnv3_"
        )
    ]

    print()
    print(
        f"BDD100K V3 images: "
        f"{len(bdd_images)}"
    )

    print(
        f"BDD100K V3 labels: "
        f"{len(bdd_labels)}"
    )

    non_empty_bdd_labels = [
        label
        for label in bdd_labels
        if label.stat().st_size != 0
    ]

    print(
        "Non-empty BDD negative labels: "
        f"{len(non_empty_bdd_labels)}"
    )

    if (
        len(bdd_images)
        != EXPECTED_BDD_NEGATIVES
    ):
        raise RuntimeError(
            "Incorrect number of BDD "
            "images in final dataset."
        )

    if (
        len(bdd_labels)
        != EXPECTED_BDD_NEGATIVES
    ):
        raise RuntimeError(
            "Incorrect number of BDD "
            "labels in final dataset."
        )

    if non_empty_bdd_labels:
        raise RuntimeError(
            "BDD negative labels "
            "must remain empty."
        )


def main():
    print()
    print(
        "FLOODLENS AI"
    )

    print(
        "FLOOD DATASET V3 BUILDER"
    )

    print("=" * 60)

    validate_source_dataset()

    validate_bdd_negatives()

    copy_base_dataset()

    copied = add_bdd_negatives()

    data_yaml = (
        create_data_yaml()
    )

    validate_final_dataset()

    print()
    print("=" * 60)
    print("DATASET V3 CREATED")
    print("=" * 60)

    print(
        f"Base training images: "
        f"{EXPECTED_BASE_TRAIN}"
    )

    print(
        f"New BDD negatives:     "
        f"{copied}"
    )

    print(
        f"Final training images: "
        f"{EXPECTED_FINAL_TRAIN}"
    )

    print(
        f"Validation images:     "
        f"{EXPECTED_FINAL_VALID}"
    )

    print()

    print(
        "Dataset:"
    )

    print(
        OUTPUT_DATASET
    )

    print()

    print(
        "data.yaml:"
    )

    print(
        data_yaml
    )

    print()

    print(
        "STATUS: PASSED"
    )

    print("=" * 60)


if __name__ == "__main__":
    main()