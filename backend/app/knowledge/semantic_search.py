from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.knowledge.hybrid_retriever import HybridRetriever

class SemanticSearch:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.retriever = HybridRetriever(db)

    async def search(
        self,
        snapshot_id: str,
        query: str,
        search_type: str = "ALL", # "ALL", "FUNCTION", "CLASS", "API", "DEPENDENCY", "DOCUMENTATION"
        top_k: int = 5,
        token_limit: int = 4000
    ) -> Dict[str, Any]:
        """
        Executes semantic query processing routing, adapting retrieval parameters based on intent classification.
        """
        # Adapt query keywords or boost intents depending on search type
        refined_query = query
        if search_type == "FUNCTION":
            refined_query = f"function method {query}"
        elif search_type == "CLASS":
            refined_query = f"class interface struct {query}"
        elif search_type == "API":
            refined_query = f"api router endpoint path route http {query}"
        elif search_type == "DEPENDENCY":
            refined_query = f"import package library require depend {query}"
        elif search_type == "DOCUMENTATION":
            refined_query = f"readme documentation docstring md description {query}"

        # Execute hybrid retrieval
        retrieval_result = await self.retriever.retrieve(
            snapshot_id=snapshot_id,
            query=refined_query,
            top_k=top_k,
            token_limit=token_limit
        )

        # Inject search classification details into metadata
        retrieval_result["metadata"]["search_type"] = search_type
        retrieval_result["metadata"]["original_query"] = query

        return retrieval_result
