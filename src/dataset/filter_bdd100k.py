from pathlib import Path
import csv
import json
import random


PROJECT_ROOT = Path(__file__).resolve().parents[2]

METADATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "bdd100k_metadata"
    / "samples.json"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "bdd100k_candidates"
)

RANDOM_SEED = 42

CANDIDATES_PER_GROUP = 100


def get_label(sample, field):
    value = sample.get(field)

    if not isinstance(value, dict):
        return None

    return value.get("label")


def build_record(sample):
    return {
        "filepath": sample.get(
            "filepath",
            "",
        ),
        "weather": get_label(
            sample,
            "weather",
        ),
        "timeofday": get_label(
            sample,
            "timeofday",
        ),
        "scene": get_label(
            sample,
            "scene",
        ),
    }


def save_csv(
    path,
    samples,
):
    rows = [
        build_record(sample)
        for sample in samples
    ]

    with open(
        path,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "filepath",
                "weather",
                "timeofday",
                "scene",
            ],
        )

        writer.writeheader()
        writer.writerows(rows)


def choose_samples(
    samples,
    amount,
):
    if len(samples) <= amount:
        return samples.copy()

    return random.sample(
        samples,
        amount,
    )


def main():
    if not METADATA_PATH.exists():
        raise FileNotFoundError(
            f"Metadata not found: "
            f"{METADATA_PATH}"
        )

    print()
    print("BDD100K CANDIDATE FILTER")
    print("=" * 50)

    with open(
        METADATA_PATH,
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    samples = data["samples"]

    rainy = [
        sample
        for sample in samples
        if get_label(
            sample,
            "weather",
        ) == "rainy"
    ]

    night = [
        sample
        for sample in samples
        if get_label(
            sample,
            "timeofday",
        ) == "night"
    ]

    rainy_night = [
        sample
        for sample in samples
        if (
            get_label(
                sample,
                "weather",
            ) == "rainy"
            and get_label(
                sample,
                "timeofday",
            ) == "night"
        )
    ]

    rainy_day = [
        sample
        for sample in samples
        if (
            get_label(
                sample,
                "weather",
            ) == "rainy"
            and get_label(
                sample,
                "timeofday",
            ) != "night"
        )
    ]

    night_nonrain = [
        sample
        for sample in samples
        if (
            get_label(
                sample,
                "timeofday",
            ) == "night"
            and get_label(
                sample,
                "weather",
            ) != "rainy"
        )
    ]

    print(
        f"Total samples: "
        f"{len(samples)}"
    )

    print(
        f"Rainy: "
        f"{len(rainy)}"
    )

    print(
        f"Night: "
        f"{len(night)}"
    )

    print(
        f"Rainy + Night: "
        f"{len(rainy_night)}"
    )

    print(
        f"Rainy daytime/non-night: "
        f"{len(rainy_day)}"
    )

    print(
        f"Night without rainy label: "
        f"{len(night_nonrain)}"
    )

    random.seed(
        RANDOM_SEED
    )

    selected_rainy_day = (
        choose_samples(
            rainy_day,
            CANDIDATES_PER_GROUP,
        )
    )

    selected_night = (
        choose_samples(
            night_nonrain,
            CANDIDATES_PER_GROUP,
        )
    )

    selected_rainy_night = (
        choose_samples(
            rainy_night,
            CANDIDATES_PER_GROUP,
        )
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    save_csv(
        OUTPUT_DIR
        / "rainy_day_candidates.csv",
        selected_rainy_day,
    )

    save_csv(
        OUTPUT_DIR
        / "night_candidates.csv",
        selected_night,
    )

    save_csv(
        OUTPUT_DIR
        / "rainy_night_candidates.csv",
        selected_rainy_night,
    )

    print()
    print("CANDIDATES SELECTED")
    print("=" * 50)

    print(
        "Rainy day: "
        f"{len(selected_rainy_day)}"
    )

    print(
        "Night: "
        f"{len(selected_night)}"
    )

    print(
        "Rainy + Night: "
        f"{len(selected_rainy_night)}"
    )

    print()
    print(
        f"Saved in: "
        f"{OUTPUT_DIR}"
    )

    print("=" * 50)


if __name__ == "__main__":
    main()