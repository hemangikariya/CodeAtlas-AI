import time
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

# Authentication and config
from backend.app.core.dependencies import get_db, get_current_active_developer
from backend.app.domain.models import User

# Schemas
from backend.app.schemas.ai import AIQueryRequest, AIChatResponse

# AI Infrastructure
from backend.app.gateway.ai_gateway import AIGateway
from backend.app.guardrails.safety import SafetyGuardrails
from backend.app.memory.memory_manager import MemoryManager
from backend.app.mcp.tool_executor import ToolExecutor
from backend.app.agents.planner_agent import PlannerAgent
from backend.app.agents.task_router import TaskRouter
from backend.app.agents.response_synthesizer import ResponseSynthesizer
from backend.app.logging.agent_logs import AgentWorkflowLogger
from backend.app.knowledge.knowledge_service import KnowledgeService

router = APIRouter()


async def execute_agent_pipeline(
    req: AIQueryRequest,
    plan: dict,
    db: AsyncSession
) -> AIChatResponse:
    """
    Core executor function driving safety checks, tool routing, specialized agent
    reasoning, execution logging, and output syntheses.
    """
    gateway = AIGateway()
    guardrails = SafetyGuardrails(gateway)

    # 1. Input Guardrail prompt injection checks
    start_time = time.time()
    is_safe = await guardrails.check_input_prompt(req.query)
    if not is_safe:
        AgentWorkflowLogger.log_error("InputGuardrails", f"Blocked unsafe query: '{req.query}'")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request flagged by safety guardrails as potentially dangerous or injection attempt."
        )

    # 2. Setup Services & Executors
    memory = MemoryManager()
    memory.add_message("user", req.query)
    
    tool_executor = ToolExecutor(guardrails)
    knowledge_service = KnowledgeService(db)
    
    router_agent = TaskRouter(gateway, memory, tool_executor)
    synthesizer = ResponseSynthesizer(gateway)

    # 3. Router dispatch & execute
    try:
        agent_outputs = await router_agent.route_and_execute(
            plan=plan,
            query=req.query,
            knowledge_service=knowledge_service,
            snapshot_id=req.snapshot_id
        )
    except Exception as e:
        AgentWorkflowLogger.log_error("TaskRouter", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Task routing execution encountered a critical error: {str(e)}"
        )

    # 4. Final synthesis compilation
    try:
        synthesized_text = await synthesizer.synthesize(
            query=req.query,
            plan=plan,
            agent_outputs=agent_outputs
        )
    except Exception as e:
        AgentWorkflowLogger.log_error("ResponseSynthesizer", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Final response synthesis failed: {str(e)}"
        )

    # 5. Output Guardrail sanitizations
    sanitized_response = guardrails.sanitize_response(synthesized_text)
    
    # 6. Log execution latency and token metrics
    latency = time.time() - start_time
    total_tokens = gateway.total_prompt_tokens + gateway.total_completion_tokens
    
    AgentWorkflowLogger.log_gateway(
        model=plan.get("intent", "general"),
        prompt_tokens=gateway.total_prompt_tokens,
        completion_tokens=gateway.total_completion_tokens,
        latency=latency,
        cost=gateway.calculate_cost(gateway.total_prompt_tokens, gateway.total_completion_tokens, "gemini-1.5-pro")
    )

    return AIChatResponse(
        response=sanitized_response,
        plan=plan,
        total_cost=gateway.calculate_cost(gateway.total_prompt_tokens, gateway.total_completion_tokens, "gemini-1.5-pro"),
        total_tokens=total_tokens
    )


@router.post("/chat", response_model=AIChatResponse)
async def chat_interaction(
    req: AIQueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_developer)
):
    """
    POST /api/v1/ai/chat
    General multi-agent dialog loop routing query requests via Cognitive Planner.
    """
    gateway = AIGateway()
    planner = PlannerAgent(gateway)
    
    # Formulate Plan
    start_time = time.time()
    plan = await planner.create_plan(req.query)
    latency = time.time() - start_time
    AgentWorkflowLogger.log_planner(req.query, plan, latency)

    return await execute_agent_pipeline(req, plan, db)


@router.post("/analyze", response_model=AIChatResponse)
async def analyze_interaction(
    req: AIQueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_developer)
):
    """
    POST /api/v1/ai/analyze
    General repository audit analyzing multiple source files and structure logic.
    """
    # Simply delegates to planner for dynamic routing
    return await chat_interaction(req, db, current_user)


@router.post("/search", response_model=AIChatResponse)
async def search_interaction(
    req: AIQueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_developer)
):
    """
    POST /api/v1/ai/search
    Dedicated semantic chunk and keyword file lookups.
    """
    plan = {
        "intent": "code_search",
        "complexity": "low",
        "tasks": [
            {
                "agent": "SearchAgent",
                "tool": "SemanticSearch",
                "priority": 1,
                "arguments": {"query": req.query, "search_type": "ALL", "top_k": 5}
            }
        ]
    }
    return await execute_agent_pipeline(req, plan, db)


@router.post("/architecture", response_model=AIChatResponse)
async def architecture_interaction(
    req: AIQueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_developer)
):
    """
    POST /api/v1/ai/architecture
    Evaluates packages, class relations, and design pattern flows.
    """
    plan = {
        "intent": "architecture_analysis",
        "complexity": "medium",
        "tasks": [
            {
                "agent": "ArchitectureAgent",
                "tool": "DependencyLookup",
                "priority": 1,
                "arguments": {}
            }
        ]
    }
    return await execute_agent_pipeline(req, plan, db)


@router.post("/documentation", response_model=AIChatResponse)
async def documentation_interaction(
    req: AIQueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_developer)
):
    """
    POST /api/v1/ai/documentation
    Analyzes documentation quality, README configurations, and comment alignments.
    """
    plan = {
        "intent": "documentation_review",
        "complexity": "low",
        "tasks": [
            {
                "agent": "DocumentationAgent",
                "tool": "ContextBuilder",
                "priority": 1,
                "arguments": {"query": f"documentation README docstrings {req.query}", "search_type": "DOCUMENTATION", "token_limit": 4000}
            }
        ]
    }
    return await execute_agent_pipeline(req, plan, db)


@router.post("/security", response_model=AIChatResponse)
async def security_interaction(
    req: AIQueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_developer)
):
    """
    POST /api/v1/ai/security
    Runs vulnerability checks and unsafe programming structure searches.
    """
    plan = {
        "intent": "security_audit",
        "complexity": "medium",
        "tasks": [
            {
                "agent": "SecurityAgent",
                "tool": "SemanticSearch",
                "priority": 1,
                "arguments": {"query": f"security vulnerabilities credentials SQL injection authorization {req.query}", "search_type": "ALL", "top_k": 5}
            }
        ]
    }
    return await execute_agent_pipeline(req, plan, db)


@router.post("/quality", response_model=AIChatResponse)
async def quality_interaction(
    req: AIQueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_developer)
):
    """
    POST /api/v1/ai/quality
    Audits AST sizes, connected components, and metrics.
    """
    plan = {
        "intent": "quality_review",
        "complexity": "low",
        "tasks": [
            {
                "agent": "QualityAgent",
                "tool": "StatisticsLookup",
                "priority": 1,
                "arguments": {}
            }
        ]
    }
    return await execute_agent_pipeline(req, plan, db)
