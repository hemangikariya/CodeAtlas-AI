import uuid
import base64
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# Auth & config
from backend.app.core.dependencies import get_db, get_current_active_developer
from backend.app.domain.models import User

# Models & Schemas
from backend.app.adapters.models.generated_artifact_model import GeneratedArtifactModel
from backend.app.schemas.copilot import (
    CopilotArtifactRequest,
    CopilotArtifactResponse,
    HistoricalArtifactListItem
)

# Core Gateway & Copilot
from backend.app.gateway.ai_gateway import AIGateway
from backend.app.copilot.engineering_copilot import EngineeringCopilot
from backend.app.export import MarkdownExporter, HTMLExporter, PDFExporter, JSONExporter

logger = logging.getLogger("codeatlas.copilot")
router = APIRouter()


def apply_export_format(artifact_data: dict, export_format: str) -> str:
    """
    Helper function rendering the structured JSON payload into Markdown, HTML, PDF, or JSON.
    """
    fmt = (export_format or "json").strip().lower()
    if fmt == "markdown":
        return MarkdownExporter.export(artifact_data)
    elif fmt == "html":
        return HTMLExporter.export(artifact_data)
    elif fmt == "pdf":
        pdf_bytes = PDFExporter.export(artifact_data)
        return base64.b64encode(pdf_bytes).decode("utf-8")
    else:
        return JSONExporter.export(artifact_data)


async def run_copilot_pipeline(
    req: CopilotArtifactRequest,
    artifact_type: str,
    db: AsyncSession
) -> CopilotArtifactResponse:
    """
    Core routing helper invoking the appropriate copilot generator and returning
    the formatted exported output content payload.
    """
    gateway = AIGateway()
    copilot = EngineeringCopilot(gateway)

    try:
        # Generate artifact (which also commits it to database history)
        artifact_data = await copilot.generate_artifact(
            db=db,
            artifact_type=artifact_type,
            query=req.query,
            snapshot_id=req.snapshot_id,
            repository_id=req.repository_id
        )

        # Apply target export format representation
        exported_content = apply_export_format(artifact_data, req.export_format)
        
        # Build schema response
        return CopilotArtifactResponse(
            id=artifact_data.get("id", str(uuid.uuid4())),
            title=artifact_data.get("title", ""),
            summary=artifact_data.get("summary", ""),
            sections=artifact_data.get("sections", []),
            references=artifact_data.get("references", []),
            generator=artifact_data.get("generator", ""),
            generator_version=artifact_data.get("generator_version", "1.0"),
            prompt_version=artifact_data.get("prompt_version", "1.0"),
            knowledge_snapshot=artifact_data.get("knowledge_snapshot", ""),
            artifact_version=artifact_data.get("artifact_version", "1.0"),
            created_at=artifact_data.get("created_at", ""),
            exported_content=exported_content
        )
    except Exception as e:
        logger.error(f"Copilot pipeline execution failed for '{artifact_type}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Engineering Copilot pipeline execution failed: {str(e)}"
        )


@router.post("/repository", response_model=CopilotArtifactResponse)
async def post_repository_explainer(
    req: CopilotArtifactRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_developer)
):
    """
    POST /api/v1/copilot/repository
    Generates folder overview, technologies stack, request/data flow.
    """
    return await run_copilot_pipeline(req, "repository_explainer", db)


@router.post("/architecture", response_model=CopilotArtifactResponse)
async def post_architecture_generator(
    req: CopilotArtifactRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_developer)
):
    """
    POST /api/v1/copilot/architecture
    Generates component blueprints, service mappings, dependency flows.
    """
    return await run_copilot_pipeline(req, "architecture_generator", db)


@router.post("/adr", response_model=CopilotArtifactResponse)
async def post_adr_generator(
    req: CopilotArtifactRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_developer)
):
    """
    POST /api/v1/copilot/adr
    Generates Architecture Decision Records documenting trade-offs.
    """
    return await run_copilot_pipeline(req, "adr_generator", db)


@router.post("/api-design", response_model=CopilotArtifactResponse)
async def post_api_designer(
    req: CopilotArtifactRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_developer)
):
    """
    POST /api/v1/copilot/api-design
    Generates REST APIs schemas, validation rules, OpenAPI templates.
    """
    return await run_copilot_pipeline(req, "api_designer", db)


@router.post("/documentation", response_model=CopilotArtifactResponse)
async def post_documentation_generator(
    req: CopilotArtifactRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_developer)
):
    """
    POST /api/v1/copilot/documentation
    Generates READMEs, setup steps, and module documentation guides.
    """
    return await run_copilot_pipeline(req, "documentation_generator", db)


@router.post("/test-plan", response_model=CopilotArtifactResponse)
async def post_test_plan_generator(
    req: CopilotArtifactRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_developer)
):
    """
    POST /api/v1/copilot/test-plan
    Generates QA test plan frameworks (unit, integration, security).
    """
    return await run_copilot_pipeline(req, "test_plan_generator", db)


@router.post("/refactor", response_model=CopilotArtifactResponse)
async def post_refactoring_advisor(
    req: CopilotArtifactRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_developer)
):
    """
    POST /api/v1/copilot/refactor
    Generates code refactoring advice, SOLID audits, complexity suggestions.
    """
    return await run_copilot_pipeline(req, "refactoring_advisor", db)


@router.post("/code-review", response_model=CopilotArtifactResponse)
async def post_code_review_assistant(
    req: CopilotArtifactRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_developer)
):
    """
    POST /api/v1/copilot/code-review
    Generates automated PR code review summaries, bug warnings, maintainability issues.
    """
    return await run_copilot_pipeline(req, "code_review_assistant", db)


@router.post("/sprint", response_model=CopilotArtifactResponse)
async def post_sprint_planner(
    req: CopilotArtifactRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_developer)
):
    """
    POST /api/v1/copilot/sprint
    Generates agile tasks list, epics, estimated user stories.
    """
    return await run_copilot_pipeline(req, "sprint_planner", db)


@router.post("/implementation-plan", response_model=CopilotArtifactResponse)
async def post_implementation_planner(
    req: CopilotArtifactRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_developer)
):
    """
    POST /api/v1/copilot/implementation-plan
    Generates program implementation roadmaps, milestones, timelines, risks.
    """
    return await run_copilot_pipeline(req, "implementation_planner", db)


@router.post("/onboarding", response_model=CopilotArtifactResponse)
async def post_onboarding_generator(
    req: CopilotArtifactRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_developer)
):
    """
    POST /api/v1/copilot/onboarding
    Generates new joiner project setup guides, folders overview, standards checklists.
    """
    return await run_copilot_pipeline(req, "onboarding_generator", db)


@router.post("/dependency-analysis", response_model=CopilotArtifactResponse)
async def post_dependency_analysis(
    req: CopilotArtifactRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_developer)
):
    """
    POST /api/v1/copilot/dependency-analysis
    Generates circular reference checks, imports diagrams mapping.
    """
    return await run_copilot_pipeline(req, "dependency_analyzer", db)


@router.get("/artifacts", response_model=List[HistoricalArtifactListItem])
async def list_artifacts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_developer)
):
    """
    GET /api/v1/copilot/artifacts
    Retrieves historical created artifact metadata items.
    """
    query = select(GeneratedArtifactModel).order_by(GeneratedArtifactModel.created_at.desc())
    res = await db.execute(query)
    artifacts = res.scalars().all()
    
    # Map to schema output
    output = []
    for art in artifacts:
        output.append(
            HistoricalArtifactListItem(
                id=str(art.id),
                repository_id=str(art.repository_id),
                snapshot_id=str(art.snapshot_id),
                artifact_type=art.artifact_type,
                generator=art.generator,
                artifact_version=art.artifact_version,
                prompt_version=art.prompt_version,
                llm_provider=art.llm_provider,
                model_name=art.model_name,
                created_at=str(art.created_at)
            )
        )
    return output


@router.get("/artifacts/{id}", response_model=CopilotArtifactResponse)
async def get_artifact(
    id: str,
    export_format: Optional[str] = "json",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_developer)
):
    """
    GET /api/v1/copilot/artifacts/{id}
    Retrieves and outputs specific historical artifact by database ID.
    """
    try:
        art_uuid = uuid.UUID(id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid UUID format."
        )

    query = select(GeneratedArtifactModel).where(GeneratedArtifactModel.id == art_uuid)
    res = await db.execute(query)
    art = res.scalar_one_or_none()
    if not art:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artifact with ID '{id}' was not found."
        )

    # Format content
    content = art.content
    exported_content = apply_export_format(content, export_format)

    return CopilotArtifactResponse(
        id=str(art.id),
        title=content.get("title", ""),
        summary=content.get("summary", ""),
        sections=content.get("sections", []),
        references=content.get("references", []),
        generator=content.get("generator", ""),
        generator_version=content.get("generator_version", "1.0"),
        prompt_version=content.get("prompt_version", "1.0"),
        knowledge_snapshot=content.get("knowledge_snapshot", ""),
        artifact_version=content.get("artifact_version", "1.0"),
        created_at=content.get("created_at", ""),
        exported_content=exported_content
    )


@router.delete("/artifacts/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_artifact(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_developer)
):
    """
    DELETE /api/v1/copilot/artifacts/{id}
    Deletes a specific generated artifact item from database history.
    """
    try:
        art_uuid = uuid.UUID(id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid UUID format."
        )

    query = select(GeneratedArtifactModel).where(GeneratedArtifactModel.id == art_uuid)
    res = await db.execute(query)
    art = res.scalar_one_or_none()
    if not art:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artifact with ID '{id}' was not found."
        )

    await db.delete(art)
    await db.commit()
    return None
