import json
from backend.app.copilot.base_generator import BaseGenerator
from backend.app.knowledge.knowledge_service import KnowledgeService


class RepositoryExplainer(BaseGenerator):
    """
    Feature 1: Repository Explainer
    Generates overview, folder structure, technologies, request flows, and statistics.
    """

    def __init__(self):
        super().__init__("RepositoryExplainer", "repository_explainer")

    async def get_context_block(self, snapshot_id: str, query: str, knowledge_service: KnowledgeService) -> str:
        base_ctx = await super().get_context_block(snapshot_id, query, knowledge_service)
        
        # Load extra graph statistics and sample files list
        stats = await knowledge_service.get_statistics(snapshot_id)
        files = await knowledge_service.search_files(snapshot_id, "")
        files_list = "\n".join([f"- {f['path']}" for f in files[:25]])
        
        return (
            f"--- Repository Graph Statistics ---\n"
            f"{json.dumps(stats, indent=2)}\n\n"
            f"--- Repository Files (Sample) ---\n"
            f"{files_list}\n\n"
            f"--- Repository Similarity Snippets ---\n"
            f"{base_ctx}"
        )
