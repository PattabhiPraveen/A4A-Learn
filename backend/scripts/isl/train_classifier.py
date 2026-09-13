import sys
from pathlib import Path

import joblib
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC


BACKEND_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_ROOT.parent

DATA_FILE = (
    PROJECT_ROOT
    / "datasets"
    / "processed"
    / "DS002_ISL_Alphabet"
    / "landmarks.csv"
)

MODEL_DIR = (
    PROJECT_ROOT
    / "models"
    / "isl"
)

MODEL_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


def main():

    print("=" * 70)
    print("A4A Learn - ISL Baseline Model Training")
    print("=" * 70)

    df = pd.read_csv(DATA_FILE)

    feature_columns = [
        column
        for column in df.columns
        if column not in {
            "label",
            "image_path",
        }
    ]

    X = df[feature_columns]
    y = df["label"]

    print(f"Samples  : {len(df)}")
    print(f"Features : {len(feature_columns)}")
    print(f"Classes  : {y.nunique()}")

    # 80/20 stratified split.
    X_train, X_test, y_train, y_test = (
        train_test_split(
            X,
            y,
            test_size=0.20,
            random_state=42,
            stratify=y,
        )
    )

    print(f"Training : {len(X_train)}")
    print(f"Testing  : {len(X_test)}")

    models = {
        "logistic_regression": Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "classifier",
                    LogisticRegression(
                        max_iter=3000,
                        class_weight="balanced",
                        random_state=42,
                    ),
                ),
            ]
        ),

        "random_forest": RandomForestClassifier(
            n_estimators=300,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        ),

        "svm_rbf": Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "classifier",
                    SVC(
                        kernel="rbf",
                        probability=True,
                        class_weight="balanced",
                        random_state=42,
                    ),
                ),
            ]
        ),
    }

    results = []

    best_model = None
    best_name = None
    best_f1 = -1.0

    for name, model in models.items():

        print()
        print("-" * 70)
        print(f"Training: {name}")
        print("-" * 70)

        model.fit(
            X_train,
            y_train,
        )

        predictions = model.predict(
            X_test
        )

        accuracy = accuracy_score(
            y_test,
            predictions,
        )

        macro_f1 = f1_score(
            y_test,
            predictions,
            average="macro",
        )

        print(
            f"Accuracy : {accuracy:.4f}"
        )

        print(
            f"Macro F1 : {macro_f1:.4f}"
        )

        results.append(
            {
                "model": name,
                "accuracy": accuracy,
                "macro_f1": macro_f1,
            }
        )

        if macro_f1 > best_f1:
            best_f1 = macro_f1
            best_model = model
            best_name = name

    print()
    print("=" * 70)
    print("MODEL COMPARISON")
    print("=" * 70)

    results_df = pd.DataFrame(
        results
    ).sort_values(
        "macro_f1",
        ascending=False,
    )

    print(
        results_df.to_string(
            index=False
        )
    )

    # Detailed evaluation of selected model
    best_predictions = best_model.predict(
        X_test
    )

    print()
    print("=" * 70)
    print(f"BEST MODEL: {best_name}")
    print("=" * 70)

    print(
        classification_report(
            y_test,
            best_predictions,
            zero_division=0,
        )
    )

    model_path = (
        MODEL_DIR
        / "isl_alphabet_classifier.joblib"
    )

    joblib.dump(
        {
            "model": best_model,
            "feature_columns": feature_columns,
            "classes": sorted(y.unique()),
            "model_name": best_name,
        },
        model_path,
    )

    results_path = (
        MODEL_DIR
        / "baseline_results.csv"
    )

    results_df.to_csv(
        results_path,
        index=False,
    )

    print()
    print(f"Model saved   : {model_path}")
    print(f"Results saved : {results_path}")

    print()
    print("Training completed.")


if __name__ == "__main__":
    main()