import cv2
import numpy as np


IMAGE_PATH = "data/frames/frame_3.jpg"


def main():
    image = cv2.imread(IMAGE_PATH)

    if image is None:
        print(f"Erro: não foi possível abrir {IMAGE_PATH}")
        return

    height, width = image.shape[:2]

    # Posição do medidor virtual
    x_start = int(width * 0.39)
    x_end = int(width * 0.46)

    y_start = int(height * 0.45)
    y_end = height

    gauge = image[y_start:y_end, x_start:x_end]

    # Converte para HSV
    hsv = cv2.cvtColor(gauge, cv2.COLOR_BGR2HSV)

    # Faixa inicial para tons da água
    lower_water = np.array([5, 35, 50])
    upper_water = np.array([35, 255, 255])

    # Cria máscara binária
    mask = cv2.inRange(
        hsv,
        lower_water,
        upper_water
    )

    # Remove pequenos ruídos
    kernel = np.ones((5, 5), np.uint8)

    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_OPEN,
        kernel
    )

    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_CLOSE,
        kernel
    )

    # Encontra regiões conectadas na máscara
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
        mask,
        connectivity=8
    )

    # Analisa os últimos pixels do medidor
    # Procuramos regiões que chegam até a parte inferior,
    # pois a água deve estar conectada ao fundo da imagem
    bottom_area = labels[-10:, :]

    candidate_labels = np.unique(bottom_area)

    # Remove o fundo preto (label 0)
    candidate_labels = candidate_labels[
        candidate_labels != 0
    ]

    waterline = None

    if len(candidate_labels) > 0:

        # Escolhe o maior componente conectado ao fundo
        water_label = max(
            candidate_labels,
            key=lambda label: stats[
                label,
                cv2.CC_STAT_AREA
            ]
        )

        # Posição superior do componente de água
        waterline = stats[
            water_label,
            cv2.CC_STAT_TOP
        ]

    preview = image.copy()

    if waterline is None:

        print("Nenhuma linha de água detectada.")

    else:

        gauge_height = y_end - y_start

        flooded_height = gauge_height - waterline

        level_percentage = (
            flooded_height / gauge_height
        ) * 100

        global_waterline = y_start + waterline

        print(
            f"Nível relativo detectado: "
            f"{level_percentage:.2f}%"
        )

        # Linha vermelha indicando o limite da água
        cv2.line(
            preview,
            (x_start, global_waterline),
            (x_end, global_waterline),
            (0, 0, 255),
            4
        )

        cv2.putText(
            preview,
            f"Flood level: {level_percentage:.1f}%",
            (x_start - 80, y_start - 15),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2
        )

    # Retângulo verde mostrando o medidor virtual
    cv2.rectangle(
        preview,
        (x_start, y_start),
        (x_end, y_end - 1),
        (0, 255, 0),
        3
    )

    # Janela principal redimensionável
    cv2.namedWindow(
        "FloodLens - Flood Level",
        cv2.WINDOW_NORMAL
    )

    cv2.resizeWindow(
        "FloodLens - Flood Level",
        1000,
        600
    )

    cv2.imshow(
        "FloodLens - Flood Level",
        preview
    )

    # Janela da máscara
    cv2.namedWindow(
        "FloodLens - Gauge Mask",
        cv2.WINDOW_NORMAL
    )

    cv2.resizeWindow(
        "FloodLens - Gauge Mask",
        400,
        600
    )

    cv2.imshow(
        "FloodLens - Gauge Mask",
        mask
    )

    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()