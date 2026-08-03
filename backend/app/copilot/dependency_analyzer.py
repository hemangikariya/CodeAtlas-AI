from backend.app.copilot.base_generator import BaseGenerator
from backend.app.knowledge.knowledge_service import KnowledgeService


class DependencyAnalyzer(BaseGenerator):
    """
    Feature 12: Dependency Analyzer
    Generates dependency tree visual representations, circular import checks, and risks recommendations.
    """

    def __init__(self):
        super().__init__("DependencyAnalyzer", "dependency_analyzer")

    async def get_context_block(self, snapshot_id: str, query: str, knowledge_service: KnowledgeService) -> str:
        deps = await knowledge_service.get_dependencies(snapshot_id)
        deps_list = "\n".join([f"- {d.get('source_path')} -> {d.get('target_path')} ({d.get('type')})" for d in deps])
        
        base_ctx = await super().get_context_block(snapshot_id, query, knowledge_service)
        return (
            f"--- Repository Linkage Dependency Nodes ---\n"
            f"{deps_list}\n\n"
            f"--- Core Similarity Snippets ---\n"
            f"{base_ctx}"
        )
