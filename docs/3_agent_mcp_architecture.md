# Agent & MCP Architecture - CodeAtlas AI Enterprise Platform

This document describes the design, cognitive workflows, safety validation stages, memory layers, and registry abstractions implemented for the **CodeAtlas AI Agent Layer** (Phase 4).

---

## 1. Agent Cognitive Pipeline Flow

The execution workflow is completely decoupled, isolating business logic, tool execution, safety checks, and memory:

```
              ┌────────────────────────────────────────────────────────┐
              │                       User Query                       │
              └────────────────────────────────────────┬───────────────┘
                                                       │
                                                       ▼
              ┌────────────────────────────────────────────────────────┐
              │                   Input Guardrails                     │
              │         (Heuristics & structured prompt checks)        │
              └────────────────────────────────────────┬───────────────┘
                                                       │
                                                       ▼
              ┌────────────────────────────────────────────────────────┐
              │                    Planner Agent                       │
              │        (Intent classification & subtasks JSON)         │
              └────────────────────────────────────────┬───────────────┘
                                                       │
                                                       ▼
              ┌────────────────────────────────────────────────────────┐
              │                     Task Router                        │
              │         (Sorts by priority, coordinates tools)         │
              └──────────────┬─────────────────────────┬───────────────┘
                             │                         │
                             ▼                         ▼
              ┌────────────────────────┐     ┌────────────────────────┐
              │    MCP Tool Registry   │     │   Specialized Agents   │
              │    (Validates schemas  │     │   (RepositoryAgent,    │
              │     & permissions)     │     │    SecurityAgent,      │
              └──────────────┬─────────┘     │    QualityAgent,       │
                             │               │    SearchAgent, etc.)  │
                             ▼               └─────────┬──────────────┘
              ┌────────────────────────┐               │
              │    KnowledgeService    │               │
              │  (Abstracts DB/Vector) │               │
              └────────────────────────┘               ▼
                                             ┌────────────────────────┐
                                             │  Response Synthesizer  │
                                             │  (Assembles final md)  │
                                             └─────────┬──────────────┘
                                                       │
                                                       ▼
              ┌────────────────────────────────────────────────────────┐
              │                   Output Guardrails                    │
              │             (Redacts secrets & sanitizes)              │
              └────────────────────────────────────────┬───────────────┘
                                                       │
                                                       ▼
              ┌────────────────────────────────────────────────────────┐
              │                     Final Response                     │
              └────────────────────────────────────────────────────────┘
```

---

## 2. Pluggable AI Gateway

Provides a unified interface to any LLM backends:

- **Abstractions**: [BaseProvider](file:///d:/CodeAtlas%20AI/backend/app/gateway/base_provider.py) defines standard contracts for content generations and structured outputs.
- **Gemini REST Client**: [GeminiProvider](file:///d:/CodeAtlas%20AI/backend/app/gateway/gemini_provider.py) executes HTTP calls asynchronously to Generative Language REST endpoints. Integrates a regex-driven mock logic for offline and unit testing environments.
- **Model Router**: [ModelRouter](file:///d:/CodeAtlas%20AI/backend/app/gateway/model_router.py) routes complex tasks (Planning, Synthesis) to `gemini-1.5-pro` and validation tasks to `gemini-1.5-flash`.
- **AIGateway**: [AIGateway](file:///d:/CodeAtlas%20AI/backend/app/gateway/ai_gateway.py) wraps calls with exponential backoff retries, calculates costs in USD, and logs token usage.

---

## 3. Cognitive Agents & Task Router

### Base & Planner Agents
- **BaseAgent**: Every specialized agent inherits from [BaseAgent](file:///d:/CodeAtlas%20AI/backend/app/agents/base_agent.py), implementing `plan()`, `execute()`, `validate()`, and `summarize()`.
- **PlannerAgent**: [PlannerAgent](file:///d:/CodeAtlas%20AI/backend/app/agents/planner_agent.py) executes intent detection, returns structured task steps in JSON (agent target, tool recommendation, priority, optional parameters). Never executes tools.

### Task Router
- **TaskRouter**: [TaskRouter](file:///d:/CodeAtlas%20AI/backend/app/agents/task_router.py) acts as the execution coordinator. Receives subtasks, sorts them by priority, executes recommended tools through the registry, passes tool outcomes as context to specialized agents, and collects reports. Does not contain agent business logic.

### Specialized Agents ([agents/specialized/](file:///d:/CodeAtlas%20AI/backend/app/agents/specialized))
- **RepositoryAgent**: Review files and directory contexts.
- **ArchitectureAgent**: Analyzes package imports and graph dependencies.
- **DocumentationAgent**: Audits README files and docstrings.
- **SecurityAgent**: Scans for vulnerability markers.
- **QualityAgent**: Audits code metrics and connected component statistics.
- **SearchAgent**: Performs similarity and file lookup operations.
- **AnalysisAgent**: Assesses logical flows and control structures.

---

## 4. MCP Tool Registry

A protocol registry ensuring tools implement the common interface [MCPTool](file:///d:/CodeAtlas%20AI/backend/app/mcp/tool_schema.py):

### Builtin Tools ([mcp/builtins/](file:///d:/CodeAtlas%20AI/backend/app/mcp/builtins))
1. **RepositorySearch**: Finds files matching keyword patterns.
2. **GraphSearch**: Retrieves nodes and relations.
3. **SemanticSearch**: Performs vector similarity search.
4. **FileReader**: Reads content files.
5. **DependencyLookup**: Loads import and package relationships.
6. **StatisticsLookup**: Computes connected subgraph statistics.
7. **ContextBuilder**: Packs code chunks into token budget.

All tools communicate with the database/vector store strictly via the **KnowledgeService** facade. Direct database queries from tools are blocked.

---

## 5. safety Guardrails

A multi-stage validator enforcing security and formatting:

1. **Prompt Validation**: [PromptValidator](file:///d:/CodeAtlas%20AI/backend/app/guardrails/prompt_validator.py) checks input queries for prompt injection patterns and unauthorized commands.
2. **Tool Validation**: [ToolPermissionValidator](file:///d:/CodeAtlas%20AI/backend/app/guardrails/tool_permission.py) prevents path traversals (`..` directory escapes) in `FileReader` arguments.
3. **JSON Validation**: [JSONSchemaValidator](file:///d:/CodeAtlas%20AI/backend/app/guardrails/json_validator.py) validates LLM outputs against required target schemas.
4. **Output Sanitization**: [OutputValidator](file:///d:/CodeAtlas%20AI/backend/app/guardrails/output_validator.py) redacts exposed credentials, secret keys, or passwords.

---

## 6. Prompt & Memory Management

### Prompt Templates
Prompts are loaded from filesystem template files located under [prompts/prompt_templates/](file:///d:/CodeAtlas%20AI/backend/app/prompts/prompt_templates) using the [PromptLoader](file:///d:/CodeAtlas%20AI/backend/app/prompts/prompt_loader.py), keeping Python source code clean of system instructions.

### Memory Layer
The [MemoryManager](file:///d:/CodeAtlas%20AI/backend/app/memory/memory_manager.py) exposes a unified interface encapsulating:
- **Conversation Memory**: Conversational chat history.
- **Repository Memory**: Snapshot metadata.
- **Session Memory**: Stateful request variables.

---

## 7. REST APIs Endpoints

Mounted under `/api/v1/ai/`:

- `POST /api/v1/ai/chat`: Multi-agent query routing via Planner.
- `POST /api/v1/ai/analyze`: Complete codebase audit.
- `POST /api/v1/ai/search`: Semantic search queries.
- `POST /api/v1/ai/architecture`: Graph import audits.
- `POST /api/v1/ai/documentation`: README and comments review.
- `POST /api/v1/ai/security`: Vulnerability scans.
- `POST /api/v1/ai/quality`: AST complexity stats checks.
