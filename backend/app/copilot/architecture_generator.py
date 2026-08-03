from backend.app.copilot.base_generator import BaseGenerator
from backend.app.knowledge.knowledge_service import KnowledgeService


class ArchitectureGenerator(BaseGenerator):
    """
    Feature 2: Architecture Generator
    Generates high/low level designs, component relationships, and module mappings.
    """

    def __init__(self):
        super().__init__("ArchitectureGenerator", "architecture_generator")

    async def get_context_block(self, snapshot_id: str, query: str, knowledge_service: KnowledgeService) -> str:
        base_ctx = await super().get_context_block(snapshot_id, query, knowledge_service)
        
        # Load dependency flows
        deps = await knowledge_service.get_dependencies(snapshot_id)
        deps_list = "\n".join([f"- {d.get('source_path')} imports {d.get('target_path')} ({d.get('type')})" for d in deps[:30]])
        
        return (
            f"--- Repository Import Relationships ---\n"
            f"{deps_list}\n\n"
            f"--- Core Similarity Snippets ---\n"
            f"{base_ctx}"
        )
