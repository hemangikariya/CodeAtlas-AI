import uuid
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.knowledge.semantic_search import SemanticSearch
from backend.app.knowledge.hybrid_retriever import HybridRetriever
from backend.app.knowledge.graph.graph_repository import GraphRepository
from backend.app.knowledge.graph.graph_queries import GraphQueries


class KnowledgeService:
    """
    Unified facade service exposing Knowledge Layer retrieval, graph query traversals,
    statistics lookup, and context assembly interfaces. This is the exclusive
    boundary that the AI Layer utilizes to access repository intelligence.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.semantic_search = SemanticSearch(db)
        self.retriever = HybridRetriever(db)
        self.graph_repo = GraphRepository(db)
        self.graph_queries = GraphQueries(db)

    async def search(
        self,
        snapshot_id: str,
        query: str,
        search_type: str = "ALL",
        top_k: int = 5,
        token_limit: int = 4000
    ) -> Dict[str, Any]:
        """
        Executes hybrid semantic search on the repository snapshot.
        """
        return await self.semantic_search.search(
            snapshot_id=snapshot_id,
            query=query,
            search_type=search_type,
            top_k=top_k,
            token_limit=token_limit
        )

    async def get_context(
        self,
        snapshot_id: str,
        query: str,
        search_type: str = "ALL",
        top_k: int = 5,
        token_limit: int = 4000
    ) -> str:
        """
        Compiles relevant context snippets for LLM prompting, adhering to token budget limit.
        """
        res = await self.search(
            snapshot_id=snapshot_id,
            query=query,
            search_type=search_type,
            top_k=top_k,
            token_limit=token_limit
        )
        return res.get("final_context", "")

    async def get_graph(self, snapshot_id: str) -> Dict[str, Any]:
        """
        Retrieves all graph nodes and edges stored for the snapshot.
        """
        sid = uuid.UUID(snapshot_id)
        nodes = await self.graph_repo.get_snapshot_nodes(sid)
        edges = await self.graph_repo.get_snapshot_edges(sid)
        return {
            "nodes": [
                {
                    "id": str(n.id),
                    "snapshot_id": str(n.snapshot_id),
                    "entity_id": str(n.entity_id) if n.entity_id else None,
                    "name": n.name,
                    "type": n.type,
                    "properties": n.properties
                }
                for n in nodes
            ],
            "edges": [
                {
                    "id": str(e.id),
                    "snapshot_id": str(e.snapshot_id),
                    "source_node_id": str(e.source_node_id),
                    "target_node_id": str(e.target_node_id),
                    "type": e.type,
                    "properties": e.properties
                }
                for e in edges
            ]
        }

    async def get_statistics(self, snapshot_id: str) -> Dict[str, Any]:
        """
        Calculates interconnected network stats.
        """
        return await self.graph_queries.get_graph_statistics(snapshot_id)

    async def get_node_by_id(self, snapshot_id: str, node_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves properties for a specific graph node.
        """
        node = await self.graph_repo.get_node(uuid.UUID(node_id))
        if not node or str(node.snapshot_id) != snapshot_id:
            return None
        return {
            "id": str(node.id),
            "snapshot_id": str(node.snapshot_id),
            "entity_id": str(node.entity_id) if node.entity_id else None,
            "name": node.name,
            "type": node.type,
            "properties": node.properties
        }

    async def get_similar_chunks(self, snapshot_id: str, chunk_id: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Finds sibling chunks with highest cosine similarity relative to target chunk.
        """
        cid = uuid.UUID(chunk_id)
        sid = uuid.UUID(snapshot_id)

        from backend.app.adapters.models.embedding_model import EmbeddingModel
        from backend.app.adapters.models.code_chunk_model import CodeChunkModel

        # Fetch the embedding vector of the source chunk
        emb_res = await self.db.execute(
            select(EmbeddingModel).filter(EmbeddingModel.chunk_id == cid)
        )
        emb = emb_res.scalar_one_or_none()
        if not emb:
            return []

        # Query similarities from vector store
        from backend.app.knowledge.vector_store.vector_store_factory import VectorStoreFactory
        store = VectorStoreFactory.get_store(self.db)
        sim_res = await store.search_similar(
            snapshot_id=sid,
            query_vector=emb.vector,
            top_k=top_k
        )

        matched_chunk_ids = [uuid.UUID(r[0]) for r in sim_res]
        if not matched_chunk_ids:
            return []

        # Load original chunk structures
        chunk_res = await self.db.execute(
            select(CodeChunkModel).filter(CodeChunkModel.id.in_(matched_chunk_ids))
        )
        chunks = chunk_res.scalars().all()
        chunk_map = {str(c.id): c for c in chunks}

        results = []
        for match_id, score in sim_res:
            c = chunk_map.get(match_id)
            if c:
                results.append({
                    "chunk_id": match_id,
                    "name": c.name,
                    "type": c.type,
                    "content": c.content,
                    "start_line": c.start_line,
                    "end_line": c.end_line,
                    "similarity": score
                })
        return results

    async def get_file_content(self, snapshot_id: str, path: str) -> Optional[str]:
        """
        Loads source code content for a target file.
        """
        from backend.app.adapters.models.file_model import FileModel
        res = await self.db.execute(
            select(FileModel).filter(
                FileModel.snapshot_id == uuid.UUID(snapshot_id),
                FileModel.path == path
            )
        )
        file = res.scalar_one_or_none()
        return file.content_chunk if file else None

    async def search_files(self, snapshot_id: str, pattern: str) -> List[Dict[str, Any]]:
        """
        Searches matching project files.
        """
        from backend.app.adapters.models.file_model import FileModel
        res = await self.db.execute(
            select(FileModel).filter(
                FileModel.snapshot_id == uuid.UUID(snapshot_id),
                FileModel.path.like(f"%{pattern}%")
            )
        )
        files = res.scalars().all()
        return [{"id": str(f.id), "path": f.path, "size": len(f.content_chunk)} for f in files]

    async def get_dependencies(self, snapshot_id: str) -> List[Dict[str, Any]]:
        """
        Loads all snapshot import and external package references.
        """
        from backend.app.adapters.models.dependency_model import DependencyModel
        res = await self.db.execute(
            select(DependencyModel).filter(DependencyModel.snapshot_id == uuid.UUID(snapshot_id))
        )
        deps = res.scalars().all()
        return [{"id": str(d.id), "source": d.source, "target": d.target, "type": d.type} for d in deps]
