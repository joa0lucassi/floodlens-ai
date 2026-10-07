import csv
import shutil
from pathlib import Path


# ============================================================
# CONFIGURAÇÃO
# ============================================================

PROJECT_ROOT = Path.cwd()

RUALIVREIA_ROOT = Path(
    "data/datasets/rualivreia"
)

UFES_ROOT = Path(
    "data/ufes_yolo"
)

UFES_MANIFEST = (
    UFES_ROOT / "manifest.csv"
)

NEGATIVE_ROOT = Path(
    "data/negative_training/prepared"
)

OUTPUT_ROOT = Path(
    "data/combined_flood_dataset"
)

MIN_CONVERSION_IOU = 0.85

NEGATIVE_REPEATS = 3


# ============================================================
# PASTAS
# ============================================================

TRAIN_IMAGES = (
    OUTPUT_ROOT / "train" / "images"
)

TRAIN_LABELS = (
    OUTPUT_ROOT / "train" / "labels"
)

VALID_IMAGES = (
    OUTPUT_ROOT / "valid" / "images"
)

VALID_LABELS = (
    OUTPUT_ROOT / "valid" / "labels"
)


IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}


def create_directories():
    if OUTPUT_ROOT.exists():
        shutil.rmtree(
            OUTPUT_ROOT
        )

    for directory in [
        TRAIN_IMAGES,
        TRAIN_LABELS,
        VALID_IMAGES,
        VALID_LABELS,
    ]:
        directory.mkdir(
            parents=True,
            exist_ok=True,
        )


# ============================================================
# UTILIDADES
# ============================================================

def get_images(directory):
    return sorted(
        [
            file
            for file in directory.iterdir()
            if (
                file.is_file()
                and file.suffix.lower()
                in IMAGE_EXTENSIONS
            )
        ]
    )


def copy_pair(
    image_path,
    label_path,
    destination_images,
    destination_labels,
    prefix,
):
    if not image_path.exists():
        raise FileNotFoundError(
            image_path
        )

    if not label_path.exists():
        raise FileNotFoundError(
            label_path
        )

    output_stem = (
        f"{prefix}_{image_path.stem}"
    )

    output_image = (
        destination_images
        / (
            output_stem
            + image_path.suffix.lower()
        )
    )

    output_label = (
        destination_labels
        / (
            output_stem
            + ".txt"
        )
    )

    shutil.copy2(
        image_path,
        output_image,
    )

    shutil.copy2(
        label_path,
        output_label,
    )

    return {
        "image":
            output_image,

        "label":
            output_label,
    }


# ============================================================
# RUALIVREIA
# ============================================================

def copy_rualivreia_split(
    split,
    destination_images,
    destination_labels,
):
    images_dir = (
        RUALIVREIA_ROOT
        / split
        / "images"
    )

    labels_dir = (
        RUALIVREIA_ROOT
        / split
        / "labels"
    )

    images = get_images(
        images_dir
    )

    copied = 0

    for image_path in images:
        label_path = (
            labels_dir
            / (
                image_path.stem
                + ".txt"
            )
        )

        copy_pair(
            image_path=image_path,
            label_path=label_path,
            destination_images=destination_images,
            destination_labels=destination_labels,
            prefix="rualivreia",
        )

        copied += 1

    return copied


# ============================================================
# UFES
# ============================================================

def load_ufes_manifest():
    with open(
        UFES_MANIFEST,
        "r",
        encoding="utf-8",
    ) as file:
        return list(
            csv.DictReader(file)
        )


def copy_ufes_dataset(
    manifest,
    dataset_name,
    destination_images,
    destination_labels,
):
    rows = [
        row
        for row in manifest
        if (
            row["dataset"]
            == dataset_name
            and float(
                row["conversion_iou"]
            )
            >= MIN_CONVERSION_IOU
        )
    ]

    copied = 0

    prefix = (
        dataset_name.lower()
    )

    for row in rows:
        image_path = Path(
            row["output_image"]
        )

        label_path = Path(
            row["output_label"]
        )

        copy_pair(
            image_path=image_path,
            label_path=label_path,
            destination_images=destination_images,
            destination_labels=destination_labels,
            prefix=prefix,
        )

        copied += 1

    return copied


# ============================================================
# HARD NEGATIVES
# ============================================================

def copy_hard_negatives():
    source_images = (
        NEGATIVE_ROOT
        / "images"
    )

    images = get_images(
        source_images
    )

    copied = 0

    for index, image_path in enumerate(
        images,
        start=1,
    ):
        for repeat in range(
            1,
            NEGATIVE_REPEATS + 1,
        ):
            output_stem = (
                f"hardneg_"
                f"{index:03d}_"
                f"r{repeat}"
            )

            output_image = (
                TRAIN_IMAGES
                / (
                    output_stem
                    + image_path.suffix.lower()
                )
            )

            output_label = (
                TRAIN_LABELS
                / (
                    output_stem
                    + ".txt"
                )
            )

            shutil.copy2(
                image_path,
                output_image,
            )

            # Label vazio:
            # nenhuma região flood.
            output_label.write_text(
                "",
                encoding="utf-8",
            )

            copied += 1

    return copied


# ============================================================
# VALIDAÇÃO DO DATASET FINAL
# ============================================================

def count_images(directory):
    return len(
        get_images(directory)
    )


def count_labels(directory):
    return len(
        list(
            directory.glob("*.txt")
        )
    )


def verify_pairs(
    images_dir,
    labels_dir,
):
    images = get_images(
        images_dir
    )

    missing = []

    for image in images:
        label = (
            labels_dir
            / (
                image.stem
                + ".txt"
            )
        )

        if not label.exists():
            missing.append(
                image.name
            )

    return missing


# ============================================================
# DATA.YAML
# ============================================================

def create_yaml():
    yaml_path = (
        OUTPUT_ROOT
        / "data.yaml"
    )

    content = """
path: data/combined_flood_dataset

train: train/images
val: valid/images

names:
  0: flood
""".strip()

    yaml_path.write_text(
        content,
        encoding="utf-8",
    )

    return yaml_path


# ============================================================
# MAIN
# ============================================================

def main():
    print()
    print(
        "FloodLens AI - "
        "Combined Dataset Builder"
    )

    print("=" * 65)

    create_directories()

    manifest = (
        load_ufes_manifest()
    )

    print()
    print(
        "Copiando RuaLivreIA..."
    )

    rualivreia_train = (
        copy_rualivreia_split(
            split="train",
            destination_images=TRAIN_IMAGES,
            destination_labels=TRAIN_LABELS,
        )
    )

    rualivreia_valid = (
        copy_rualivreia_split(
            split="valid",
            destination_images=VALID_IMAGES,
            destination_labels=VALID_LABELS,
        )
    )

    print(
        "RuaLivreIA train:",
        rualivreia_train,
    )

    print(
        "RuaLivreIA valid:",
        rualivreia_valid,
    )

    print()
    print(
        "Copiando Deepflood..."
    )

    deepflood = copy_ufes_dataset(
        manifest=manifest,
        dataset_name="Deepflood",
        destination_images=TRAIN_IMAGES,
        destination_labels=TRAIN_LABELS,
    )

    print(
        "Deepflood:",
        deepflood,
    )

    print()
    print(
        "Copiando Sazara..."
    )

    sazara = copy_ufes_dataset(
        manifest=manifest,
        dataset_name="Sazara",
        destination_images=TRAIN_IMAGES,
        destination_labels=TRAIN_LABELS,
    )

    print(
        "Sazara:",
        sazara,
    )

    print()
    print(
        "Copiando WebCOOS "
        "exclusivamente para validação..."
    )

    webcoos = copy_ufes_dataset(
        manifest=manifest,
        dataset_name="WebCOOS",
        destination_images=VALID_IMAGES,
        destination_labels=VALID_LABELS,
    )

    print(
        "WebCOOS:",
        webcoos,
    )

    print()
    print(
        "Adicionando hard negatives..."
    )

    hard_negatives = (
        copy_hard_negatives()
    )

    print(
        "Hard negatives:",
        hard_negatives,
    )

    train_images_count = (
        count_images(
            TRAIN_IMAGES
        )
    )

    train_labels_count = (
        count_labels(
            TRAIN_LABELS
        )
    )

    valid_images_count = (
        count_images(
            VALID_IMAGES
        )
    )

    valid_labels_count = (
        count_labels(
            VALID_LABELS
        )
    )

    train_missing = (
        verify_pairs(
            TRAIN_IMAGES,
            TRAIN_LABELS,
        )
    )

    valid_missing = (
        verify_pairs(
            VALID_IMAGES,
            VALID_LABELS,
        )
    )

    yaml_path = create_yaml()

    print()
    print(
        "=" * 65
    )

    print(
        "DATASET COMBINADO"
    )

    print(
        "=" * 65
    )

    print(
        "TRAIN"
    )

    print(
        "  RuaLivreIA:",
        rualivreia_train,
    )

    print(
        "  Deepflood:",
        deepflood,
    )

    print(
        "  Sazara:",
        sazara,
    )

    print(
        "  Hard negatives:",
        hard_negatives,
    )

    print(
        "  ----------------"
    )

    print(
        "  Imagens:",
        train_images_count,
    )

    print(
        "  Labels:",
        train_labels_count,
    )

    print()

    print(
        "VALIDATION"
    )

    print(
        "  RuaLivreIA:",
        rualivreia_valid,
    )

    print(
        "  WebCOOS:",
        webcoos,
    )

    print(
        "  ----------------"
    )

    print(
        "  Imagens:",
        valid_images_count,
    )

    print(
        "  Labels:",
        valid_labels_count,
    )

    print()

    print(
        "Imagens train sem label:",
        len(train_missing),
    )

    print(
        "Imagens valid sem label:",
        len(valid_missing),
    )

    print()

    print(
        "data.yaml:"
    )

    print(
        yaml_path
    )

    expected_train = (
        1040
        + 1002
        + 241
        + 63
    )

    expected_valid = (
        99
        + 35
    )

    if (
        train_images_count
        != expected_train
    ):
        raise ValueError(
            f"Train esperado: "
            f"{expected_train}, "
            f"encontrado: "
            f"{train_images_count}"
        )

    if (
        valid_images_count
        != expected_valid
    ):
        raise ValueError(
            f"Validation esperado: "
            f"{expected_valid}, "
            f"encontrado: "
            f"{valid_images_count}"
        )

    if train_missing:
        raise ValueError(
            "Existem imagens de treino "
            "sem label."
        )

    if valid_missing:
        raise ValueError(
            "Existem imagens de validação "
            "sem label."
        )

    print()
    print(
        "✅ Dataset combinado validado."
    )


if __name__ == "__main__":
    main()