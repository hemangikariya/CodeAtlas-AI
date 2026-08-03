import os
import json
import logging
from datetime import datetime
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sklearn.model_selection import KFold, cross_val_score

# DB and Registry
from backend.app.adapters.models.trained_model_model import TrainedModelModel
from backend.app.ml.model_registry import model_registry
from backend.app.ml.dataset_builder import DatasetBuilder

# Pipelines
from backend.app.ml.pipelines.maintainability_pipeline import MaintainabilityPipeline
from backend.app.ml.pipelines.bug_pipeline import BugPipeline
from backend.app.ml.pipelines.complexity_pipeline import ComplexityPipeline
from backend.app.ml.pipelines.health_pipeline import HealthPipeline

# Evaluation
from backend.app.ml.evaluation import MLEvaluator

logger = logging.getLogger("codeatlas.ml")


class ModelTrainer:
    """
    Orchestrates dataset loading, splitting, cross-validation, hyperparameter fit,
    evaluation report generation, and filesystem model registry serialization.
    """

    @classmethod
    async def train_all_models(cls, db: AsyncSession, num_samples: int = 150) -> Dict[str, Any]:
        """
        Trains and registers all four repository analysis models.
        """
        logger.info("Initializing offline ML training pipeline...")
        
        # 1. Generate or load training data
        df = DatasetBuilder.generate_synthetic_seed(num_samples=num_samples)
        train_df, val_df, test_df = DatasetBuilder.train_val_test_split(df)

        X_train = train_df[DatasetBuilder.FEATURE_COLS].to_numpy()
        X_val = val_df[DatasetBuilder.FEATURE_COLS].to_numpy()
        X_test = test_df[DatasetBuilder.FEATURE_COLS].to_numpy()

        results = {}

        # -------------------------------------------------------------
        # Model 1: Maintainability Regression Pipeline
        # -------------------------------------------------------------
        logger.info("Training Maintainability Index model...")
        y_train_m = train_df["maintainability"].to_numpy()
        y_test_m = test_df["maintainability"].to_numpy()

        m_pipeline = MaintainabilityPipeline()
        m_pipeline.fit(X_train, y_train_m)
        preds_m = m_pipeline.predict(X_test)
        
        metrics_m = MLEvaluator.evaluate_regression(y_test_m, preds_m)
        metadata_m = {
            "algorithm": "Random Forest Regressor",
            "dataset": f"Synthetic Seed v1 ({num_samples} samples)",
            "feature_version": "1.0",
            "accuracy": float(metrics_m["r2"]),
            "notes": "Predicts maintainability index using structural LOC and code smell ratios."
        }
        model_registry.save_model("maintainability", "v1", m_pipeline, metadata_m, metrics_m)
        await cls._log_model_to_db(db, "maintainability", "v1", "Random Forest Regressor", metrics_m.get("r2", 0.0), metrics_m)
        results["maintainability"] = {"metadata": metadata_m, "metrics": metrics_m}

        # -------------------------------------------------------------
        # Model 2: Bug Risk Classification Pipeline
        # -------------------------------------------------------------
        logger.info("Training Bug Risk classification model...")
        y_train_b = train_df["bug_risk"].to_numpy()
        y_test_b = test_df["bug_risk"].to_numpy()

        b_pipeline = BugPipeline()
        b_pipeline.fit(X_train, y_train_b)
        preds_b = b_pipeline.predict(X_test)
        
        metrics_b = MLEvaluator.evaluate_classification(y_test_b, preds_b)
        metadata_b = {
            "algorithm": "Random Forest Classifier",
            "dataset": f"Synthetic Seed v1 ({num_samples} samples)",
            "feature_version": "1.0",
            "accuracy": float(metrics_b["accuracy"]),
            "precision": float(metrics_b["precision"]),
            "recall": float(metrics_b["recall"]),
            "f1": float(metrics_b["f1"]),
            "notes": "Predicts high vs low bug risk based on code smells and circular import paths."
        }
        model_registry.save_model("bug-risk", "v1", b_pipeline, metadata_b, metrics_b)
        await cls._log_model_to_db(db, "bug-risk", "v1", "Random Forest Classifier", metrics_b["accuracy"], metrics_b)
        results["bug_risk"] = {"metadata": metadata_b, "metrics": metrics_b}

        # -------------------------------------------------------------
        # Model 3: Code Complexity Regression Pipeline
        # -------------------------------------------------------------
        logger.info("Training Code Complexity model...")
        y_train_c = train_df["complexity"].to_numpy()
        y_test_c = test_df["complexity"].to_numpy()

        c_pipeline = ComplexityPipeline()
        c_pipeline.fit(X_train, y_train_c)
        preds_c = c_pipeline.predict(X_test)
        
        metrics_c = MLEvaluator.evaluate_regression(y_test_c, preds_c)
        metadata_c = {
            "algorithm": "Random Forest Regressor",
            "dataset": f"Synthetic Seed v1 ({num_samples} samples)",
            "feature_version": "1.0",
            "accuracy": float(metrics_c["r2"]),
            "notes": "Predicts cyclomatic and logical code complexity indices."
        }
        model_registry.save_model("complexity", "v1", c_pipeline, metadata_c, metrics_c)
        await cls._log_model_to_db(db, "complexity", "v1", "Random Forest Regressor", metrics_c.get("r2", 0.0), metrics_c)
        results["complexity"] = {"metadata": metadata_c, "metrics": metrics_c}

        # -------------------------------------------------------------
        # Model 4: Repository Health Regression Pipeline
        # -------------------------------------------------------------
        logger.info("Training Repository Health model...")
        y_train_h = train_df["health"].to_numpy()
        y_test_h = test_df["health"].to_numpy()

        h_pipeline = HealthPipeline()
        h_pipeline.fit(X_train, y_train_h)
        preds_h = h_pipeline.predict(X_test)
        
        metrics_h = MLEvaluator.evaluate_regression(y_test_h, preds_h)
        metadata_h = {
            "algorithm": "Random Forest Regressor",
            "dataset": f"Synthetic Seed v1 ({num_samples} samples)",
            "feature_version": "1.0",
            "accuracy": float(metrics_h["r2"]),
            "notes": "Aggregate repository health index combining maintainability and complexity metrics."
        }
        model_registry.save_model("repository-health", "v1", h_pipeline, metadata_h, metrics_h)
        await cls._log_model_to_db(db, "repository-health", "v1", "Random Forest Regressor", metrics_h.get("r2", 0.0), metrics_h)
        results["repository_health"] = {"metadata": metadata_h, "metrics": metrics_h}

        # 5. Output Markdown Training & Evaluation reports
        cls._generate_markdown_reports(results)

        logger.info("All ML models trained and serialized successfully.")
        return results

    @staticmethod
    async def _log_model_to_db(
        db: AsyncSession,
        model_name: str,
        version: str,
        algorithm: str,
        accuracy: float,
        metrics: Dict[str, Any]
    ) -> None:
        model_db = TrainedModelModel(
            model_name=model_name,
            version=version,
            algorithm=algorithm,
            dataset="Synthetic Seed v1",
            accuracy=float(accuracy),
            precision=float(metrics.get("precision", 0.0)),
            recall=float(metrics.get("recall", 0.0)),
            f1=float(metrics.get("f1", 0.0))
        )
        db.add(model_db)
        await db.commit()

    @staticmethod
    def _generate_markdown_reports(results: Dict[str, Any]) -> None:
        reports_dir = "backend/app/ml/reports"
        os.makedirs(reports_dir, exist_ok=True)

        # 1. Training Report
        training_report = (
            "# ML Pipeline Training Report\n\n"
            f"Generated At: {datetime.utcnow().isoformat()}Z\n\n"
            "This report summarizes the results of the model fitting phase on structural features.\n\n"
            "## Algorithms Used\n"
            "- **Maintainability**: Random Forest Regressor\n"
            "- **Bug Risk**: Random Forest Classifier\n"
            "- **Complexity**: Random Forest Regressor\n"
            "- **Repository Health**: Random Forest Regressor\n\n"
            "## Model Registry Directory\n"
            "`backend/data/models/`\n"
        )
        with open(os.path.join(reports_dir, "training_report.md"), "w", encoding="utf-8") as f:
            f.write(training_report)

        # 2. Evaluation Report
        eval_report = (
            "# ML Model Evaluation Report\n\n"
            "Summary of performance scores calculated on test datasets.\n\n"
            "| Model Name | Algorithm | Metric Type | Accuracy/R² | F1-Score | MAE | RMSE |\n"
            "| --- | --- | --- | --- | --- | --- | --- |\n"
        )
        for name, data in results.items():
            metrics = data["metrics"]
            algo = data["metadata"]["algorithm"]
            acc = metrics.get("accuracy", metrics.get("r2", 0.0))
            f1 = metrics.get("f1", 0.0)
            mae = metrics.get("mae", 0.0)
            rmse = metrics.get("rmse", 0.0)
            eval_report += f"| {name} | {algo} | {'Classification' if 'f1' in metrics else 'Regression'} | {acc:.4f} | {f1:.4f} | {mae:.4f} | {rmse:.4f} |\n"

        eval_report += (
            "\n> [!NOTE]\n"
            "> Synthetic datasets are used only for demonstration and cold-start validation.\n"
        )

        with open(os.path.join(reports_dir, "evaluation_report.md"), "w", encoding="utf-8") as f:
            f.write(eval_report)

        # 3. metrics.json
        with open(os.path.join(reports_dir, "metrics.json"), "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
