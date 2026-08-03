from backend.app.copilot.base_generator import BaseGenerator
from backend.app.knowledge.knowledge_service import KnowledgeService


class APIDesigner(BaseGenerator):
    """
    Feature 4: API Designer
    Generates API endpoints layouts, request/response schemas, validation bounds, and OpenAPI specs.
    """

    def __init__(self):
        super().__init__("APIDesigner", "api_designer")

    async def get_context_block(self, snapshot_id: str, query: str, knowledge_service: KnowledgeService) -> str:
        # Search for route or controller files
        files = await knowledge_service.search_files(snapshot_id, "api")
        if not files:
            files = await knowledge_service.search_files(snapshot_id, "route")

        file_contexts = []
        for f in files[:3]:
            content = await knowledge_service.get_file_content(snapshot_id, f["path"])
            if content:
                file_contexts.append(f"--- Code Sample: {f['path']} ---\n{content[:1500]}")

        base_ctx = await super().get_context_block(snapshot_id, query, knowledge_service)
        return "\n\n".join(file_contexts) + f"\n\n--- Core Similarity Snippets ---\n{base_ctx}"
