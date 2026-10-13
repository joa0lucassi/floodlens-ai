
from pathlib import Path
import csv
import math

from PIL import (
    Image,
    ImageDraw,
    ImageFont,
)


PROJECT_ROOT = Path(
    __file__
).resolve().parents[2]

IMAGES_DIR = (
    PROJECT_ROOT
    / "data"
    / "bdd100k_candidates"
    / "images"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "bdd100k_candidates"
    / "contact_sheets"
)

INDEX_PATH = (
    OUTPUT_DIR
    / "contact_sheet_index.csv"
)


GROUPS = [
    "rainy_day",
    "night",
    "rainy_night",
]

COLUMNS = 4
ROWS = 5

IMAGES_PER_SHEET = (
    COLUMNS * ROWS
)

THUMB_WIDTH = 320
THUMB_HEIGHT = 180

LABEL_HEIGHT = 45

CELL_WIDTH = THUMB_WIDTH
CELL_HEIGHT = (
    THUMB_HEIGHT
    + LABEL_HEIGHT
)

SUPPORTED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}


def get_images(
    folder,
):
    return sorted(
        path
        for path in folder.iterdir()
        if (
            path.is_file()
            and path.suffix.lower()
            in SUPPORTED_EXTENSIONS
        )
    )


def prepare_thumbnail(
    image_path,
):
    with Image.open(
        image_path
    ) as image:

        image = image.convert(
            "RGB"
        )

        image.thumbnail(
            (
                THUMB_WIDTH,
                THUMB_HEIGHT,
            )
        )

        canvas = Image.new(
            "RGB",
            (
                THUMB_WIDTH,
                THUMB_HEIGHT,
            ),
            "black",
        )

        x = (
            THUMB_WIDTH
            - image.width
        ) // 2

        y = (
            THUMB_HEIGHT
            - image.height
        ) // 2

        canvas.paste(
            image,
            (
                x,
                y,
            ),
        )

        return canvas


def create_sheet(
    group,
    sheet_number,
    images,
    index_rows,
):
    width = (
        COLUMNS
        * CELL_WIDTH
    )

    height = (
        ROWS
        * CELL_HEIGHT
    )

    sheet = Image.new(
        "RGB",
        (
            width,
            height,
        ),
        "#111111",
    )

    draw = ImageDraw.Draw(
        sheet
    )

    font = (
        ImageFont.load_default()
    )

    for position, image_path in enumerate(
        images,
        start=1,
    ):
        zero_index = (
            position - 1
        )

        row = (
            zero_index
            // COLUMNS
        )

        column = (
            zero_index
            % COLUMNS
        )

        x = (
            column
            * CELL_WIDTH
        )

        y = (
            row
            * CELL_HEIGHT
        )

        thumbnail = (
            prepare_thumbnail(
                image_path
            )
        )

        sheet.paste(
            thumbnail,
            (
                x,
                y,
            ),
        )

        label_y = (
            y
            + THUMB_HEIGHT
        )

        draw.rectangle(
            [
                (
                    x,
                    label_y,
                ),
                (
                    x
                    + CELL_WIDTH,
                    label_y
                    + LABEL_HEIGHT,
                ),
            ],
            fill="#202020",
        )

        label = (
            f"{position:02d} | "
            f"{image_path.name}"
        )

        draw.text(
            (
                x + 8,
                label_y + 12,
            ),
            label,
            fill="white",
            font=font,
        )

        index_rows.append(
            {
                "group": group,
                "sheet": (
                    f"sheet_"
                    f"{sheet_number:02d}.jpg"
                ),
                "position": position,
                "filename": (
                    image_path.name
                ),
            }
        )

    group_output = (
        OUTPUT_DIR
        / group
    )

    group_output.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        group_output
        / (
            f"sheet_"
            f"{sheet_number:02d}.jpg"
        )
    )

    sheet.save(
        output_path,
        quality=92,
    )

    return output_path


def save_index(
    rows,
):
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        INDEX_PATH,
        "w",
        encoding="utf-8",
        newline="",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "group",
                "sheet",
                "position",
                "filename",
            ],
        )

        writer.writeheader()
        writer.writerows(
            rows
        )


def main():
    print()
    print(
        "BDD100K CONTACT SHEETS"
    )
    print("=" * 55)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    index_rows = []

    total_images = 0
    total_sheets = 0

    for group in GROUPS:

        group_dir = (
            IMAGES_DIR
            / group
        )

        if not group_dir.exists():
            print(
                f"Missing folder: "
                f"{group_dir}"
            )
            continue

        images = get_images(
            group_dir
        )

        total_images += len(
            images
        )

        number_of_sheets = (
            math.ceil(
                len(images)
                / IMAGES_PER_SHEET
            )
        )

        print()
        print(
            f"{group}: "
            f"{len(images)} images"
        )

        for sheet_index in range(
            number_of_sheets
        ):
            start = (
                sheet_index
                * IMAGES_PER_SHEET
            )

            end = (
                start
                + IMAGES_PER_SHEET
            )

            batch = images[
                start:end
            ]

            output_path = (
                create_sheet(
                    group=group,
                    sheet_number=(
                        sheet_index + 1
                    ),
                    images=batch,
                    index_rows=index_rows,
                )
            )

            total_sheets += 1

            print(
                f"  Created: "
                f"{output_path.name}"
            )

    save_index(
        index_rows
    )

    print()
    print("=" * 55)
    print("SUMMARY")
    print("=" * 55)

    print(
        f"Images reviewed: "
        f"{total_images}"
    )

    print(
        f"Contact sheets: "
        f"{total_sheets}"
    )

    print()

    print(
        "Saved in:"
    )

    print(
        OUTPUT_DIR
    )

    print()

    print(
        "Index:"
    )

    print(
        INDEX_PATH
    )

    print("=" * 55)


if __name__ == "__main__":
    main()