
from __future__ import annotations

import argparse
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import classification_report, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from xgboost import XGBClassifier

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("factorypulse.train")

RAW_FEATURES = [
    "Type",
    "Air temperature [K]",
    "Process temperature [K]",
    "Rotational speed [rpm]",
    "Torque [Nm]",
    "Tool wear [min]",
]
FAILURE_MODE_COLUMNS = ["TWF", "HDF", "PWF", "OSF", "RNF"]
NO_FAILURE_LABEL = "NONE"


@dataclass
class TrainingArtifacts:
    """Everything a downstream service needs to reproduce predictions."""

    feature_columns: list[str]
    numeric_feature_order: list[str]
    categorical_encoder_classes: list[str]
    failure_type_classes: list[str]
    metrics: dict[str, Any] = field(default_factory=dict)


class DatasetLoader:
    """Single responsibility: read the raw CSV and hand back a clean DataFrame."""

    def __init__(self, csv_path: Path):
        self._csv_path = csv_path

    def load(self) -> pd.DataFrame:
        df = pd.read_csv(self._csv_path)
        df.columns = [c.strip() for c in df.columns]
        logger.info("Loaded %d rows from %s", len(df), self._csv_path)
        return df


class FeatureEngineer:
    """Single responsibility: turn raw sensor columns into a model-ready matrix."""

    def __init__(self):
        self._type_encoder = LabelEncoder()
        self._scaler = StandardScaler()
        self._fitted = False

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        engineered = self._engineer(df)
        encoded_type = self._type_encoder.fit_transform(engineered["Type"])
        numeric_cols = [c for c in engineered.columns if c != "Type"]
        scaled = self._scaler.fit_transform(engineered[numeric_cols])
        self._fitted = True
        result = pd.DataFrame(scaled, columns=numeric_cols, index=engineered.index)
        result.insert(0, "Type", encoded_type)
        return result

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        if not self._fitted:
            raise RuntimeError("FeatureEngineer must be fit before transform().")
        engineered = self._engineer(df)
        encoded_type = self._type_encoder.transform(engineered["Type"])
        numeric_cols = [c for c in engineered.columns if c != "Type"]
        scaled = self._scaler.transform(engineered[numeric_cols])
        result = pd.DataFrame(scaled, columns=numeric_cols, index=engineered.index)
        result.insert(0, "Type", encoded_type)
        return result

    _RENAME_MAP = {
        "Type": "Type",
        "Air temperature [K]": "air_temp_k",
        "Process temperature [K]": "process_temp_k",
        "Rotational speed [rpm]": "rotational_speed_rpm",
        "Torque [Nm]": "torque_nm",
        "Tool wear [min]": "tool_wear_min",
    }

    @classmethod
    def _engineer(cls, df: pd.DataFrame) -> pd.DataFrame:
        out = df[RAW_FEATURES].rename(columns=cls._RENAME_MAP).copy()
        # Derived signals that make physical sense for a machine shop and give
        # the trees a couple of extra useful splits. XGBoost forbids "[", "]"
        # and "<" in feature names, so everything here uses plain snake_case.
        out["temp_delta"] = out["process_temp_k"] - out["air_temp_k"]
        out["power_proxy"] = out["rotational_speed_rpm"] * out["torque_nm"] / 9548.8
        return out

    @property
    def type_classes(self) -> list[str]:
        return list(self._type_encoder.classes_)

    @property
    def type_encoder(self) -> LabelEncoder:
        return self._type_encoder

    @property
    def scaler(self) -> StandardScaler:
        return self._scaler

    @property
    def numeric_feature_order(self) -> list[str]:
        return list(self._scaler.feature_names_in_)



class FailureLabeler:
    """Single responsibility: derive the failure-type label from the mode flags."""

    @staticmethod
    def derive(df: pd.DataFrame) -> pd.Series:
        def pick(row: pd.Series) -> str:
            for mode in FAILURE_MODE_COLUMNS:
                if row[mode] == 1:
                    return mode
            return NO_FAILURE_LABEL

        return df.apply(pick, axis=1)


class FailurePredictorTrainer:
    """Trains the binary 'will this machine fail' classifier."""

    def __init__(self, **xgb_params: Any):
        params = dict(
            n_estimators=300,
            max_depth=5,
            learning_rate=0.05,
            subsample=0.9,
            colsample_bytree=0.9,
            eval_metric="logloss",
            random_state=42,
        )
        params.update(xgb_params)
        self.model = XGBClassifier(**params)

    def train(self, X_train, y_train, X_test, y_test) -> dict[str, Any]:
        self.model.fit(X_train, y_train)
        proba = self.model.predict_proba(X_test)[:, 1]
        preds = self.model.predict(X_test)
        metrics = {
            "roc_auc": round(roc_auc_score(y_test, proba), 4),
            "f1": round(f1_score(y_test, preds), 4),
            "report": classification_report(y_test, preds, output_dict=True),
        }
        logger.info("Failure predictor ROC-AUC=%.4f F1=%.4f", metrics["roc_auc"], metrics["f1"])
        return metrics


class FailureTypeTrainer:
    """Trains the multiclass 'which failure mode' classifier (only on failed units)."""

    def __init__(self, **xgb_params: Any):
        params = dict(
            n_estimators=250,
            max_depth=4,
            learning_rate=0.08,
            subsample=0.9,
            colsample_bytree=0.9,
            eval_metric="mlogloss",
            random_state=42,
        )
        params.update(xgb_params)
        self.model = XGBClassifier(**params)
        self.label_encoder = LabelEncoder()

    def train(self, X_train, y_train, X_test, y_test) -> dict[str, Any]:
        y_train_enc = self.label_encoder.fit_transform(y_train)
        y_test_enc = self.label_encoder.transform(y_test)
        self.model.fit(X_train, y_train_enc)
        preds = self.model.predict(X_test)
        metrics = {
            "f1_macro": round(f1_score(y_test_enc, preds, average="macro"), 4),
            "report": classification_report(
                y_test_enc, preds, target_names=self.label_encoder.classes_, output_dict=True
            ),
        }
        logger.info("Failure type classifier macro-F1=%.4f", metrics["f1_macro"])
        return metrics


class AnomalyDetectorTrainer:
    """Trains an unsupervised Isolation Forest over sensor readings only."""

    def __init__(self, contamination: float = 0.05):
        self.model = IsolationForest(
            n_estimators=200, contamination=contamination, random_state=42
        )

    def train(self, X: pd.DataFrame) -> dict[str, Any]:
        self.model.fit(X)
        scores = self.model.decision_function(X)
        metrics = {
            "score_mean": round(float(scores.mean()), 4),
            "score_std": round(float(scores.std()), 4),
        }
        logger.info("Anomaly detector fitted. score_mean=%.4f", metrics["score_mean"])
        return metrics


class TrainingPipeline:
    """Orchestrates the loader -> feature engineer -> trainers -> persistence."""

    def __init__(self, data_path: Path, output_dir: Path):
        self._data_path = data_path
        self._output_dir = output_dir
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def run(self) -> TrainingArtifacts:
        df = DatasetLoader(self._data_path).load()
        y_failure = df["Machine failure"]
        y_type = FailureLabeler.derive(df)

        engineer = FeatureEngineer()
        X = engineer.fit_transform(df)

        X_train, X_test, y_train, y_test, ytype_train, ytype_test = train_test_split(
            X, y_failure, y_type, test_size=0.2, random_state=42, stratify=y_failure
        )

        failure_trainer = FailurePredictorTrainer()
        failure_metrics = failure_trainer.train(X_train, y_train, X_test, y_test)

        type_trainer = FailureTypeTrainer()
        type_metrics = type_trainer.train(X_train, ytype_train, X_test, ytype_test)

        anomaly_trainer = AnomalyDetectorTrainer()
        anomaly_metrics = anomaly_trainer.train(X)

        self._persist(engineer, failure_trainer, type_trainer, anomaly_trainer)

        artifacts = TrainingArtifacts(
            feature_columns=list(X.columns),
            numeric_feature_order=engineer.numeric_feature_order,
            categorical_encoder_classes=engineer.type_classes,
            failure_type_classes=list(type_trainer.label_encoder.classes_),
            metrics={
                "failure_predictor": failure_metrics,
                "failure_type": type_metrics,
                "anomaly_detector": anomaly_metrics,
            },
        )
        self._write_metadata(artifacts)
        return artifacts

    def _persist(self, engineer, failure_trainer, type_trainer, anomaly_trainer) -> None:
        joblib.dump(engineer.type_encoder, self._output_dir / "type_encoder.joblib")
        joblib.dump(engineer.scaler, self._output_dir / "feature_scaler.joblib")
        joblib.dump(failure_trainer.model, self._output_dir / "failure_predictor.joblib")
        joblib.dump(type_trainer.model, self._output_dir / "failure_type_classifier.joblib")
        joblib.dump(type_trainer.label_encoder, self._output_dir / "failure_type_encoder.joblib")
        joblib.dump(anomaly_trainer.model, self._output_dir / "anomaly_detector.joblib")
        logger.info("All model artifacts written to %s", self._output_dir)

    def _write_metadata(self, artifacts: TrainingArtifacts) -> None:
        meta_path = self._output_dir / "metadata.json"
        with open(meta_path, "w") as f:
            json.dump(
                {
                    "feature_columns": artifacts.feature_columns,
                    "numeric_feature_order": artifacts.numeric_feature_order,
                    "type_classes": artifacts.categorical_encoder_classes,
                    "failure_type_classes": artifacts.failure_type_classes,
                    "metrics": artifacts.metrics,
                },
                f,
                indent=2,
            )
        logger.info("Metadata written to %s", meta_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Train FactoryPulse AI models")
    parser.add_argument("--data", type=Path, default=Path("data/ai4i2020.csv"))
    parser.add_argument("--out", type=Path, default=Path("models"))
    args = parser.parse_args()

    pipeline = TrainingPipeline(args.data, args.out)
    artifacts = pipeline.run()
    logger.info("Training complete. Summary:\n%s", json.dumps(artifacts.metrics, indent=2)[:2000])


if __name__ == "__main__":
    main()
