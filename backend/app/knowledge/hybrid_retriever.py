import uuid
from typing import List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.knowledge.embeddings.embedding_service import EmbeddingService
from backend.app.knowledge.vector_store.vector_store_factory import VectorStoreFactory
from backend.app.knowledge.graph.graph_traversal import GraphTraversal
from backend.app.knowledge.ranking import RankingEngine
from backend.app.knowledge.context_builder import ContextBuilder
from backend.app.knowledge.retrieval_cache import RetrievalCache

from backend.app.adapters.models.code_chunk_model import CodeChunkModel
from backend.app.adapters.models.file_model import FileModel

class HybridRetriever:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStoreFactory.get_vector_store(db)
        self.graph_traversal = GraphTraversal(db)
        self.cache = RetrievalCache(db)

    async def retrieve(
        self,
        snapshot_id: str,
        query: str,
        top_k: int = 5,
        token_limit: int = 4000
    ) -> Dict[str, Any]:
        """
        Executes hybrid retrieval: caches check -> query embedding -> vector retrieval ->
        graph expansion -> metadata resolution -> ranking -> context building -> cache store.
        """
        sid = uuid.UUID(snapshot_id)
        
        # 1. Check Retrieval Cache
        cached = await self.cache.get(snapshot_id, query)
        if cached:
            # Reconstruct output contract from cache
            return {
                "query": query,
                "retrieved_chunks": [], # cached queries bypass individual lists
                "related_nodes": cached.get("retrieved_node_ids", []),
                "graph_context": [],
                "metadata": {"cached": True},
                "final_context": cached.get("context", "")
            }

        # 2. Generate Embedding Vector
        query_vector = self.embedding_service.embed_query(query)

        # 3. Vector Similarity Search
        sim_results = await self.vector_store.similarity_search(snapshot_id, query_vector, top_k=top_k)
        if not sim_results:
            return {
                "query": query,
                "retrieved_chunks": [],
                "related_nodes": [],
                "graph_context": [],
                "metadata": {"cached": False, "count": 0},
                "final_context": "No relevant context found."
            }

        # Match chunk_id list
        chunk_ids = [r[0] for r in sim_results]
        sim_scores_map = {r[0]: r[1] for r in sim_results}

        # 4. Graph Context Expansion
        # Find graph nodes that correspond to our initial chunk_ids
        from backend.app.adapters.models.graph_node_model import GraphNodeModel
        nodes_res = await self.db.execute(
            select(GraphNodeModel.id)
            .filter(
                GraphNodeModel.snapshot_id == sid,
                GraphNodeModel.entity_id.in_([uuid.UUID(cid) for cid in chunk_ids])
            )
        )
        initial_node_uuids = [str(uid) for uid in nodes_res.scalars().all()]
        
        graph_nodes, graph_edges = await self.graph_traversal.expand_graph(
            snapshot_id=snapshot_id,
            initial_node_ids=initial_node_uuids,
            max_depth=1
        )

        # 5. Fetch code chunks details and metadata
        chunk_details_res = await self.db.execute(
            select(CodeChunkModel, FileModel.path)
            .join(FileModel, FileModel.id == CodeChunkModel.file_id)
            .filter(CodeChunkModel.id.in_([uuid.UUID(cid) for cid in chunk_ids]))
        )
        
        chunks_with_scores: List[Tuple[Dict[str, Any], float]] = []
        for row in chunk_details_res.all():
            chunk_obj, file_path = row
            chunk_dict = {
                "id": str(chunk_obj.id),
                "file_id": str(chunk_obj.file_id),
                "name": chunk_obj.name,
                "type": chunk_obj.type,
                "content": chunk_obj.content,
                "start_line": chunk_obj.start_line,
                "end_line": chunk_obj.end_line,
                "file_path": file_path
            }
            chunks_with_scores.append((chunk_dict, sim_scores_map.get(str(chunk_obj.id), 0.0)))

        # 6. Rank Results
        ranked_results = RankingEngine.rank_chunks(
            chunks_with_scores=chunks_with_scores,
            query=query,
            graph_nodes=graph_nodes,
            graph_edges=graph_edges
        )

        # 7. Context Building
        final_ranked_chunk_dicts = [r[0] for r in ranked_results]
        final_context = ContextBuilder.build_context(final_ranked_chunk_dicts, token_limit=token_limit)

        # 8. Save to cache
        retrieved_node_ids = [n.get("id") for n in graph_nodes if n.get("id")]
        await self.cache.set(
            snapshot_id=snapshot_id,
            query=query,
            embedding_vector=query_vector,
            retrieved_node_ids=retrieved_node_ids,
            context=final_context
        )

        # 9. Return Contract
        return {
            "query": query,
            "retrieved_chunks": final_ranked_chunk_dicts,
            "related_nodes": retrieved_node_ids,
            "graph_context": {
                "nodes": graph_nodes,
                "edges": graph_edges
            },
            "metadata": {
                "cached": False,
                "total_retrieved": len(final_ranked_chunk_dicts),
                "embedding_provider": self.embedding_service.get_provider_name(),
                "embedding_version": self.embedding_service.get_version()
            },
            "final_context": final_context
        }
