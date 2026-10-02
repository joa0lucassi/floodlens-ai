import cv2


IMAGE_PATH = "data/frames/frame_3.jpg"


def main():
    image = cv2.imread(IMAGE_PATH)

    if image is None:
        print(f"Erro: não foi possível abrir {IMAGE_PATH}")
        return

    height, width = image.shape[:2]

    # Faixa vertical usada como medidor virtual
    x_start = int(width * 0.39)
    x_end = int(width * 0.46)

    y_start = int(height * 0.45)
    y_end = height

    gauge = image[
        y_start:y_end,
        x_start:x_end
    ]

    preview = image.copy()

    cv2.rectangle(
        preview,
        (x_start, y_start),
        (x_end, y_end - 1),
        (0, 255, 0),
        3
    )

    cv2.putText(
        preview,
        "Virtual Flood Gauge",
        (x_start - 40, y_start - 15),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 0),
        2
    )

    cv2.imshow("FloodLens - Gauge Position", preview)
    cv2.imshow("FloodLens - Gauge", gauge)

    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()