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
            
            # --- PHASE 3: KNOWLEDGE LAYER GENERATION ---
            logger.info(f"Starting Knowledge Layer generation for snapshot: {event.snapshot_id}")
            import os
            import uuid
            from sqlalchemy.future import select
            from backend.app.adapters.models.code_chunk_model import CodeChunkModel
            from backend.app.adapters.models.file_model import FileModel
            
            stmt = select(CodeChunkModel).join(FileModel).filter(FileModel.snapshot_id == uuid.UUID(event.snapshot_id))
            chunk_rows = await db.execute(stmt)
            chunks = list(chunk_rows.scalars().all())
            
            if chunks:
                logger.info(f"Generating embeddings for {len(chunks)} code chunks...")
                from backend.app.knowledge.embeddings.embedding_service import EmbeddingService
                from backend.app.knowledge.vector_store.vector_store_factory import VectorStoreFactory
                
                emb_service = EmbeddingService()
                vector_store = VectorStoreFactory.get_vector_store(db)
                
                chunk_ids = [str(c.id) for c in chunks]
                chunk_contents = [c.content for c in chunks]
                
                batch_size = 100
                for i in range(0, len(chunks), batch_size):
                    batch_ids = chunk_ids[i:i+batch_size]
                    batch_contents = chunk_contents[i:i+batch_size]
                    vectors = emb_service.embed_documents(batch_contents)
                    
                    await vector_store.add_embeddings(
                        chunk_ids=batch_ids,
                        vectors=vectors,
                        provider=emb_service.get_provider_name(),
                        version=emb_service.get_version()
                    )
                logger.info(f"Embeddings saved successfully.")
            
            logger.info(f"Constructing Knowledge Graph nodes and edges...")
            from backend.app.knowledge.graph.graph_builder import GraphBuilder
            graph_builder = GraphBuilder(db)
            await graph_builder.build_graph(event.snapshot_id)
            logger.info(f"Knowledge Graph created successfully.")
            
            await db.commit()
            logger.info(f"Ingestion pipeline and Knowledge generation completed successfully for snapshot: {event.snapshot_id}")
        except Exception as e:
            await db.rollback()
            logger.error(f"Ingestion pipeline failed for snapshot: {event.snapshot_id}: {str(e)}")
            # Mark snapshot failed in DB
            await snap_repo.update_snapshot_status(event.snapshot_id, "FAILED")
            await db.commit()

def register_subscribers():
    # Register subscribers to global event dispatcher
    event_dispatcher.subscribe(RepositoryUploadedEvent, handle_repository_uploaded)
