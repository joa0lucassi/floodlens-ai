import cv2
from pathlib import Path


VIDEO_PATH = "data/flood_sample.mp4"
OUTPUT_DIR = Path("data/frames")
NUMBER_OF_FRAMES = 5


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    video = cv2.VideoCapture(VIDEO_PATH)

    if not video.isOpened():
        print(f"Erro: não foi possível abrir {VIDEO_PATH}")
        return

    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))

    if total_frames <= 0:
        print("Erro: não foi possível determinar o número de frames.")
        return

    positions = [
        int(i * (total_frames - 1) / (NUMBER_OF_FRAMES - 1))
        for i in range(NUMBER_OF_FRAMES)
    ]

    for index, frame_position in enumerate(positions, start=1):
        video.set(cv2.CAP_PROP_POS_FRAMES, frame_position)

        success, frame = video.read()

        if not success:
            print(f"Erro ao ler o frame {frame_position}")
            continue

        output_path = OUTPUT_DIR / f"frame_{index}.jpg"

        cv2.imwrite(str(output_path), frame)

        print(f"Salvo: {output_path}")

    video.release()

    print("Extração concluída.")


if __name__ == "__main__":
    main()