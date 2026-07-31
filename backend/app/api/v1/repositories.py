import os
import shutil
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File as FastAPIFile, Form, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
import git

from backend.app.adapters.database.base import get_db
from backend.app.adapters.repositories.repository_repository import RepositoryRepository
from backend.app.adapters.repositories.snapshot_repository import SnapshotRepository
from backend.app.core.config import settings
from backend.app.core.dependencies import get_current_active_developer
from backend.app.core.logging import logger
from backend.app.domain.ingestion import Repository, RepositorySnapshot
from backend.app.domain.models import User
from backend.app.schemas.repository import (
    RepositoryResponse, SnapshotResponse, StatisticsResponse, StatusResponse, MetadataResponse,
    FolderSchema, FileSchema, CodeChunkSchema, DependencySchema, DetectedLanguageSchema
)
from backend.app.usecases.ingestion import IngestRepositoryUseCase
from backend.app.events.event_types import RepositoryUploadedEvent
from backend.app.events.dispatcher import event_dispatcher

router = APIRouter()

# Helper background tasks
async def process_zip_upload(snapshot_id: str, zip_path: str):
    logger.info(f"Background task processing ZIP upload: {zip_path}")
    # Dispatch RepositoryUploadedEvent to trigger subscribers.py
    await event_dispatcher.dispatch(RepositoryUploadedEvent(
        snapshot_id=snapshot_id,
        file_path=zip_path
    ))

async def process_git_clone(snapshot_id: str, git_url: str, branch: Optional[str] = None):
    logger.info(f"Background task processing Git clone: {git_url}")
    clone_dir = os.path.join(settings.STORAGE_DIR, "clones", snapshot_id)
    os.makedirs(clone_dir, exist_ok=True)
    
    async with get_db() as db:
        snap_repo = SnapshotRepository(db)
        await snap_repo.update_snapshot_status(snapshot_id, "UPLOADING")
        await db.commit()
        
    try:
        # Perform clone
        if branch:
            git.Repo.clone_from(git_url, clone_dir, branch=branch)
        else:
            git.Repo.clone_from(git_url, clone_dir)
            
        logger.info(f"Successfully cloned git repository {git_url} to {clone_dir}")
        
        # Dispatch event with local_dir_path
        await event_dispatcher.dispatch(RepositoryUploadedEvent(
            snapshot_id=snapshot_id,
            local_dir_path=clone_dir
        ))
    except Exception as e:
        logger.error(f"Git clone failed for URL {git_url}: {str(e)}")
        async with get_db() as db:
            snap_repo = SnapshotRepository(db)
            await snap_repo.update_snapshot_status(snapshot_id, "FAILED")
            await db.commit()
        if os.path.exists(clone_dir):
            shutil.rmtree(clone_dir)

@router.post("/upload", response_model=SnapshotResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_repository(
    background_tasks: BackgroundTasks,
    project_id: str = Form(...),
    name: str = Form(...),
    branch: Optional[str] = Form(None),
    file: UploadFile = FastAPIFile(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_developer)
):
    # Validate extension
    if not file.filename.lower().endswith(".zip"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only ZIP archives are allowed."
        )

    # Validate file size (e.g. limit to 50MB)
    max_size = 50 * 1024 * 1024
    content_size = 0
    
    # Verify project exists (crud validation)
    repo_repo = RepositoryRepository(db)
    snap_repo = SnapshotRepository(db)

    # Create directory if not exists
    upload_dir = os.path.join(settings.STORAGE_DIR, "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    snapshot_id = str(uuid.uuid4())
    zip_path = os.path.join(upload_dir, f"{snapshot_id}.zip")
    
    try:
        with open(zip_path, "wb") as f:
            for chunk in iter(lambda: file.file.read(8192), b""):
                content_size += len(chunk)
                if content_size > max_size:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="File is too large. Max size is 50MB."
                    )
                f.write(chunk)
    except HTTPException:
        if os.path.exists(zip_path):
            os.remove(zip_path)
        raise
    except Exception as e:
        if os.path.exists(zip_path):
            os.remove(zip_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload save failure: {str(e)}"
        )

    # Create entries
    repo = Repository(project_id=project_id, name=name)
    repo = await repo_repo.create_repository(repo)
    
    snap = RepositorySnapshot(
        repository_id=repo.id,
        branch=branch or "main",
        status="PENDING",
        id=snapshot_id
    )
    snap = await snap_repo.create_snapshot(snap)
    await db.commit()

    # Launch background ingestion
    background_tasks.add_task(process_zip_upload, snap.id, zip_path)
    return snap

@router.post("/git", response_model=SnapshotResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_git_repository(
    background_tasks: BackgroundTasks,
    project_id: str = Form(...),
    name: str = Form(...),
    git_url: str = Form(...),
    branch: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_developer)
):
    repo_repo = RepositoryRepository(db)
    snap_repo = SnapshotRepository(db)
    
    # Create entries
    repo = Repository(project_id=project_id, name=name, url=git_url)
    repo = await repo_repo.create_repository(repo)
    
    snapshot_id = str(uuid.uuid4())
    snap = RepositorySnapshot(
        repository_id=repo.id,
        branch=branch or "main",
        status="PENDING",
        id=snapshot_id
    )
    snap = await snap_repo.create_snapshot(snap)
    await db.commit()

    background_tasks.add_task(process_git_clone, snap.id, git_url, branch)
    return snap

@router.get("/", response_model=List[RepositoryResponse])
async def list_repositories(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_developer)
):
    repo_repo = RepositoryRepository(db)
    return await repo_repo.get_project_repositories(project_id)

@router.get("/{id}", response_model=RepositoryResponse)
async def get_repository(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_developer)
):
    repo_repo = RepositoryRepository(db)
    repo = await repo_repo.get_repository(id)
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found."
        )
    return repo

@router.get("/{id}/snapshots", response_model=List[SnapshotResponse])
async def list_snapshots(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_developer)
):
    snap_repo = SnapshotRepository(db)
    return await snap_repo.get_repository_snapshots(id)

@router.get("/{id}/status", response_model=StatusResponse)
async def get_snapshot_status(
    id: str,  # snapshot_id or repository_id
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_developer)
):
    snap_repo = SnapshotRepository(db)
    # Check if id represents snapshot_id
    snap = await snap_repo.get_snapshot(id)
    if snap:
        return StatusResponse(snapshot_id=snap.id, status=snap.status)
        
    # Check if id represents repository_id, get latest snapshot
    snaps = await snap_repo.get_repository_snapshots(id)
    if snaps:
        return StatusResponse(snapshot_id=snaps[0].id, status=snaps[0].status)
        
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Snapshot or Repository status not found."
    )

@router.get("/{id}/statistics", response_model=StatisticsResponse)
async def get_repository_statistics(
    id: str, # snapshot_id or repository_id
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_developer)
):
    snap_repo = SnapshotRepository(db)
    
    # Try to find snapshot statistics directly
    stats = await snap_repo.get_snapshot_statistics(id)
    if stats:
        return stats
        
    # Try repository_id's latest snapshot
    snaps = await snap_repo.get_repository_snapshots(id)
    if snaps:
        stats = await snap_repo.get_snapshot_statistics(snaps[0].id)
        if stats:
            return stats
            
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Statistics not found."
    )

@router.get("/{id}/metadata", response_model=MetadataResponse)
async def get_snapshot_metadata(
    id: str, # snapshot_id
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_developer)
):
    # Fetch folder structure, files, chunks, dependencies, and languages
    # Using raw SQL or model queries
    from sqlalchemy.future import select
    from backend.app.adapters.models.folder_model import FolderModel
    from backend.app.adapters.models.file_model import FileModel
    from backend.app.adapters.models.code_chunk_model import CodeChunkModel
    from backend.app.adapters.models.dependency_model import DependencyModel
    from backend.app.adapters.models.detected_language_model import DetectedLanguageModel

    snap_repo = SnapshotRepository(db)
    snap = await snap_repo.get_snapshot(id)
    if not snap:
        # Try latest snapshot of repository_id
        snaps = await snap_repo.get_repository_snapshots(id)
        if snaps:
            snap = snaps[0]
            id = snap.id
            
    if not snap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Snapshot or Repository not found."
        )

    # Folders
    res_f = await db.execute(select(FolderModel).filter(FolderModel.snapshot_id == uuid.UUID(id)))
    folders = [FolderSchema(id=str(f.id), name=f.name, path=f.path, parent_folder_id=str(f.parent_folder_id) if f.parent_folder_id else None) for f in res_f.scalars().all()]
    
    # Files
    res_fl = await db.execute(select(FileModel).filter(FileModel.snapshot_id == uuid.UUID(id)))
    files = [FileSchema(id=str(f.id), name=f.name, path=f.path, folder_id=str(f.folder_id) if f.folder_id else None) for f in res_fl.scalars().all()]
    file_ids = [uuid.UUID(f.id) for f in files]
    
    # CodeChunks
    chunks = []
    if file_ids:
        res_ch = await db.execute(select(CodeChunkModel).filter(CodeChunkModel.file_id.in_(file_ids)))
        chunks = [CodeChunkSchema(
            id=str(c.id), file_id=str(c.file_id), name=c.name, type=c.type, content=c.content, start_line=c.start_line, end_line=c.end_line, metadata_json=c.metadata_json
        ) for c in res_ch.scalars().all()]
        
    # Dependencies
    res_dp = await db.execute(select(DependencyModel).filter(DependencyModel.snapshot_id == uuid.UUID(id)))
    dependencies = [DependencySchema(id=str(d.id), source=d.source, target=d.target, type=d.type) for d in res_dp.scalars().all()]
    
    # Languages
    res_ln = await db.execute(select(DetectedLanguageModel).filter(DetectedLanguageModel.snapshot_id == uuid.UUID(id)))
    languages = [DetectedLanguageSchema(id=str(l.id), language=l.language, file_count=l.file_count, line_count=l.line_count, percentage=l.percentage) for l in res_ln.scalars().all()]
    
    return MetadataResponse(
        snapshot_id=id,
        folders=folders,
        files=files,
        chunks=chunks,
        dependencies=dependencies,
        languages=languages
    )

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_repository(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_developer)
):
    repo_repo = RepositoryRepository(db)
    repo = await repo_repo.get_repository(id)
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found."
        )
    await repo_repo.remove(uuid.UUID(id))
    await db.commit()
