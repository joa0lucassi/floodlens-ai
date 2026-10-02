import cv2


IMAGE_PATH = "data/frames/frame_3.jpg"


def main():
    image = cv2.imread(IMAGE_PATH)

    if image is None:
        print(f"Erro: não foi possível abrir {IMAGE_PATH}")
        return

    height, width = image.shape[:2]

    # Região inferior da imagem onde está a rua
    y_start = int(height * 0.62)

    roi = image[y_start:height, 0:width]

    # Mostra a região selecionada na imagem original
    preview = image.copy()

    cv2.rectangle(
        preview,
        (0, y_start),
        (width - 1, height - 1),
        (0, 255, 0),
        3,
    )

    cv2.putText(
        preview,
        "Flood Monitoring ROI",
        (20, y_start - 15),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2,
    )

    cv2.imshow("FloodLens - Monitoring Area", preview)
    cv2.imshow("FloodLens - ROI", roi)

    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()