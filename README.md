# CodeAtlas AI

> AI Powered Software Engineering Intelligence Platform

![Status](https://img.shields.io/badge/Status-Under%20Development-blue)
![Python](https://img.shields.io/badge/Python-3.12+-3776AB)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688)
![React](https://img.shields.io/badge/React-19-61DAFB)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Project Overview

CodeAtlas AI is an enterprise-grade AI Engineering platform designed to understand, analyze, document, and improve software repositories. By combining deterministic static code analysis, multi-agent AI reasoning, and predictive machine learning models, CodeAtlas AI maps source code structures and semantics into a high-density knowledge base, empowering developers with advanced architectural tools and automation.

---

## Core System Architecture

The platform follows a decoupled, clean architecture design pattern. Background workflows are abstracted through a generic execution gateway to keep code decoupled from messaging systems.

```
                                  +------------------+
                                  |   React Client   |
                                  +------------------+
                                           │ (HTTP/WS)
                                           ▼
                                  +------------------+
                                  | FastAPI Gateway  |
                                  +------------------+
                                           │
         ┌─────────────────────────────────┼─────────────────────────────────┐
         │ (Database Queries)              │ (Async Events)                  │ (AI Routing)
         ▼                                 ▼                                 ▼
+──────────────────+              +──────────────────+              +──────────────────+
|  PostgreSQL DB   |              |  Workflow Broker |              |    AI Gateway    |
| (pgvector HNSW)  |              |  (Redis/Celery)  |              |    & Registry    |
+──────────────────+              +──────────────────+              +──────────────────+
```

---

## Technical Stack

* **Frontend**: React 19, Vanilla CSS, Tailwind (optional), WebSockets (streaming)
* **Backend**: Python 3.12, FastAPI 0.115, SQLAlchemy, Pydantic v2
* **Storage & Indexing**: PostgreSQL 16 (using pgvector extension)
* **Workflow Engine**: Redis 7, Celery (abstracted via generic `WorkflowEngine` pattern)
* **Language Parsing**: Tree-sitter AST extraction engines
* **Agent Framework**: Custom LangGraph-inspired planning loops
* **LLM Integrations**: Google Gemini (Pro/Flash), Anthropic Claude, OpenAI, and local Ollama models

---

## Key Features

### 1. Hybrid Retrieval (Vector Search + Knowledge Graph)
Combines semantic vector searching with graph structures (classes, files, and functions) inside PostgreSQL to ground AI reasoning. Graph relations (calls, inherits, implements, imports) are traversed dynamically during retrieval to minimize hallucination rates.

### 2. Engineering Copilot
A flagship, standalone module designed to assist developers with complex architectural operations:
* **Architecture Explainer**: Explains codebase layouts and structural patterns.
* **ADR Generator**: Generates standard markdown Architecture Decision Records (ADRs).
* **Test Plan Designer**: Writes comprehensive test cases and suite layouts.
* **Developer Onboarding Guides**: Automatically creates context-aware walkthroughs for new engineers.
* **API Design & Refactoring Assistance**: Auto-generates clean API payloads and refactoring recipes.

### 3. Multi-Agent Architecture
Coordinates reasoning through specialized agents:
* **Planner-Orchestrator**: Decomposes developer queries into detailed execution plans.
* **Task Router**: dispatches execution tasks to specialized tools via the Model Context Protocol (MCP).
* **AI Guardrails Layer**: Audits prompt vulnerability and tool outputs against JSON schemas to secure the codebase context.
* **Response Synthesizer**: Merges output data streams into unified markdown formats.

### 4. Predictive Machine Learning Features
Provides predictive code analytics distinct from generative AI reasoning:
* **Maintainability Indexing**: Predicts code block maintainability scores.
* **Bug Risk Scoring**: Forecasts future bug risks based on AST complexity and inheritance depth.
* **Code Complexity Tracking**: Identifies code segments requiring refactoring before release.

---

## Installation & Setup

### Prerequisites
* Docker and Docker Compose
* Python 3.12+ (if running locally)
* Node.js 20+ (if running locally)

### Quick Start with Docker
1. Clone the repository and navigate to the project directory:
   ```bash
   git clone https://github.com/enterprise/codeatlas-ai.git
   cd codeatlas-ai
   ```
2. Copy the environment template:
   ```bash
   cp .env.example .env
   ```
3. Configure your API keys in the `.env` file.
4. Launch the application stack:
   ```bash
   docker-compose up --build
   ```
5. Access the services:
   * Web Portal: `http://localhost:3000`
   * API Documentation: `http://localhost:8000/docs`

---

## Environment Configuration

The application is configured using environment variables. Below are the primary settings required in `.env`:

```env
# System Configuration
ENVIRONMENT=development
SECRET_KEY=generate-a-secure-secret-key-for-jwt-signing

# Database Setup
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/codeatlas

# Redis Broker (Celery & Caching)
REDIS_URL=redis://localhost:6379/0

# Model Provider Keys
GEMINI_API_KEY=your_gemini_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
OLLAMA_HOST=http://localhost:11434
```

---

## API Overview

The FastAPI backend exposes the following primary endpoints:

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/projects` | Creates a new project workspace. |
| `POST` | `/api/v1/projects/{id}/snapshots` | Uploads a repository and schedules ingestion. |
| `GET` | `/api/v1/projects/{id}/status` | Returns the parsing and indexing progress. |
| `POST` | `/api/v1/chat` | Opens a repository chat query stream. |
| `POST` | `/api/v1/copilot/adr` | Generates a markdown ADR proposal. |

---

## Documentation Links

For detailed architectural specifications and design patterns, refer to the docs:

1. [Product Requirements & PRD](file:///d:/CodeAtlas%20AI/docs/1_product_requirements.md): Positioning, target scopes, and success metrics.
2. [System Architecture Blueprint](file:///d:/CodeAtlas%20AI/docs/2_system_architecture.md): Microservices, workflow decoupling, and deployment guidelines.
3. [Agent & MCP Design](file:///d:/CodeAtlas%20AI/docs/3_agent_mcp_architecture.md): Multi-agent orchestrations, memory hierarchies, and sequence flows.
4. [Knowledge Layer & PostgreSQL Schema](file:///d:/CodeAtlas%20AI/docs/4_knowledge_layer_schema.md): Hybrid retrieval queries and database DDL setups.
5. [API & Event Specs](file:///d:/CodeAtlas%20AI/docs/5_api_event_design.md): OpenAPI definitions and asynchronous ingestion event flows.
6. [Development & Operations Guide](file:///d:/CodeAtlas%20AI/docs/6_development_operations.md): Clean Architecture patterns, plugin frameworks, roadmaps, and security guidelines.

---

## Roadmap

Refer to [ROADMAP.md](file:///d:/CodeAtlas%20AI/ROADMAP.md) for milestones, upcoming versions, and the feature pipeline.

---

## Contributing

We welcome contributions! Please review [CONTRIBUTING.md](file:///d:/CodeAtlas%20AI/CONTRIBUTING.md) for code styling guides and pull request procedures.

---

## License

CodeAtlas AI is distributed under the MIT License. See [LICENSE](file:///d:/CodeAtlas%20AI/LICENSE) for details.
