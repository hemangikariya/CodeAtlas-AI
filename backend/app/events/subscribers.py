from backend.app.events.event_types import RepositoryUploadedEvent, SnapshotCompletedEvent
from backend.app.events.dispatcher import event_dispatcher
from backend.app.adapters.repositories.repository_repository import RepositoryRepository
from backend.app.adapters.repositories.snapshot_repository import SnapshotRepository
from backend.app.core.logging import logger

async def handle_repository_uploaded(event: RepositoryUploadedEvent):
    logger.info(f"Subscribed handler triggered for snapshot indexing: {event.snapshot_id}")
    from backend.app.usecases.ingestion import IngestRepositoryUseCase
    from backend.app.adapters.database.base import AsyncSessionLocal
    
    # Open isolated database connection for background execution
    async with AsyncSessionLocal() as db:
        repo_repo = RepositoryRepository(db)
        snap_repo = SnapshotRepository(db)
        
        # Instantiate usecase and run ingestion pipeline
        usecase = IngestRepositoryUseCase(repo_repo, snap_repo)
        try:
            await usecase.execute(event.snapshot_id, zip_file_path=event.file_path, local_dir_path=event.local_dir_path)
            await db.commit()
            logger.info(f"Ingestion pipeline completed successfully for snapshot: {event.snapshot_id}")
        except Exception as e:
            await db.rollback()
            logger.error(f"Ingestion pipeline failed for snapshot: {event.snapshot_id}: {str(e)}")
            # Mark snapshot failed in DB
            await snap_repo.update_snapshot_status(event.snapshot_id, "FAILED")
            await db.commit()

def register_subscribers():
    # Register subscribers to global event dispatcher
    event_dispatcher.subscribe(RepositoryUploadedEvent, handle_repository_uploaded)
