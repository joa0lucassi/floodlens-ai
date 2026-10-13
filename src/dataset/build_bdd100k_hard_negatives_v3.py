from pathlib import Path
import csv
import hashlib
import shutil


PROJECT_ROOT = Path(
    __file__
).resolve().parents[2]

CANDIDATES_DIR = (
    PROJECT_ROOT
    / "data"
    / "bdd100k_candidates"
)

SOURCE_IMAGES_DIR = (
    CANDIDATES_DIR
    / "images"
)

INDEX_PATH = (
    CANDIDATES_DIR
    / "contact_sheets"
    / "contact_sheet_index.csv"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "bdd100k_hard_negatives_v3"
)

OUTPUT_IMAGES_DIR = (
    OUTPUT_DIR
    / "images"
)

OUTPUT_LABELS_DIR = (
    OUTPUT_DIR
    / "labels"
)

MANIFEST_PATH = (
    OUTPUT_DIR
    / "manifest.csv"
)


SELECTIONS = {
    "rainy_day": {
        "sheet_01.jpg": [
            1, 4, 6, 7,
            13, 16, 17, 18,
        ],
        "sheet_02.jpg": [
            1, 2, 5, 10,
            11, 13, 15, 17, 18,
        ],
        "sheet_03.jpg": [
            1, 4, 8, 10,
            11, 13, 17, 19,
        ],
        "sheet_04.jpg": [
            3, 6, 8, 10,
            11, 14, 20,
        ],
        "sheet_05.jpg": [
            3, 7, 8, 10,
            13, 15, 16, 18,
        ],
    },

    "night": {
        "sheet_01.jpg": [
            4, 7, 11, 14,
            17, 18, 19,
        ],
        "sheet_02.jpg": [
            4, 11, 13, 15,
            18, 20,
        ],
        "sheet_03.jpg": [
            6, 7, 9, 11, 18,
        ],
        "sheet_04.jpg": [
            3, 4, 10, 12,
            17, 19, 20,
        ],
        "sheet_05.jpg": [
            10, 11, 18,
        ],
    },

    "rainy_night": {
        "sheet_01.jpg": [
            2, 3, 5, 6,
            8, 10, 14, 16,
        ],
        "sheet_02.jpg": [
            1, 3, 5, 6,
            10, 12, 16, 20,
        ],
        "sheet_03.jpg": [
            1, 2, 4, 6,
            10, 12, 18, 20,
        ],
        "sheet_04.jpg": [
            1, 3, 6, 10,
            12, 15, 17, 18,
        ],
        "sheet_05.jpg": [
            1, 4, 7, 8,
            9, 12, 15, 20,
        ],
    },
}


EXPECTED_COUNTS = {
    "rainy_day": 40,
    "night": 28,
    "rainy_night": 40,
}

EXPECTED_TOTAL = 108


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


def load_index():
    if not INDEX_PATH.exists():
        raise FileNotFoundError(
            f"Contact sheet index not found: "
            f"{INDEX_PATH}"
        )

    index = {}

    with open(
        INDEX_PATH,
        "r",
        encoding="utf-8",
        newline="",
    ) as file:

        reader = csv.DictReader(
            file
        )

        for row in reader:

            key = (
                row["group"],
                row["sheet"],
                int(
                    row["position"]
                ),
            )

            index[key] = (
                row["filename"]
            )

    return index


def count_requested():
    counts = {}

    for group, sheets in (
        SELECTIONS.items()
    ):

        count = sum(
            len(positions)
            for positions
            in sheets.values()
        )

        counts[group] = count

    return counts


def validate_selection_counts():
    counts = count_requested()

    total = sum(
        counts.values()
    )

    for group, expected in (
        EXPECTED_COUNTS.items()
    ):

        actual = counts.get(
            group,
            0,
        )

        if actual != expected:
            raise RuntimeError(
                f"Invalid selection count "
                f"for {group}: "
                f"expected {expected}, "
                f"found {actual}"
            )

    if total != EXPECTED_TOTAL:
        raise RuntimeError(
            f"Expected {EXPECTED_TOTAL} "
            f"selected images, "
            f"found {total}."
        )

    return counts


def main():
    print()
    print(
        "BDD100K HARD NEGATIVES V3"
    )
    print("=" * 60)

    counts = (
        validate_selection_counts()
    )

    print(
        f"Rainy day:   "
        f"{counts['rainy_day']}"
    )

    print(
        f"Night:       "
        f"{counts['night']}"
    )

    print(
        f"Rainy night: "
        f"{counts['rainy_night']}"
    )

    print(
        f"Total:       "
        f"{sum(counts.values())}"
    )

    if OUTPUT_DIR.exists():
        raise RuntimeError(
            "Output directory already exists. "
            "Refusing to overwrite:\n"
            f"{OUTPUT_DIR}"
        )

    index = load_index()

    OUTPUT_IMAGES_DIR.mkdir(
        parents=True,
        exist_ok=False,
    )

    OUTPUT_LABELS_DIR.mkdir(
        parents=True,
        exist_ok=False,
    )

    manifest_rows = []

    copied = 0

    for group, sheets in (
        SELECTIONS.items()
    ):

        for sheet, positions in (
            sheets.items()
        ):

            for position in positions:

                key = (
                    group,
                    sheet,
                    position,
                )

                filename = (
                    index.get(
                        key
                    )
                )

                if filename is None:
                    raise RuntimeError(
                        "Selection not found "
                        "in contact sheet index: "
                        f"{key}"
                    )

                source_path = (
                    SOURCE_IMAGES_DIR
                    / group
                    / filename
                )

                if not source_path.exists():
                    raise FileNotFoundError(
                        f"Source image not found: "
                        f"{source_path}"
                    )

                output_filename = (
                    f"{group}__"
                    f"{filename}"
                )

                destination_path = (
                    OUTPUT_IMAGES_DIR
                    / output_filename
                )

                shutil.copy2(
                    source_path,
                    destination_path,
                )

                label_path = (
                    OUTPUT_LABELS_DIR
                    / (
                        Path(
                            output_filename
                        ).stem
                        + ".txt"
                    )
                )

                # Empty YOLO label:
                # no flood object in image.
                label_path.touch()

                sha256 = (
                    calculate_sha256(
                        destination_path
                    )
                )

                manifest_rows.append(
                    {
                        "dataset": (
                            "BDD100K"
                        ),
                        "group": group,
                        "sheet": sheet,
                        "position": position,
                        "original_filename": (
                            filename
                        ),
                        "output_filename": (
                            output_filename
                        ),
                        "label_filename": (
                            label_path.name
                        ),
                        "annotation": (
                            "negative_no_flood"
                        ),
                        "sha256": (
                            sha256
                        ),
                    }
                )

                copied += 1

                print(
                    f"[{copied:03d}/"
                    f"{EXPECTED_TOTAL}] "
                    f"{group:<12} "
                    f"{filename}"
                )

    if copied != EXPECTED_TOTAL:
        raise RuntimeError(
            f"Expected to copy "
            f"{EXPECTED_TOTAL} images, "
            f"but copied {copied}."
        )

    with open(
        MANIFEST_PATH,
        "w",
        encoding="utf-8",
        newline="",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "dataset",
                "group",
                "sheet",
                "position",
                "original_filename",
                "output_filename",
                "label_filename",
                "annotation",
                "sha256",
            ],
        )

        writer.writeheader()

        writer.writerows(
            manifest_rows
        )

    print()
    print("=" * 60)
    print("DATASET CREATED")
    print("=" * 60)

    print(
        f"Images: "
        f"{len(list(OUTPUT_IMAGES_DIR.glob('*')))}"
    )

    print(
        f"Labels: "
        f"{len(list(OUTPUT_LABELS_DIR.glob('*.txt')))}"
    )

    print()

    print(
        "Images directory:"
    )

    print(
        OUTPUT_IMAGES_DIR
    )

    print()

    print(
        "Labels directory:"
    )

    print(
        OUTPUT_LABELS_DIR
    )

    print()

    print(
        "Manifest:"
    )

    print(
        MANIFEST_PATH
    )

    print("=" * 60)


if __name__ == "__main__":
    main()