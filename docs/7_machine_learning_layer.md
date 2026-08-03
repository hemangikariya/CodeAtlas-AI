# Phase 6 — Machine Learning Layer Design Documentation

This document describes the design, implementation, and features of the CodeAtlas AI **Machine Learning Layer**. The ML Layer is an offline prediction and metric scoring subsystem designed to evaluate code maintainability, bug risk, code complexity, and aggregate repository health.

---

## 1. High-Level Architecture

The ML Layer runs decoupled from the AI Gateway and LLM components to assure high-velocity metrics calculations.

```
Repository Snapshot
       ↓
Feature Engineering (FeatureExtractor)
       ↓
Feature Store (cached features)
       ↓
Preprocessing (FeaturePreprocessor: scaling & validation)
       ↓
Prediction Engine (InferenceEngine: Random Forest models)
       ↓
Explainability (top features calculation)
       ↓
REST APIs / ML Service Facade
```

---

## 2. Feature Engineering & Store

### Feature Extraction (`FeatureExtractor`)
Computes 27 structural metrics across three categories:
1. **Repository Metrics**: File counts, class/function counts, LOC, average function lengths, comment ratio, folder depth, import counts, and language ratios.
2. **Knowledge Graph Features**: Graph nodes, graph edges, density, connected components, centrality, and dependency density.
3. **Static Analysis Heuristics**: Cyclomatic complexity approximation, long method count, large class count, dead code guesses, duplicate lines ratio, and aggregate code smells.

### Feature Store (`FeatureStore`)
Features are cached in memory and serialized to the disk filesystem at `backend/data/features/{snapshot_id}.json` to avoid redundant computation.

---

## 3. Preprocessing & Dataset Pipeline

### Feature Preprocessing (`FeaturePreprocessor`)
- Validates that all required feature columns are numeric.
- Handles missing features by applying logical zero values.
- Applies standard scaling standardization using training dataset mean and standard deviations: `(x - mean) / std`.

### Dataset Builder (`DatasetBuilder`)
- Formulates training datasets from indexed repositories.
- Splits samples into train, validation, and test subsets.
- Exports features and labels to CSV files.
- Generates synthetic seed datasets.
- **IMPORTANT**: Synthetic datasets and heuristical labels are used solely for demonstration, testing, and cold-start model validation.

---

## 4. Models & Registry

### Model Types
The layer implements four classical ML estimators using `scikit-learn`:
1. **Maintainability Model**: Random Forest Regressor predicting scoring indices (0 to 100).
2. **Bug Risk Model**: Random Forest Classifier predicting risk probabilities and binary class labels (Low vs High).
3. **Complexity Model**: Random Forest Regressor predicting cyclomatic complexity scores (0 to 100).
4. **Repository Health Model**: Random Forest Regressor predicting aggregate health indices (0 to 100).

### Model Registry (`ModelRegistry`)
Trained pipelines (standardization parameters + model weights) are versioned and stored under:
`backend/data/models/{model_name}/{version}/model.pkl` along with `metadata.json` and `metrics.json`.

---

## 5. Training, Inference, and Explainability

### Training Pipeline (`ModelTrainer`)
Triggers Random Forest fits, calculates evaluation metrics (R² score, MAE, F1, accuracy, etc.), and persists logs into the database `trained_models` table.

### Prediction & Explainability (`PredictionEngine`)
- Retrieves computed features and feeds them into the serialized registry model.
- Calculates top-3 explanatory features based on raw model feature importances, returning:
```json
{
  "prediction": 84.2,
  "confidence": 0.93,
  "top_features": [
    "Cyclomatic Complexity",
    "Dependency Density",
    "Average Function Length"
  ]
}
```

---

## 6. REST API Endpoints

Authorized developers can call the following endpoints under `/api/v1/ml/`:
- `POST /maintainability`: Returns maintainability index predictions.
- `POST /bug-risk`: Returns bug risk classification and confidences.
- `POST /complexity`: Returns complexity predictions.
- `POST /repository-health`: Returns aggregate health predictions.
- `GET /models`: Lists registered model configurations.
- `GET /evaluation`: Retrieves hyperparameter validation metrics.
- `GET /features`: Gets raw calculated features for a snapshot.
