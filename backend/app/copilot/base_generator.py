import time
import json
import logging
from datetime import datetime
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.gateway.ai_gateway import AIGateway
from backend.app.knowledge.knowledge_service import KnowledgeService
from backend.app.prompts.prompt_registry import prompt_registry
from backend.app.adapters.models.generated_artifact_model import GeneratedArtifactModel

logger = logging.getLogger("codeatlas.copilot")


class BaseGenerator:
    """
    Common base class for all Engineering Copilot Generators.
    Encapsulates static prompt retrieval, LLM query execution, validation, and historical persistence.
    """

    def __init__(self, name: str, artifact_type: str, version: str = "1.0"):
        self.name = name
        self.artifact_type = artifact_type
        self.version = version

    async def get_context_block(self, snapshot_id: str, query: str, knowledge_service: KnowledgeService) -> str:
        """
        Gathers related files, graph metadata, or semantic chunks to establish LLM context.
        Can be overridden by specialized subclasses.
        """
        # Default behavior: assemble token-bounded similarity context block
        try:
            return await knowledge_service.get_context(
                snapshot_id=snapshot_id,
                query=query,
                search_type="ALL",
                token_limit=4000
            )
        except Exception as e:
            logger.warning(f"Failed to gather similarity context for {self.name}: {str(e)}. Defaulting to empty context.")
            return "No repository context available."

    async def generate(
        self,
        db: AsyncSession,
        query: str,
        snapshot_id: str,
        repository_id: str,
        knowledge_service: KnowledgeService,
        gateway: AIGateway
    ) -> Dict[str, Any]:
        """
        Drives the complete compilation cycle: gathers context, formats prompt, calls gateway,
        validates output structure, and persists artifact metadata to database history.
        """
        logger.info(f"Copilot Generator '{self.name}' initiated for snapshot: {snapshot_id}")
        
        # 1. Retrieve Context
        context = await self.get_context_block(snapshot_id, query, knowledge_service)

        # 2. Format Prompt
        created_at_str = datetime.utcnow().isoformat() + "Z"
        prompt_name = f"copilot/{self.artifact_type}"
        
        prompt = prompt_registry.get_prompt(
            prompt_name,
            context=context,
            query=query,
            snapshot_id=snapshot_id,
            created_at=created_at_str
        )

        # 3. Formulate JSON Schema validation
        schema = {
            "type": "OBJECT",
            "properties": {
                "title": {"type": "STRING"},
                "summary": {"type": "STRING"},
                "sections": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "heading": {"type": "STRING"},
                            "content": {"type": "STRING"}
                        },
                        "required": ["heading", "content"]
                    }
                },
                "references": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"}
                },
                "generator": {"type": "STRING"},
                "generator_version": {"type": "STRING"},
                "prompt_version": {"type": "STRING"},
                "knowledge_snapshot": {"type": "STRING"},
                "artifact_version": {"type": "STRING"},
                "created_at": {"type": "STRING"}
            },
            "required": ["title", "summary", "sections", "references", "generator", "generator_version", "prompt_version", "knowledge_snapshot", "artifact_version", "created_at"]
        }

        # 4. Generate structured output
        res = await gateway.generate_structured(
            prompt=prompt,
            response_schema=schema,
            task_type="copilot"
        )
        
        artifact_data = res.get("data", {})
        
        # Fallback in case LLM missed prompt fields
        if not self.validate(artifact_data):
            artifact_data = self.format_output(artifact_data, snapshot_id, created_at_str)

        # 5. Persist artifact to database
        import uuid as py_uuid
        model_ref = GeneratedArtifactModel(
            repository_id=py_uuid.UUID(repository_id) if isinstance(repository_id, str) else repository_id,
            snapshot_id=py_uuid.UUID(snapshot_id) if isinstance(snapshot_id, str) else snapshot_id,
            artifact_type=self.artifact_type,
            generator=self.name,
            artifact_version=self.version,
            prompt_version="1.0",
            llm_provider="Gemini",
            model_name="gemini-1.5-pro",
            content=artifact_data
        )
        db.add(model_ref)
        await db.commit()
        await db.refresh(model_ref)
        
        # Inject the generated artifact ID to output
        artifact_data["id"] = str(model_ref.id)
        return artifact_data

    def validate(self, artifact_dict: Dict[str, Any]) -> bool:
        """
        Asserts correctness of generated fields.
        """
        required = ["title", "summary", "sections", "references", "generator"]
        for key in required:
            if key not in artifact_dict or not artifact_dict[key]:
                return False
        return True

    def format_output(self, artifact_dict: Dict[str, Any], snapshot_id: str, created_at: str) -> Dict[str, Any]:
        """
        Applies schema default fallbacks in case of validation failures.
        """
        return {
            "title": artifact_dict.get("title", f"{self.name} Report"),
            "summary": artifact_dict.get("summary", "No summary provided by generator."),
            "sections": artifact_dict.get("sections", [{"heading": "Audit Findings", "content": str(artifact_dict)}]),
            "references": artifact_dict.get("references", []),
            "generator": self.name,
            "generator_version": self.version,
            "prompt_version": "1.0",
            "knowledge_snapshot": str(snapshot_id),
            "artifact_version": "1.0",
            "created_at": created_at
        }
