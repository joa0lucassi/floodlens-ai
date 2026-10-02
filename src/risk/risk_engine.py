from pathlib import Path
import csv
import json

import numpy as np


TIMELINE_PATH = Path(
    "data/temporal_analysis/flood_timeline.csv"
)

OUTPUT_PATH = Path(
    "data/temporal_analysis/risk_assessment.json"
)

SMOOTHING_WINDOW = 3
TREND_THRESHOLD_PP = 1.5


def load_records():
    records = []

    with open(
        TIMELINE_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:
            records.append(
                {
                    "time_seconds": float(
                        row["time_seconds"]
                    ),
                    "flooded_area": float(
                        row["flooded_area_percent"]
                    ),
                    "detections": int(
                        row["detections"]
                    ),
                    "max_confidence": float(
                        row["max_confidence"]
                    ),
                }
            )

    return records


def moving_average(values, window):
    if len(values) < window:
        return np.array(values)

    kernel = np.ones(window) / window

    return np.convolve(
        values,
        kernel,
        mode="valid"
    )


def calculate_trend(records):
    if len(records) < 3:
        return "INSUFFICIENT DATA", 0.0

    areas = np.array([
        record["flooded_area"]
        for record in records
    ])

    smoothed = moving_average(
        areas,
        SMOOTHING_WINDOW
    )

    if len(smoothed) < 2:
        return "INSUFFICIENT DATA", 0.0

    comparison_size = min(
        3,
        max(1, len(smoothed) // 3)
    )

    initial_area = float(
        np.median(
            smoothed[:comparison_size]
        )
    )

    final_area = float(
        np.median(
            smoothed[-comparison_size:]
        )
    )

    change = final_area - initial_area

    if change > TREND_THRESHOLD_PP:
        trend = "RISING"

    elif change < -TREND_THRESHOLD_PP:
        trend = "FALLING"

    else:
        trend = "STABLE"

    return trend, change


def area_risk_score(area):
    """
    Limites provisórios para o MVP.

    Eles representam a porcentagem visual da câmera
    ocupada pela região classificada como flood.

    No futuro serão calibrados por câmera.
    """

    if area < 5:
        return 0

    if area < 15:
        return 1

    if area < 30:
        return 2

    if area < 45:
        return 3

    return 4


def calculate_reliability(confidence):
    if confidence >= 0.60:
        return "HIGH"

    if confidence >= 0.40:
        return "MEDIUM"

    return "LOW"


def calculate_risk(records):
    areas = np.array([
        record["flooded_area"]
        for record in records
    ])

    confidences = np.array([
        record["max_confidence"]
        for record in records
    ])

    average_area = float(
        np.mean(areas)
    )

    average_confidence = float(
        np.mean(confidences)
    )

    trend, change = calculate_trend(
        records
    )

    score = area_risk_score(
        average_area
    )

    # Tendência altera o risco
    if trend == "RISING":
        score += 1

    elif trend == "FALLING":
        score -= 1

    score = max(
        0,
        min(score, 4)
    )

    if score <= 1:
        risk_level = "LOW"

    elif score == 2:
        risk_level = "MODERATE"

    elif score == 3:
        risk_level = "HIGH"

    else:
        risk_level = "CRITICAL"

    reliability = calculate_reliability(
        average_confidence
    )

    return {
        "risk_level": risk_level,
        "risk_score": score,
        "flooded_area_average": round(
            average_area,
            2
        ),
        "trend": trend,
        "trend_change_pp": round(
            change,
            2
        ),
        "average_confidence": round(
            average_confidence,
            2
        ),
        "reliability": reliability,
    }


def main():
    if not TIMELINE_PATH.exists():
        print(
            "Erro: execute primeiro o "
            "video_flood_analyzer.py"
        )
        return

    records = load_records()

    if not records:
        print(
            "Erro: histórico temporal vazio."
        )
        return

    assessment = calculate_risk(
        records
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        OUTPUT_PATH,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            assessment,
            file,
            indent=4
        )

    print()
    print("FloodLens - Risk Engine")
    print("=" * 45)

    print(
        f"Área alagada média: "
        f"{assessment['flooded_area_average']:.2f}%"
    )

    print(
        f"Tendência: "
        f"{assessment['trend']}"
    )

    print(
        f"Mudança: "
        f"{assessment['trend_change_pp']:+.2f} pp"
    )

    print(
        f"Confiança média: "
        f"{assessment['average_confidence']:.2f}"
    )

    print(
        f"Confiabilidade: "
        f"{assessment['reliability']}"
    )

    print()
    print(
        f"RISCO: "
        f"{assessment['risk_level']}"
    )

    print(
        f"Risk score: "
        f"{assessment['risk_score']}/4"
    )

    print()
    print(
        f"Resultado salvo em: "
        f"{OUTPUT_PATH}"
    )

    print("=" * 45)


if __name__ == "__main__":
    main()