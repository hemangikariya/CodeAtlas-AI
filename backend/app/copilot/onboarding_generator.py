from backend.app.copilot.base_generator import BaseGenerator
from backend.app.knowledge.knowledge_service import KnowledgeService


class OnboardingGenerator(BaseGenerator):
    """
    Feature 11: Onboarding Generator
    Generates developer setup instructions, coding conventions, workflows.
    """

    def __init__(self):
        super().__init__("OnboardingGenerator", "onboarding_generator")

    async def get_context_block(self, snapshot_id: str, query: str, knowledge_service: KnowledgeService) -> str:
        files = await knowledge_service.search_files(snapshot_id, "")
        structure = "\n".join([f"- {f['path']}" for f in files[:20]])
        
        base_ctx = await super().get_context_block(snapshot_id, query, knowledge_service)
        return (
            f"--- Repository Files structure ---\n"
            f"{structure}\n\n"
            f"--- Core Similarity Snippets ---\n"
            f"{base_ctx}"
        )
