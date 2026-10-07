from pathlib import Path
import hashlib

import cv2
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]

HOLDOUT_DIR = PROJECT_ROOT / "data" / "final_holdout" / "images"

REFERENCE_DIRS = [
    PROJECT_ROOT / "data" / "combined_flood_dataset",
    PROJECT_ROOT / "data" / "datasets" / "rualivreia",
    PROJECT_ROOT / "data" / "ufes_yolo",
    PROJECT_ROOT / "data" / "negative_training_v2",
    PROJECT_ROOT / "data" / "regression_set",
]

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp",
}

DHASH_THRESHOLD = 8


def get_images(directory):
    if not directory.exists():
        return []

    return [
        path
        for path in directory.rglob("*")
        if path.is_file()
        and path.suffix.lower() in IMAGE_EXTENSIONS
    ]


def sha256(path):
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def dhash(path):
    image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)

    if image is None:
        raise RuntimeError(f"Não foi possível abrir: {path}")

    resized = cv2.resize(
        image,
        (9, 8),
        interpolation=cv2.INTER_AREA,
    )

    differences = resized[:, 1:] > resized[:, :-1]

    value = 0

    for bit in differences.flatten():
        value = (value << 1) | int(bit)

    return value


def hamming_distance(hash1, hash2):
    return (hash1 ^ hash2).bit_count()


def main():
    print()
    print("FLOODLENS AI")
    print("FINAL HOLDOUT OVERLAP CHECK")
    print("===========================")
    print()

    holdout_images = get_images(HOLDOUT_DIR)

    print(f"Holdout images: {len(holdout_images)}")

    if len(holdout_images) != 40:
        raise RuntimeError(
            f"Esperado 40 imagens no holdout, "
            f"encontrado {len(holdout_images)}."
        )

    reference_images = []

    print()
    print("REFERÊNCIAS")
    print("===========")

    for directory in REFERENCE_DIRS:
        images = get_images(directory)

        print(
            f"{directory.relative_to(PROJECT_ROOT)}: "
            f"{len(images)} imagens"
        )

        reference_images.extend(images)

    print()
    print(
        f"Total de imagens de referência: "
        f"{len(reference_images)}"
    )

    print()
    print("Calculando hashes...")

    holdout_data = []

    for index, path in enumerate(holdout_images, start=1):
        print(
            f"Holdout {index:02d}/{len(holdout_images)}",
            end="\r",
        )

        holdout_data.append(
            {
                "path": path,
                "sha256": sha256(path),
                "dhash": dhash(path),
            }
        )

    print()

    reference_data = []

    for index, path in enumerate(reference_images, start=1):
        if index % 100 == 0 or index == len(reference_images):
            print(
                f"Referências {index}/{len(reference_images)}",
                end="\r",
            )

        try:
            reference_data.append(
                {
                    "path": path,
                    "sha256": sha256(path),
                    "dhash": dhash(path),
                }
            )
        except RuntimeError as error:
            print()
            print("AVISO:", error)

    print()
    print()

    reference_sha = {}

    for item in reference_data:
        reference_sha.setdefault(
            item["sha256"],
            [],
        ).append(item["path"])

    exact_matches = []
    near_matches = []

    print("Comparando...")
    print()

    for holdout in holdout_data:
        if holdout["sha256"] in reference_sha:
            for reference_path in reference_sha[holdout["sha256"]]:
                exact_matches.append(
                    (
                        holdout["path"],
                        reference_path,
                    )
                )

        best_distance = 65
        best_reference = None

        for reference in reference_data:
            distance = hamming_distance(
                holdout["dhash"],
                reference["dhash"],
            )

            if distance < best_distance:
                best_distance = distance
                best_reference = reference["path"]

        if (
            best_reference is not None
            and best_distance <= DHASH_THRESHOLD
        ):
            near_matches.append(
                (
                    holdout["path"],
                    best_reference,
                    best_distance,
                )
            )

    print("RESULTADO")
    print("=========")
    print(
        f"Coincidências SHA-256: "
        f"{len(exact_matches)}"
    )
    print(
        f"Near-duplicates dHash <= {DHASH_THRESHOLD}: "
        f"{len(near_matches)}"
    )

    if exact_matches:
        print()
        print("COINCIDÊNCIAS EXATAS")
        print("====================")

        for holdout_path, reference_path in exact_matches:
            print()
            print("Holdout:")
            print(holdout_path)
            print("Referência:")
            print(reference_path)

    if near_matches:
        print()
        print("POSSÍVEIS NEAR-DUPLICATES")
        print("=========================")

        for (
            holdout_path,
            reference_path,
            distance,
        ) in near_matches:
            print()
            print(f"Distância dHash: {distance}")
            print("Holdout:")
            print(holdout_path)
            print("Referência:")
            print(reference_path)

    print()

    if not exact_matches and not near_matches:
        print("✅ Nenhuma sobreposição detectada.")
        print(
            "O holdout pode ser congelado para "
            "a avaliação final."
        )
    else:
        print(
            "⚠️ Revisar os casos acima antes "
            "da avaliação final."
        )


if __name__ == "__main__":
    main()