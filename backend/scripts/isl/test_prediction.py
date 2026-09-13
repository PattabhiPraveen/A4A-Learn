import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_ROOT.parent

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


from app.isl.landmarks import HandLandmarkExtractor
from app.isl.predictor import ISLAlphabetPredictor


def main():

    image_path = (
        PROJECT_ROOT
        / "datasets"
        / "raw"
        / "DS002_ISL_Alphabet"
        / "A"
        / "1.jpeg"
    )

    print("=" * 70)
    print("A4A Learn - ISL Prediction Test")
    print("=" * 70)

    print(f"Image: {image_path}")

    extractor = HandLandmarkExtractor()

    try:
        features = extractor.extract(
            str(image_path)
        )
    finally:
        extractor.close()

    if features is None:
        print("FAIL: No hand detected.")
        return

    predictor = ISLAlphabetPredictor()

    result = predictor.predict(
        features
    )

    print()
    print(f"Expected   : A")
    print(f"Predicted  : {result['label']}")
    print(f"Confidence : {result['confidence']:.2%}")
    print(f"Model      : {result['model']}")

    print()

    if result["label"] == "A":
        print("RESULT: PASS")
    else:
        print("RESULT: INCORRECT PREDICTION")

    print("=" * 70)


if __name__ == "__main__":
    main()