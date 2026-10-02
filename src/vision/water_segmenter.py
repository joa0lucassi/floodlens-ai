import cv2
import numpy as np


IMAGE_PATH = "data/frames/frame_3.jpg"


def main():
    image = cv2.imread(IMAGE_PATH)

    if image is None:
        print(f"Erro: não foi possível abrir {IMAGE_PATH}")
        return

    height, width = image.shape[:2]

    # Mesma região de interesse usada anteriormente
    y_start = int(height * 0.62)
    roi = image[y_start:height, 0:width]

    # Converte BGR para HSV
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    # Faixa inicial para tons marrons/amarelados da água
    lower_water = np.array([5, 35, 50])
    upper_water = np.array([35, 255, 255])

    # Cria máscara binária
    mask = cv2.inRange(hsv, lower_water, upper_water)

    # Remove pequenos ruídos
    kernel = np.ones((7, 7), np.uint8)

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

    # Calcula percentual da ROI identificado como água
    flooded_pixels = cv2.countNonZero(mask)
    total_pixels = mask.shape[0] * mask.shape[1]

    flooded_percentage = (
        flooded_pixels / total_pixels
    ) * 100

    print(
        f"Área potencialmente alagada: "
        f"{flooded_percentage:.2f}%"
    )

    # Overlay para visualizar a detecção
    overlay = roi.copy()

    overlay[mask > 0] = (
        overlay[mask > 0] * 0.5
        + np.array([255, 0, 0]) * 0.5
    ).astype(np.uint8)

    cv2.putText(
        overlay,
        f"Flooded area: {flooded_percentage:.1f}%",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (255, 255, 255),
        2,
    )

    cv2.imshow("FloodLens - Original ROI", roi)
    cv2.imshow("FloodLens - Water Mask", mask)
    cv2.imshow("FloodLens - Detection", overlay)

    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()