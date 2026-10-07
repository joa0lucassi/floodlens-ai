from pathlib import Path
import csv
import shutil
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]

SOURCE_DATASET = PROJECT_ROOT / "data" / "combined_flood_dataset"
NEGATIVE_DATASET = PROJECT_ROOT / "data" / "negative_training_v2"

MINING_CSV = (
    NEGATIVE_DATASET
    / "model_mining"
    / "hard_negative_results.csv"
)

OUTPUT_DATASET = PROJECT_ROOT / "data" / "balanced_flood_dataset"

NEGATIVE_IMAGES = NEGATIVE_DATASET / "images" / "train"
NEGATIVE_LABELS = NEGATIVE_DATASET / "labels" / "train"


def get_repeat_count(predicted: str, confidence: float) -> int:
    """
    Define quantas vezes cada negativo V2 aparecerá no treino.

    Negativo corretamente reconhecido:
        1x

    Falso positivo >= 0.70:
        7x

    Falso positivo >= 0.40:
        5x

    Falso positivo >= 0.25:
        3x
    """

    if predicted == "dry":
        return 1

    if confidence >= 0.70:
        return 7

    if confidence >= 0.40:
        return 5

    return 3


def copy_original_dataset():
    print()
    print("COPIANDO DATASET MULTI-DOMAIN")
    print("=============================")

    if OUTPUT_DATASET.exists():
        print(f"Removendo dataset anterior: {OUTPUT_DATASET}")
        shutil.rmtree(OUTPUT_DATASET)

    OUTPUT_DATASET.mkdir(parents=True, exist_ok=True)

    for split in ["train", "valid"]:
        source_images = SOURCE_DATASET / split / "images"
        source_labels = SOURCE_DATASET / split / "labels"

        destination_images = OUTPUT_DATASET / split / "images"
        destination_labels = OUTPUT_DATASET / split / "labels"

        if not source_images.exists():
            raise FileNotFoundError(
                f"Pasta não encontrada: {source_images}"
            )

        if not source_labels.exists():
            raise FileNotFoundError(
                f"Pasta não encontrada: {source_labels}"
            )

        shutil.copytree(
            source_images,
            destination_images,
        )

        shutil.copytree(
            source_labels,
            destination_labels,
        )

        image_count = len(
            list(destination_images.rglob("*.*"))
        )

        label_count = len(
            list(destination_labels.rglob("*.txt"))
        )

        print(
            f"{split}: "
            f"{image_count} imagens | "
            f"{label_count} labels"
        )


def add_balanced_negatives():
    print()
    print("ADICIONANDO HARD NEGATIVES V2")
    print("=============================")

    if not MINING_CSV.exists():
        raise FileNotFoundError(
            f"CSV de mineração não encontrado: {MINING_CSV}"
        )

    destination_images = OUTPUT_DATASET / "train" / "images"
    destination_labels = OUTPUT_DATASET / "train" / "labels"

    total_original_negatives = 0
    total_balanced_samples = 0

    stats = {
        "correct_negative": {
            "unique": 0,
            "copies": 0,
        },
        "fp_high": {
            "unique": 0,
            "copies": 0,
        },
        "fp_medium": {
            "unique": 0,
            "copies": 0,
        },
        "fp_low": {
            "unique": 0,
            "copies": 0,
        },
    }

    with MINING_CSV.open(
        "r",
        encoding="utf-8",
    ) as file:
        reader = csv.DictReader(file)

        rows = list(reader)

    if len(rows) != 60:
        print(
            f"ATENÇÃO: esperado 60 registros, "
            f"mas foram encontrados {len(rows)}."
        )

    for row in rows:
        filename = row["filename"]
        category = row["category"]
        predicted = row["predicted"]

        confidence = float(
            row["max_confidence"]
        )

        image_path = (
            NEGATIVE_IMAGES
            / category
            / filename
        )

        label_path = (
            NEGATIVE_LABELS
            / category
            / f"{Path(filename).stem}.txt"
        )

        if not image_path.exists():
            raise FileNotFoundError(
                f"Imagem não encontrada: {image_path}"
            )

        if not label_path.exists():
            raise FileNotFoundError(
                f"Label não encontrada: {label_path}"
            )

        if label_path.stat().st_size != 0:
            raise RuntimeError(
                f"Label deveria estar vazia: {label_path}"
            )

        repeat_count = get_repeat_count(
            predicted,
            confidence,
        )

        total_original_negatives += 1
        total_balanced_samples += repeat_count

        if predicted == "dry":
            stats["correct_negative"]["unique"] += 1
            stats["correct_negative"]["copies"] += repeat_count

        elif confidence >= 0.70:
            stats["fp_high"]["unique"] += 1
            stats["fp_high"]["copies"] += repeat_count

        elif confidence >= 0.40:
            stats["fp_medium"]["unique"] += 1
            stats["fp_medium"]["copies"] += repeat_count

        else:
            stats["fp_low"]["unique"] += 1
            stats["fp_low"]["copies"] += repeat_count

        suffix = image_path.suffix.lower()

        for repeat_index in range(1, repeat_count + 1):
            new_stem = (
                f"hnv2_{category}_"
                f"{Path(filename).stem}_"
                f"r{repeat_index:02d}"
            )

            new_image_path = (
                destination_images
                / f"{new_stem}{suffix}"
            )

            new_label_path = (
                destination_labels
                / f"{new_stem}.txt"
            )

            shutil.copy2(
                image_path,
                new_image_path,
            )

            shutil.copy2(
                label_path,
                new_label_path,
            )

    print()
    print("BALANCEAMENTO APLICADO")
    print("======================")

    print(
        f"Negativos únicos V2:     "
        f"{total_original_negatives}"
    )

    print(
        f"Amostras V2 no treino:   "
        f"{total_balanced_samples}"
    )

    print()
    print(
        "Corretos pelo modelo:    "
        f"{stats['correct_negative']['unique']} únicos -> "
        f"{stats['correct_negative']['copies']} amostras"
    )

    print(
        "FP alta confiança:       "
        f"{stats['fp_high']['unique']} únicos -> "
        f"{stats['fp_high']['copies']} amostras"
    )

    print(
        "FP média confiança:      "
        f"{stats['fp_medium']['unique']} únicos -> "
        f"{stats['fp_medium']['copies']} amostras"
    )

    print(
        "FP baixa confiança:      "
        f"{stats['fp_low']['unique']} únicos -> "
        f"{stats['fp_low']['copies']} amostras"
    )

    return total_balanced_samples


def create_data_yaml():
    data_yaml = OUTPUT_DATASET / "data.yaml"

    config = {
        "path": str(OUTPUT_DATASET.resolve()),
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

    print()
    print(f"data.yaml criado: {data_yaml}")


def validate_dataset():
    print()
    print("VALIDAÇÃO FINAL")
    print("===============")

    train_images = OUTPUT_DATASET / "train" / "images"
    train_labels = OUTPUT_DATASET / "train" / "labels"

    valid_images = OUTPUT_DATASET / "valid" / "images"
    valid_labels = OUTPUT_DATASET / "valid" / "labels"

    image_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".webp",
    }

    train_image_files = [
        file
        for file in train_images.rglob("*")
        if file.is_file()
        and file.suffix.lower() in image_extensions
    ]

    valid_image_files = [
        file
        for file in valid_images.rglob("*")
        if file.is_file()
        and file.suffix.lower() in image_extensions
    ]

    train_label_files = list(
        train_labels.rglob("*.txt")
    )

    valid_label_files = list(
        valid_labels.rglob("*.txt")
    )

    print(
        f"Train images: {len(train_image_files)}"
    )

    print(
        f"Train labels: {len(train_label_files)}"
    )

    print(
        f"Valid images: {len(valid_image_files)}"
    )

    print(
        f"Valid labels: {len(valid_label_files)}"
    )

    missing_labels = []

    for image_path in train_image_files:
        expected_label = (
            train_labels
            / f"{image_path.stem}.txt"
        )

        if not expected_label.exists():
            missing_labels.append(
                image_path.name
            )

    for image_path in valid_image_files:
        expected_label = (
            valid_labels
            / f"{image_path.stem}.txt"
        )

        if not expected_label.exists():
            missing_labels.append(
                image_path.name
            )

    print(
        f"Labels ausentes: {len(missing_labels)}"
    )

    if missing_labels:
        print()
        print("Primeiros labels ausentes:")

        for filename in missing_labels[:10]:
            print(f"  - {filename}")

        raise RuntimeError(
            "Dataset possui imagens sem label."
        )

    empty_train_labels = sum(
        1
        for label in train_label_files
        if label.stat().st_size == 0
    )

    print(
        f"Labels vazias no treino: "
        f"{empty_train_labels}"
    )

    print()
    print("Dataset validado com sucesso.")


def main():
    print()
    print("FLOODLENS AI")
    print("BALANCED HARD-NEGATIVE DATASET")
    print("==============================")

    if not SOURCE_DATASET.exists():
        raise FileNotFoundError(
            f"Dataset original não encontrado: "
            f"{SOURCE_DATASET}"
        )

    copy_original_dataset()

    balanced_samples = add_balanced_negatives()

    create_data_yaml()

    validate_dataset()

    print()
    print("RESUMO")
    print("======")

    print(
        f"Dataset criado em:"
    )

    print(
        OUTPUT_DATASET
    )

    print()

    print(
        f"Hard negatives V2 adicionados: "
        f"{balanced_samples}"
    )

    print()

    print(
        "O combined_flood_dataset original "
        "não foi alterado."
    )


if __name__ == "__main__":
    main()