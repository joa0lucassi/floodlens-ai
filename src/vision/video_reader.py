import cv2


VIDEO_PATH = "data/sample.mp4"


def main():
    video = cv2.VideoCapture(VIDEO_PATH)

    if not video.isOpened():
        print(f"Erro: não foi possível abrir o vídeo em {VIDEO_PATH}")
        return

    fps = video.get(cv2.CAP_PROP_FPS)
    frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))

    print(f"FPS: {fps:.2f}")
    print(f"Frames: {frame_count}")
    print(f"Resolução: {width}x{height}")

    while True:
        success, frame = video.read()

        if not success:
            break

        cv2.imshow("FloodLens AI - Video", frame)

        # Pressione Q para encerrar
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    video.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()