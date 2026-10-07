import json
from pathlib import Path

import cv2
from ultralytics import YOLO


HOLDOUT_ROOT = Path(
    "data/final_holdout/images"
)

OUTPUT_DIR = Path(
    "data/model_comparison"
)

MODELS = {
    "hardneg": Path(
        "models/flood_segmentation/best_hardneg.pt"
    ),
    "multidomain": Path(
        "models/flood_segmentation/best_multidomain.pt"
    ),
}

SUPPORTED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}


def get_images(
    directory,
):
    return sorted(
        [
            file
            for file in directory.iterdir()
            if (
                file.is_file()
                and file.suffix.lower()
                in SUPPORTED_EXTENSIONS
            )
        ]
    )


def safe_divide(
    numerator,
    denominator,
):
    if denominator == 0:
        return 0.0

    return numerator / denominator


def evaluate_model(
    model_name,
    model_path,
):
    print()
    print("=" * 70)
    print(
        f"MODEL: {model_name.upper()}"
    )
    print("=" * 70)

    model = YOLO(
        str(model_path)
    )

    records = []

    groups = [
        (
            "flood",
            HOLDOUT_ROOT
            / "flood",
        ),
        (
            "dry",
            HOLDOUT_ROOT
            / "dry",
        ),
    ]

    for (
        expected_label,
        directory,
    ) in groups:

        images = get_images(
            directory
        )

        for image_path in images:

            image = cv2.imread(
                str(image_path)
            )

            if image is None:
                print(
                    "Erro ao abrir:",
                    image_path.name,
                )
                continue

            results = model.predict(
                source=str(image_path),
                imgsz=640,
                conf=0.25,
                verbose=False,
            )

            result = results[0]

            detections = len(
                result.boxes
            )

            predicted_label = (
                "flood"
                if detections > 0
                else "dry"
            )

            max_confidence = 0.0

            if detections > 0:
                max_confidence = float(
                    result.boxes.conf.max()
                )

            correct = (
                predicted_label
                == expected_label
            )

            records.append(
                {
                    "filename":
                        image_path.name,

                    "expected":
                        expected_label,

                    "predicted":
                        predicted_label,

                    "correct":
                        correct,

                    "detections":
                        detections,

                    "max_confidence":
                        round(
                            max_confidence,
                            4,
                        ),
                }
            )

    tp = 0
    tn = 0
    fp = 0
    fn = 0

    for record in records:

        expected = record[
            "expected"
        ]

        predicted = record[
            "predicted"
        ]

        if (
            expected == "flood"
            and predicted == "flood"
        ):
            tp += 1

        elif (
            expected == "dry"
            and predicted == "dry"
        ):
            tn += 1

        elif (
            expected == "dry"
            and predicted == "flood"
        ):
            fp += 1

        elif (
            expected == "flood"
            and predicted == "dry"
        ):
            fn += 1

    total = len(
        records
    )

    accuracy = safe_divide(
        tp + tn,
        total,
    )

    precision = safe_divide(
        tp,
        tp + fp,
    )

    recall = safe_divide(
        tp,
        tp + fn,
    )

    specificity = safe_divide(
        tn,
        tn + fp,
    )

    f1 = safe_divide(
        2
        * precision
        * recall,
        precision
        + recall,
    )

    summary = {
        "model":
            model_name,

        "model_path":
            str(model_path),

        "total":
            total,

        "true_positive":
            tp,

        "true_negative":
            tn,

        "false_positive":
            fp,

        "false_negative":
            fn,

        "accuracy":
            round(
                accuracy,
                4,
            ),

        "precision":
            round(
                precision,
                4,
            ),

        "recall":
            round(
                recall,
                4,
            ),

        "specificity":
            round(
                specificity,
                4,
            ),

        "f1_score":
            round(
                f1,
                4,
            ),

        "failures": [
            record
            for record in records
            if not record[
                "correct"
            ]
        ],
    }

    print(
        f"TP: {tp}"
    )

    print(
        f"TN: {tn}"
    )

    print(
        f"FP: {fp}"
    )

    print(
        f"FN: {fn}"
    )

    print()

    print(
        f"Accuracy:    "
        f"{accuracy * 100:.2f}%"
    )

    print(
        f"Precision:   "
        f"{precision * 100:.2f}%"
    )

    print(
        f"Recall:      "
        f"{recall * 100:.2f}%"
    )

    print(
        f"Specificity: "
        f"{specificity * 100:.2f}%"
    )

    print(
        f"F1-score:    "
        f"{f1 * 100:.2f}%"
    )

    return summary


def main():
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    for model_path in (
        MODELS.values()
    ):
        if not model_path.exists():
            raise FileNotFoundError(
                model_path
            )

    results = {}

    for (
        model_name,
        model_path,
    ) in MODELS.items():

        results[
            model_name
        ] = evaluate_model(
            model_name,
            model_path,
        )

    print()
    print("=" * 70)
    print(
        "MODEL COMPARISON"
    )
    print("=" * 70)

    print()

    print(
        f"{'Metric':<16}"
        f"{'HardNeg':>12}"
        f"{'MultiDomain':>15}"
    )

    print(
        "-" * 43
    )

    metrics = [
        (
            "TP",
            "true_positive",
        ),
        (
            "TN",
            "true_negative",
        ),
        (
            "FP",
            "false_positive",
        ),
        (
            "FN",
            "false_negative",
        ),
    ]

    for (
        label,
        key,
    ) in metrics:

        print(
            f"{label:<16}"
            f"{results['hardneg'][key]:>12}"
            f"{results['multidomain'][key]:>15}"
        )

    percentage_metrics = [
        (
            "Accuracy",
            "accuracy",
        ),
        (
            "Precision",
            "precision",
        ),
        (
            "Recall",
            "recall",
        ),
        (
            "Specificity",
            "specificity",
        ),
        (
            "F1-score",
            "f1_score",
        ),
    ]

    for (
        label,
        key,
    ) in percentage_metrics:

        hardneg = (
            results[
                "hardneg"
            ][key]
            * 100
        )

        multidomain = (
            results[
                "multidomain"
            ][key]
            * 100
        )

        print(
            f"{label:<16}"
            f"{hardneg:>11.2f}%"
            f"{multidomain:>14.2f}%"
        )

    output_path = (
        OUTPUT_DIR
        / "comparison.json"
    )

    output_path.write_text(
        json.dumps(
            results,
            indent=4,
        ),
        encoding="utf-8",
    )

    print()
    print(
        "Resultado salvo em:"
    )

    print(
        output_path
    )


if __name__ == "__main__":
    main()