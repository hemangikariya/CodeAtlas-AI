from backend.app.copilot.base_generator import BaseGenerator
from backend.app.knowledge.knowledge_service import KnowledgeService


class DocumentationGenerator(BaseGenerator):
    """
    Feature 5: Documentation Generator
    Generates READMEs, module guides, API specifications, and setup/deployment guides.
    """

    def __init__(self):
        super().__init__("DocumentationGenerator", "documentation_generator")

    async def get_context_block(self, snapshot_id: str, query: str, knowledge_service: KnowledgeService) -> str:
        files = await knowledge_service.search_files(snapshot_id, "readme")
        readme_content = ""
        if files:
            content = await knowledge_service.get_file_content(snapshot_id, files[0]["path"])
            if content:
                readme_content = f"--- Current README.md ---\n{content[:2000]}\n\n"

        base_ctx = await super().get_context_block(snapshot_id, query, knowledge_service)
        return f"{readme_content}--- Core Similarity Snippets ---\n{base_ctx}"
