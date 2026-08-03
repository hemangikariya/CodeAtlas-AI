import pytest
import os
import uuid
import numpy as np
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# DB models
from backend.app.adapters.models.project_model import ProjectModel
from backend.app.adapters.models.repository_model import RepositoryModel
from backend.app.adapters.models.snapshot_model import SnapshotModel
from backend.app.adapters.models.file_model import FileModel
from backend.app.adapters.models.code_chunk_model import CodeChunkModel
from backend.app.adapters.models.dependency_model import DependencyModel
from backend.app.adapters.models.graph_node_model import GraphNodeModel
from backend.app.adapters.models.graph_edge_model import GraphEdgeModel
from backend.app.adapters.models.trained_model_model import TrainedModelModel
from backend.app.adapters.models.prediction_history_model import PredictionHistoryModel

# ML Modules
from backend.app.ml.feature_engineering import FeatureExtractor
from backend.app.ml.feature_store import feature_store
from backend.app.ml.preprocessing import FeaturePreprocessor
from backend.app.ml.dataset_builder import DatasetBuilder
from backend.app.ml.model_registry import model_registry
from backend.app.ml.training import ModelTrainer
from backend.app.ml.inference import InferenceEngine
from backend.app.ml.prediction_engine import PredictionEngine
from backend.app.ml.ml_service import MLService


@pytest.mark.asyncio
async def test_feature_engineering_and_store(db_session: AsyncSession):
    # 1. Setup mock repository records
    proj = ProjectModel(name="ML Test Proj", description="ML description")
    db_session.add(proj)
    await db_session.commit()
    await db_session.refresh(proj)

    repo = RepositoryModel(project_id=proj.id, name="ml-test-repo", url="https://github.com/ml/test")
    db_session.add(repo)
    await db_session.commit()
    await db_session.refresh(repo)

    snap = SnapshotModel(repository_id=repo.id, commit_sha="mlcommit123", status="INDEXED")
    db_session.add(snap)
    await db_session.commit()
    await db_session.refresh(snap)

    # Add code file
    file_record = FileModel(
        snapshot_id=snap.id,
        name="calculator.py",
        path="src/calculator.py",
        content_chunk="def add(a, b):\n    # adds values\n    if a > 0:\n        return a + b\n    return b\n"
    )
    db_session.add(file_record)
    await db_session.commit()
    await db_session.refresh(file_record)

    # Add code chunk
    chunk_record = CodeChunkModel(
        file_id=file_record.id,
        name="add",
        type="FUNCTION",
        content="def add(a, b):\n    # adds values\n    if a > 0:\n        return a + b\n    return b\n",
        start_line=1,
        end_line=5
    )
    db_session.add(chunk_record)

    # Add dependency
    dep_record = DependencyModel(
        snapshot_id=snap.id,
        source="src/calculator.py",
        target="sys",
        type="EXTERNAL"
    )
    db_session.add(dep_record)

    # Add graph nodes
    node1 = GraphNodeModel(snapshot_id=snap.id, name="calculator.py", type="FILE", properties={})
    db_session.add(node1)
    await db_session.commit()
    await db_session.refresh(node1)

    node2 = GraphNodeModel(snapshot_id=snap.id, name="add", type="FUNCTION", properties={})
    db_session.add(node2)
    await db_session.commit()
    await db_session.refresh(node2)

    edge1 = GraphEdgeModel(snapshot_id=snap.id, source_node_id=node1.id, target_node_id=node2.id, type="CONTAINS", properties={})
    db_session.add(edge1)
    await db_session.commit()

    # 2. Extract features
    features = await FeatureExtractor.extract_features(db_session, str(snap.id))
    assert features["total_files"] == 1.0
    assert features["total_functions"] == 1.0
    assert features["lines_of_code"] == 5.0
    assert features["comment_ratio"] == 0.2
    assert features["folder_depth"] == 2.0
    assert features["cyclomatic_complexity"] == 2.0  # 1 file + 1 if condition

    # 3. Test Feature Store caching
    assert not feature_store.exists(str(snap.id))
    feature_store.set(str(snap.id), features)
    assert feature_store.exists(str(snap.id))
    cached = feature_store.get(str(snap.id))
    assert cached["total_files"] == 1.0
    feature_store.invalidate(str(snap.id))
    assert not feature_store.exists(str(snap.id))


@pytest.mark.asyncio
async def test_preprocessing_and_dataset_builder():
    # 1. Dataset builder check
    df = DatasetBuilder.generate_synthetic_seed(num_samples=20)
    assert len(df) == 20
    assert "maintainability" in df.columns
    assert "bug_risk" in df.columns

    train, val, test = DatasetBuilder.train_val_test_split(df, 0.6, 0.2)
    assert len(train) == 12
    assert len(val) == 4
    assert len(test) == 4

    # 2. Preprocessor validation and scaling
    sample_feat = df[DatasetBuilder.FEATURE_COLS].iloc[0].to_dict()
    FeaturePreprocessor.validate_features(sample_feat)

    # Impute check
    imputed = FeaturePreprocessor.impute_missing({"total_files": None, "lines_of_code": 100})
    assert imputed["total_files"] == 0.0
    assert imputed["lines_of_code"] == 100.0

    # Vector conversion
    vec = FeaturePreprocessor.to_vector(sample_feat)
    assert vec.shape == (27,)

    # Standardization scale
    mean = np.zeros(27)
    std = np.ones(27)
    scaled = FeaturePreprocessor.scale_vector(vec, mean, std)
    assert np.allclose(scaled, vec)


@pytest.mark.asyncio
async def test_model_training_and_registry(db_session: AsyncSession):
    # 1. Run model training pipeline
    results = await ModelTrainer.train_all_models(db_session, num_samples=30)
    assert "maintainability" in results
    assert "bug_risk" in results
    assert "complexity" in results
    assert "repository_health" in results

    # Assert model serialized files are present
    model_dir = os.path.join("backend/data/models", "maintainability", "v1")
    assert os.path.exists(os.path.join(model_dir, "model.pkl"))
    assert os.path.exists(os.path.join(model_dir, "metadata.json"))

    # Assert SQL database rows logged
    db_models_q = await db_session.execute(select(TrainedModelModel))
    db_models = db_models_q.scalars().all()
    assert len(db_models) >= 4


@pytest.mark.asyncio
async def test_ml_service_and_rest_api(client: AsyncClient, db_session: AsyncSession):
    # 1. Create a dummy snapshot to predict
    proj = ProjectModel(name="ML Router Proj", description="ML router description")
    db_session.add(proj)
    await db_session.commit()
    await db_session.refresh(proj)

    repo = RepositoryModel(project_id=proj.id, name="ml-router-repo", url="https://github.com/ml/router")
    db_session.add(repo)
    await db_session.commit()
    await db_session.refresh(repo)

    snap = SnapshotModel(repository_id=repo.id, commit_sha="mlroutercommit", status="INDEXED")
    db_session.add(snap)
    await db_session.commit()
    await db_session.refresh(snap)

    # Seed some fake file
    f = FileModel(snapshot_id=snap.id, name="main.py", path="main.py", content_chunk="import sys\n")
    db_session.add(f)
    await db_session.commit()

    # Ensure models are trained
    await MLService.train_all_models(db_session)

    # 2. Authentication setup
    await client.post(
        "/api/v1/auth/register",
        json={"email": "ml-developer@codeatlas.ai", "password": "securepass123", "role": "DEVELOPER"}
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "ml-developer@codeatlas.ai", "password": "securepass123"}
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Test REST endpoints
    endpoints = ["maintainability", "bug-risk", "complexity", "repository-health"]
    for route in endpoints:
        resp = await client.post(
            f"/api/v1/ml/{route}",
            json={"repository_id": str(repo.id), "snapshot_id": str(snap.id)},
            headers=headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "prediction" in data
        assert "confidence" in data
        assert len(data["top_features"]) == 3

    # Test GET list models
    models_resp = await client.get("/api/v1/ml/models", headers=headers)
    assert models_resp.status_code == 200
    assert len(models_resp.json()) >= 4

    # Test GET evaluations
    eval_resp = await client.get("/api/v1/ml/evaluation", headers=headers)
    assert eval_resp.status_code == 200
    assert "maintainability" in eval_resp.json()

    # Test GET features
    feats_resp = await client.get(f"/api/v1/ml/features?snapshot_id={snap.id}", headers=headers)
    assert feats_resp.status_code == 200
    assert "total_files" in feats_resp.json()
