from backend.app.copilot.base_generator import BaseGenerator
from backend.app.knowledge.knowledge_service import KnowledgeService


class TestPlanGenerator(BaseGenerator):
    """
    Feature 6: Test Plan Generator
    Generates test specs (unit, integration, edge cases, APIs, security scenarios).
    """

    def __init__(self):
        super().__init__("TestPlanGenerator", "test_plan_generator")

    async def get_context_block(self, snapshot_id: str, query: str, knowledge_service: KnowledgeService) -> str:
        files = await knowledge_service.search_files(snapshot_id, "test")
        test_samples = []
        for f in files[:3]:
            content = await knowledge_service.get_file_content(snapshot_id, f["path"])
            if content:
                test_samples.append(f"--- Test Sample: {f['path']} ---\n{content[:1200]}")

        base_ctx = await super().get_context_block(snapshot_id, query, knowledge_service)
        return "\n\n".join(test_samples) + f"\n\n--- Core Similarity Snippets ---\n{base_ctx}"
