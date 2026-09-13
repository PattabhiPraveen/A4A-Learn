from pathlib import Path

from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[3]

DATASET_PATH = (
    PROJECT_ROOT
    / "datasets"
    / "raw"
    / "DS002_ISL_Alphabet"
)

VALID_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
}


def main():

    print()
    print("=" * 70)
    print("A4A Learn - ISL Alphabet Dataset Validation")
    print("=" * 70)

    print(f"Dataset path : {DATASET_PATH}")
    print(f"Exists       : {DATASET_PATH.exists()}")

    if not DATASET_PATH.exists():
        raise FileNotFoundError(DATASET_PATH)

    total_images = 0
    invalid_images = []
    class_counts = {}

    dimensions = {}

    for class_folder in sorted(DATASET_PATH.iterdir()):

        if not class_folder.is_dir():
            continue

        count = 0

        for image_path in class_folder.iterdir():

            if not image_path.is_file():
                continue

            if image_path.suffix.lower() not in VALID_EXTENSIONS:
                continue

            try:

                with Image.open(image_path) as image:

                    image.verify()

                with Image.open(image_path) as image:

                    size = image.size

                    dimensions[size] = (
                        dimensions.get(size, 0)
                        + 1
                    )

                count += 1
                total_images += 1

            except Exception as exc:

                invalid_images.append(
                    {
                        "file": str(image_path),
                        "error": str(exc),
                    }
                )

        class_counts[class_folder.name] = count

    print()
    print("Class Distribution")
    print("-" * 70)

    for class_name, count in sorted(
        class_counts.items()
    ):

        print(
            f"{class_name:>2} : {count}"
        )

    print()
    print(f"Classes       : {len(class_counts)}")
    print(f"Total images  : {total_images}")
    print(f"Invalid files : {len(invalid_images)}")

    print()
    print("Image Resolutions")
    print("-" * 70)

    for size, count in sorted(
        dimensions.items(),
        key=lambda item: item[1],
        reverse=True,
    ):

        print(
            f"{size[0]}x{size[1]} : {count}"
        )

    if invalid_images:

        print()
        print("Invalid Images")
        print("-" * 70)

        for item in invalid_images:
            print(
                item["file"],
                "->",
                item["error"],
            )

    print()
    print("=" * 70)
    print("Dataset validation completed.")
    print("=" * 70)


if __name__ == "__main__":
    main()