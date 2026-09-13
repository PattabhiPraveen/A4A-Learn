import csv
import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_ROOT.parent

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


from app.isl.landmarks import HandLandmarkExtractor


DATASET_PATH = (
    PROJECT_ROOT
    / "datasets"
    / "raw"
    / "DS002_ISL_Alphabet"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "datasets"
    / "processed"
    / "DS002_ISL_Alphabet"
)

OUTPUT_FILE = OUTPUT_DIR / "landmarks.csv"

VALID_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
}


def main():

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    extractor = HandLandmarkExtractor()

    rows = []

    total = 0
    detected = 0
    failed = 0

    class_stats = {}

    try:

        for class_dir in sorted(DATASET_PATH.iterdir()):

            if not class_dir.is_dir():
                continue

            label = class_dir.name

            class_total = 0
            class_detected = 0

            for image_path in sorted(class_dir.iterdir()):

                if (
                    not image_path.is_file()
                    or image_path.suffix.lower()
                    not in VALID_EXTENSIONS
                ):
                    continue

                total += 1
                class_total += 1

                features = extractor.extract(
                    str(image_path)
                )

                if features is None:
                    failed += 1
                    continue

                detected += 1
                class_detected += 1

                rows.append(
                    [
                        label,
                        str(image_path),
                        *features.tolist(),
                    ]
                )

            class_stats[label] = (
                class_total,
                class_detected,
            )

    finally:
        extractor.close()

    feature_names = [
        f"{axis}{index}"
        for index in range(21)
        for axis in ("x", "y", "z")
    ]

    with OUTPUT_FILE.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.writer(file)

        writer.writerow(
            [
                "label",
                "image_path",
                *feature_names,
            ]
        )

        writer.writerows(rows)

    print()
    print("=" * 70)
    print("A4A Learn - ISL Landmark Extraction")
    print("=" * 70)

    for label, stats in sorted(class_stats.items()):

        class_total, class_detected = stats

        print(
            f"{label}: "
            f"{class_detected}/{class_total}"
        )

    print()
    print(f"Images processed : {total}")
    print(f"Hands detected   : {detected}")
    print(f"No hand detected : {failed}")

    if total:
        rate = detected / total * 100
        print(f"Detection rate   : {rate:.2f}%")

    print()
    print(f"Output: {OUTPUT_FILE}")
    print("=" * 70)


if __name__ == "__main__":
    main()