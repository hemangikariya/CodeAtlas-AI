from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
import uuid

from backend.app.adapters.models.snapshot_model import SnapshotModel
from backend.app.adapters.models.folder_model import FolderModel
from backend.app.adapters.models.file_model import FileModel
from backend.app.adapters.models.code_chunk_model import CodeChunkModel
from backend.app.adapters.models.dependency_model import DependencyModel
from backend.app.adapters.models.detected_language_model import DetectedLanguageModel

from backend.app.adapters.repositories.base_repository import BaseRepository
from backend.app.domain.ingestion import (
    RepositorySnapshot, Folder, File, CodeChunk, Dependency, DetectedLanguage, RepositoryStatistics
)

class SnapshotRepository(BaseRepository[SnapshotModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(SnapshotModel, db)

    def _to_domain(self, model: SnapshotModel) -> RepositorySnapshot:
        return RepositorySnapshot(
            id=str(model.id),
            repository_id=str(model.repository_id),
            branch=model.branch,
            commit_sha=model.commit_sha,
            version=model.version,
            status=model.status,
            upload_time=model.upload_time,
            created_at=model.created_at
        )

    async def get_snapshot(self, snapshot_id: str) -> Optional[RepositorySnapshot]:
        try:
            uid = uuid.UUID(snapshot_id)
        except ValueError:
            return None
        model = await self.get(uid)
        if model:
            return self._to_domain(model)
        return None

    async def get_repository_snapshots(self, repo_id: str) -> List[RepositorySnapshot]:
        try:
            rid = uuid.UUID(repo_id)
        except ValueError:
            return []
        result = await self.db.execute(
            select(SnapshotModel)
            .filter(SnapshotModel.repository_id == rid)
            .order_by(SnapshotModel.created_at.desc())
        )
        models = result.scalars().all()
        return [self._to_domain(m) for m in models]

    async def create_snapshot(self, snap: RepositorySnapshot) -> RepositorySnapshot:
        model = SnapshotModel(
            id=uuid.UUID(snap.id),
            repository_id=uuid.UUID(snap.repository_id),
            branch=snap.branch,
            commit_sha=snap.commit_sha,
            version=snap.version,
            status=snap.status,
            upload_time=snap.upload_time,
            created_at=snap.created_at
        )
        created_model = await self.create(model)
        return self._to_domain(created_model)

    async def update_snapshot_status(self, snapshot_id: str, status: str) -> Optional[RepositorySnapshot]:
        try:
            uid = uuid.UUID(snapshot_id)
        except ValueError:
            return None
        model = await self.get(uid)
        if model:
            model.status = status
            await self.db.flush()
            return self._to_domain(model)
        return None

    async def save_indexing_results(
        self,
        snapshot_id: str,
        folders: List[Folder],
        files: List[File],
        chunks: List[CodeChunk],
        deps: List[Dependency],
        langs: List[DetectedLanguage]
    ) -> None:
        sid = uuid.UUID(snapshot_id)
        
        # Save folders
        folder_id_map = {}
        for folder in folders:
            db_folder = FolderModel(
                id=uuid.UUID(folder.id),
                snapshot_id=sid,
                name=folder.name,
                path=folder.path,
                parent_folder_id=uuid.UUID(folder.parent_folder_id) if folder.parent_folder_id else None
            )
            self.db.add(db_folder)
            folder_id_map[folder.path] = db_folder.id

        await self.db.flush()

        # Save files
        file_id_map = {}
        for file in files:
            # Find parent folder path
            # We split the file path and check if the parent directory matches one of our folder paths
            db_file = FileModel(
                id=uuid.UUID(file.id),
                snapshot_id=sid,
                folder_id=uuid.UUID(file.folder_id) if file.folder_id else None,
                name=file.name,
                path=file.path,
                content_chunk=file.content_chunk
            )
            self.db.add(db_file)
            file_id_map[file.id] = db_file.id

        await self.db.flush()

        # Save code chunks
        for chunk in chunks:
            db_chunk = CodeChunkModel(
                id=uuid.UUID(chunk.id),
                file_id=uuid.UUID(chunk.file_id),
                name=chunk.name,
                type=chunk.type,
                content=chunk.content,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                metadata_json=chunk.metadata
            )
            self.db.add(db_chunk)

        # Save dependencies
        for dep in deps:
            db_dep = DependencyModel(
                id=uuid.UUID(dep.id),
                snapshot_id=sid,
                source=dep.source,
                target=dep.target,
                type=dep.type
            )
            self.db.add(db_dep)

        # Save detected languages
        for lang in langs:
            db_lang = DetectedLanguageModel(
                id=uuid.UUID(lang.id),
                snapshot_id=sid,
                language=lang.language,
                file_count=lang.file_count,
                line_count=lang.line_count,
                percentage=lang.percentage
            )
            self.db.add(db_lang)

        await self.db.flush()

    async def get_snapshot_statistics(self, snapshot_id: str) -> Optional[RepositoryStatistics]:
        try:
            sid = uuid.UUID(snapshot_id)
        except ValueError:
            return None
        
        # Check if snapshot exists
        snap = await self.get(sid)
        if not snap:
            return None

        # Calculate statistics
        # Files Count
        res_files = await self.db.execute(select(func.count(FileModel.id)).filter(FileModel.snapshot_id == sid))
        total_files = res_files.scalar() or 0

        # Folders Count
        res_folders = await self.db.execute(select(func.count(FolderModel.id)).filter(FolderModel.snapshot_id == sid))
        total_folders = res_folders.scalar() or 0

        # Chunks metrics
        res_classes = await self.db.execute(
            select(func.count(CodeChunkModel.id))
            .join(FileModel)
            .filter(FileModel.snapshot_id == sid, CodeChunkModel.type == "CLASS")
        )
        total_classes = res_classes.scalar() or 0

        res_methods = await self.db.execute(
            select(func.count(CodeChunkModel.id))
            .join(FileModel)
            .filter(FileModel.snapshot_id == sid, CodeChunkModel.type == "METHOD")
        )
        total_methods = res_methods.scalar() or 0

        res_functions = await self.db.execute(
            select(func.count(CodeChunkModel.id))
            .join(FileModel)
            .filter(FileModel.snapshot_id == sid, CodeChunkModel.type == "FUNCTION")
        )
        total_functions = res_functions.scalar() or 0

        # Lines count: sum lines of all files
        # For simplicity, we can calculate LOC from line_count of detected languages
        res_loc = await self.db.execute(
            select(func.sum(DetectedLanguageModel.line_count)).filter(DetectedLanguageModel.snapshot_id == sid)
        )
        total_lines_of_code = res_loc.scalar() or 0

        # Dependencies Count
        res_deps = await self.db.execute(select(func.count(DependencyModel.id)).filter(DependencyModel.snapshot_id == sid))
        total_dependencies = res_deps.scalar() or 0

        # Languages Count
        res_langs = await self.db.execute(select(func.count(DetectedLanguageModel.id)).filter(DetectedLanguageModel.snapshot_id == sid))
        total_languages = res_langs.scalar() or 0

        return RepositoryStatistics(
            snapshot_id=snapshot_id,
            total_files=total_files,
            total_folders=total_folders,
            total_classes=total_classes,
            total_methods=total_methods,
            total_functions=total_functions,
            total_lines_of_code=total_lines_of_code,
            total_dependencies=total_dependencies,
            total_languages=total_languages
        )
