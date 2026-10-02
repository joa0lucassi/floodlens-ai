from pathlib import Path
import csv

import cv2
import numpy as np
from ultralytics import YOLO


MODEL_PATH = "models/flood_segmentation/best.pt"
VIDEO_PATH = "data/flood_sample.mp4"

OUTPUT_DIR = Path("data/temporal_analysis")
OUTPUT_CSV = OUTPUT_DIR / "flood_timeline.csv"

CONFIDENCE = 0.25

# Analisa aproximadamente 1 frame por segundo
SAMPLE_INTERVAL_SECONDS = 1.0

# Número de amostras usadas para suavização
SMOOTHING_WINDOW = 3

# Mudanças menores que 1.5 ponto percentual
# são consideradas variação normal do modelo.
TREND_THRESHOLD_PP = 1.5


def calculate_flooded_area(result, frame_shape):
    """
    Combina todas as máscaras detectadas e calcula
    o percentual visual da imagem classificado como flood.
    """

    height, width = frame_shape[:2]

    combined_mask = np.zeros(
        (height, width),
        dtype=np.uint8
    )

    if result.masks is None:
        return 0.0

    for polygon in result.masks.xy:
        if len(polygon) < 3:
            continue

        points = polygon.astype(np.int32)

        cv2.fillPoly(
            combined_mask,
            [points],
            255
        )

    flooded_pixels = cv2.countNonZero(combined_mask)
    total_pixels = height * width

    return (
        flooded_pixels / total_pixels
    ) * 100


def moving_average(values, window):
    """
    Suaviza pequenas oscilações entre frames.
    """

    if len(values) < window:
        return np.array(values)

    kernel = np.ones(window) / window

    return np.convolve(
        values,
        kernel,
        mode="valid"
    )


def calculate_trend(records):
    """
    Compara o início e o final da série temporal
    usando valores suavizados.

    Evita transformar pequenas oscilações de vídeos
    curtos em falsos alertas de aumento ou queda.
    """

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

    # Usa até 3 valores suavizados no início/final
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


def main():
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    model = YOLO(MODEL_PATH)

    video = cv2.VideoCapture(
        VIDEO_PATH
    )

    if not video.isOpened():
        print(
            f"Erro: não foi possível abrir "
            f"{VIDEO_PATH}"
        )
        return

    fps = video.get(
        cv2.CAP_PROP_FPS
    )

    total_frames = int(
        video.get(
            cv2.CAP_PROP_FRAME_COUNT
        )
    )

    duration = (
        total_frames / fps
        if fps > 0
        else 0
    )

    frame_interval = max(
        1,
        int(
            fps * SAMPLE_INTERVAL_SECONDS
        )
    )

    print()
    print("FloodLens - Temporal Flood Analysis")
    print("=" * 55)

    print(f"FPS: {fps:.2f}")
    print(f"Frames: {total_frames}")
    print(f"Duração: {duration:.2f} s")

    print(
        f"Amostragem: "
        f"{SAMPLE_INTERVAL_SECONDS:.1f} s"
    )

    print("=" * 55)

    records = []

    frame_index = 0

    while True:
        success, frame = video.read()

        if not success:
            break

        if frame_index % frame_interval != 0:
            frame_index += 1
            continue

        time_seconds = (
            frame_index / fps
            if fps > 0
            else 0
        )

        results = model.predict(
            source=frame,
            imgsz=640,
            conf=CONFIDENCE,
            verbose=False
        )

        result = results[0]

        flooded_area = calculate_flooded_area(
            result,
            frame.shape
        )

        if (
            result.boxes is not None
            and len(result.boxes) > 0
        ):
            confidences = (
                result.boxes.conf
                .cpu()
                .numpy()
            )

            max_confidence = float(
                np.max(confidences)
            )

            detection_count = len(
                result.boxes
            )

        else:
            max_confidence = 0.0
            detection_count = 0

        records.append(
            {
                "time_seconds": time_seconds,
                "flooded_area": flooded_area,
                "detections": detection_count,
                "max_confidence": max_confidence,
            }
        )

        print(
            f"{time_seconds:6.1f}s | "
            f"Área: {flooded_area:6.2f}% | "
            f"Detecções: {detection_count} | "
            f"Conf: {max_confidence:.2f}"
        )

        frame_index += 1

    video.release()

    with open(
        OUTPUT_CSV,
        "w",
        newline="",
        encoding="utf-8"
    ) as csv_file:

        writer = csv.writer(
            csv_file
        )

        writer.writerow([
            "time_seconds",
            "flooded_area_percent",
            "detections",
            "max_confidence",
        ])

        for record in records:
            writer.writerow([
                f"{record['time_seconds']:.2f}",
                f"{record['flooded_area']:.4f}",
                record["detections"],
                f"{record['max_confidence']:.4f}",
            ])

    trend, change = calculate_trend(
        records
    )

    print()
    print("=" * 55)

    if records:
        areas = np.array([
            record["flooded_area"]
            for record in records
        ])

        print(
            f"Área média: "
            f"{np.mean(areas):.2f}%"
        )

        print(
            f"Área mínima: "
            f"{np.min(areas):.2f}%"
        )

        print(
            f"Área máxima: "
            f"{np.max(areas):.2f}%"
        )

        print(
            f"Desvio padrão: "
            f"{np.std(areas):.2f} pp"
        )

    print()
    print(
        f"Tendência: {trend}"
    )

    print(
        f"Mudança suavizada: "
        f"{change:+.2f} pontos percentuais"
    )

    print()
    print(
        f"Histórico salvo em: "
        f"{OUTPUT_CSV}"
    )

    print("=" * 55)


if __name__ == "__main__":
    main()