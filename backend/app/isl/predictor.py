from pathlib import Path

import joblib
import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]

DEFAULT_MODEL_PATH = (
    PROJECT_ROOT
    / "models"
    / "isl"
    / "isl_alphabet_classifier.joblib"
)


class ISLAlphabetPredictor:
    """
    Predict an ISL alphabet class from 63 MediaPipe
    hand-landmark features.
    """

    def __init__(
        self,
        model_path: Path = DEFAULT_MODEL_PATH,
    ):

        if not model_path.exists():
            raise FileNotFoundError(
                f"ISL model not found: {model_path}"
            )

        artifact = joblib.load(model_path)

        self.model = artifact["model"]
        self.feature_columns = artifact["feature_columns"]
        self.classes = artifact["classes"]
        self.model_name = artifact["model_name"]

    def predict(
        self,
        features: np.ndarray,
        confidence_threshold: float = 0.70,
    ) -> dict:
        """
        Predict an ISL alphabet from 63 hand-landmark features.

        A prediction is returned to the learner only when its
        confidence meets the configured threshold.
        """

        features = np.asarray(
            features,
            dtype=np.float32,
        )

        if features.shape != (63,):
            raise ValueError(
                "Expected exactly 63 landmark features."
            )

        if not 0.0 <= confidence_threshold <= 1.0:
            raise ValueError(
                "Confidence threshold must be between 0 and 1."
            )

        # Preserve the feature names used during model training.
        # This also avoids the scikit-learn feature-name warning.
        X = pd.DataFrame(
            [features],
            columns=self.feature_columns,
        )

        prediction = self.model.predict(X)[0]

        probabilities = self.model.predict_proba(X)[0]

        best_index = int(
            np.argmax(probabilities)
        )

        confidence = float(
            probabilities[best_index]
        )

        accepted = (
            confidence >= confidence_threshold
        )

        return {
            "label": (
                str(prediction)
                if accepted
                else None
            ),
            "predicted_label": str(prediction),
            "confidence": round(
                confidence,
                4,
            ),
            "accepted": accepted,
            "threshold": confidence_threshold,
            "model": self.model_name,
        }