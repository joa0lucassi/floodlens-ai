from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
)
from pathlib import Path
import csv
import shutil

from huggingface_hub import (
    hf_hub_download,
)


PROJECT_ROOT = Path(
    __file__
).resolve().parents[2]

CANDIDATES_DIR = (
    PROJECT_ROOT
    / "data"
    / "bdd100k_candidates"
)

OUTPUT_DIR = (
    CANDIDATES_DIR
    / "images"
)

REPO_ID = "dgural/bdd100k"

GROUPS = {
    "rainy_day": (
        CANDIDATES_DIR
        / "rainy_day_candidates.csv"
    ),
    "night": (
        CANDIDATES_DIR
        / "night_candidates.csv"
    ),
    "rainy_night": (
        CANDIDATES_DIR
        / "rainy_night_candidates.csv"
    ),
}

MAX_WORKERS = 6


def load_candidates(
    csv_path,
):
    with open(
        csv_path,
        "r",
        encoding="utf-8",
        newline="",
    ) as file:
        reader = csv.DictReader(
            file
        )

        return list(
            reader
        )


def download_one(
    group,
    record,
):
    remote_path = (
        record["filepath"]
    )

    filename = Path(
        remote_path
    ).name

    group_dir = (
        OUTPUT_DIR
        / group
    )

    group_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    destination = (
        group_dir
        / filename
    )

    if destination.exists():
        return {
            "group": group,
            "filename": filename,
            "status": "skipped",
            "error": "",
        }

    try:
        cached_path = (
            hf_hub_download(
                repo_id=REPO_ID,
                filename=remote_path,
                repo_type="dataset",
            )
        )

        shutil.copy2(
            cached_path,
            destination,
        )

        return {
            "group": group,
            "filename": filename,
            "status": "downloaded",
            "error": "",
        }

    except Exception as error:
        return {
            "group": group,
            "filename": filename,
            "status": "failed",
            "error": str(error),
        }


def save_manifest(
    records,
):
    manifest_path = (
        CANDIDATES_DIR
        / "download_manifest.csv"
    )

    with open(
        manifest_path,
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "group",
                "filename",
                "status",
                "error",
            ],
        )

        writer.writeheader()
        writer.writerows(
            records
        )

    return manifest_path


def main():
    print()
    print(
        "BDD100K CANDIDATE DOWNLOADER"
    )
    print("=" * 55)

    tasks = []

    for group, csv_path in (
        GROUPS.items()
    ):
        if not csv_path.exists():
            raise FileNotFoundError(
                f"Missing candidate file: "
                f"{csv_path}"
            )

        candidates = (
            load_candidates(
                csv_path
            )
        )

        print(
            f"{group}: "
            f"{len(candidates)} candidates"
        )

        for record in candidates:
            tasks.append(
                (
                    group,
                    record,
                )
            )

    print()
    print(
        f"Total requested: "
        f"{len(tasks)}"
    )

    print(
        f"Parallel downloads: "
        f"{MAX_WORKERS}"
    )

    print()
    print(
        "Downloading..."
    )

    results = []

    completed = 0

    with ThreadPoolExecutor(
        max_workers=MAX_WORKERS
    ) as executor:

        futures = [
            executor.submit(
                download_one,
                group,
                record,
            )
            for group, record
            in tasks
        ]

        for future in as_completed(
            futures
        ):
            result = (
                future.result()
            )

            results.append(
                result
            )

            completed += 1

            print(
                f"[{completed:03d}/"
                f"{len(tasks):03d}] "
                f"{result['status']:<10} "
                f"{result['group']}/"
                f"{result['filename']}"
            )

    downloaded = sum(
        result["status"]
        == "downloaded"
        for result in results
    )

    skipped = sum(
        result["status"]
        == "skipped"
        for result in results
    )

    failed = sum(
        result["status"]
        == "failed"
        for result in results
    )

    manifest_path = (
        save_manifest(
            results
        )
    )

    print()
    print("=" * 55)
    print("DOWNLOAD SUMMARY")
    print("=" * 55)

    print(
        f"Downloaded: {downloaded}"
    )

    print(
        f"Skipped:    {skipped}"
    )

    print(
        f"Failed:     {failed}"
    )

    print()

    print(
        f"Images saved in:"
    )

    print(
        OUTPUT_DIR
    )

    print()

    print(
        f"Manifest:"
    )

    print(
        manifest_path
    )

    print("=" * 55)


if __name__ == "__main__":
    main()