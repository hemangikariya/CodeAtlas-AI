import logging
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

# Registry and Base
from backend.app.copilot.generator_registry import generator_registry
from backend.app.gateway.ai_gateway import AIGateway
from backend.app.knowledge.knowledge_service import KnowledgeService

# Generators
from backend.app.copilot.repository_explainer import RepositoryExplainer
from backend.app.copilot.architecture_generator import ArchitectureGenerator
from backend.app.copilot.adr_generator import ADRGenerator
from backend.app.copilot.api_designer import APIDesigner
from backend.app.copilot.documentation_generator import DocumentationGenerator
from backend.app.copilot.test_plan_generator import TestPlanGenerator
from backend.app.copilot.refactoring_advisor import RefactoringAdvisor
from backend.app.copilot.code_review_assistant import CodeReviewAssistant
from backend.app.copilot.sprint_planner import SprintPlanner
from backend.app.copilot.implementation_planner import ImplementationPlanner
from backend.app.copilot.onboarding_generator import OnboardingGenerator
from backend.app.copilot.dependency_analyzer import DependencyAnalyzer

logger = logging.getLogger("codeatlas.copilot")


class EngineeringCopilot:
    """
    Unified facade driving the Engineering Copilot.
    Dispatches artifact creation requests to the appropriate generator.
    """

    def __init__(self, gateway: AIGateway):
        self.gateway = gateway
        
        # Self-register generators in registry
        generator_registry.register(RepositoryExplainer())
        generator_registry.register(ArchitectureGenerator())
        generator_registry.register(ADRGenerator())
        generator_registry.register(APIDesigner())
        generator_registry.register(DocumentationGenerator())
        generator_registry.register(TestPlanGenerator())
        generator_registry.register(RefactoringAdvisor())
        generator_registry.register(CodeReviewAssistant())
        generator_registry.register(SprintPlanner())
        generator_registry.register(ImplementationPlanner())
        generator_registry.register(OnboardingGenerator())
        generator_registry.register(DependencyAnalyzer())

    async def generate_artifact(
        self,
        db: AsyncSession,
        artifact_type: str,
        query: str,
        snapshot_id: str,
        repository_id: str
    ) -> Dict[str, Any]:
        """
        Loads the corresponding generator and triggers structured content compilation.
        """
        logger.info(f"EngineeringCopilot: Dispatching generate request for type: '{artifact_type}'")
        
        generator = generator_registry.get(artifact_type)
        service = KnowledgeService(db)
        
        return await generator.generate(
            db=db,
            query=query,
            snapshot_id=snapshot_id,
            repository_id=repository_id,
            knowledge_service=service,
            gateway=self.gateway
        )
