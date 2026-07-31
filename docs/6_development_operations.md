# Development & Operations - CodeAtlas AI Enterprise Platform

## 1. Folder Structure (Clean Architecture Layout)

### Purpose
To detail the workspace layout and structural organization of the frontend, backend, and documentation folders, ensuring adherence to Clean Architecture and SOLID design principles.

### Responsibilities
* **Maintain Code Isolation**: Separate core domain rules, use cases, adapter layers, and external frameworks.
* **Guide Development**: Provide developers with a clear structure for where to place new components, endpoints, database models, or services.

### Project Workspace Tree
```
CodeAtlas AI
│
├── docs/                      # Architectural & design documentation files
│
├── frontend/                  # React web portal
│   ├── public/
│   └── src/
│       ├── components/        # Reusable UI elements (chat, dashboard, uploads)
│   	├── hooks/             # Custom React hooks (WS streams, API query fetches)
│   	├── context/           # Session, Project, Auth states
│       └── App.jsx
│
├── backend/                   # FastAPI gateway backend
│   ├── app/
│   │   ├── domain/            # Entities, abstract base interfaces, system schemas
│   │   ├── usecases/          # Business workflows (Ingest, RunChat, GenerateADR)
│   │   ├── adapters/          # DB controllers, Vector engines, API wrappers
│   │   └── api/               # Router endpoints, middleware, schemas
│   ├── tests/
│   ├── main.py
│   └── requirements.txt
│
├── README.md
├── LICENSE
└── .env.example
```

### Advantages
* **Strict Separation of Concerns**: Core business logic in `domain/` and `usecases/` remains completely decoupled from external databases and HTTP libraries.
* **Easy Testing**: Adapters can be mocked out, allowing core workflows to be unit-tested without requiring database connections or HTTP servers.
* **Clean Code Navigation**: Developers can locate files quickly based on layer responsibilities.

### Limitations
* **Boilerplate Overhead**: Clean Architecture requires defining interfaces, data transfer objects (DTOs), and model mappers, increasing file counts and initial setup times.
* **Indirection Complexity**: Resolving call paths across multiple layers can be harder to follow for engineers unfamiliar with Clean Architecture patterns.

### Alternatives Considered
* **Flat MVC Layout**: Grouping everything into standard `models/`, `views/`, and `controllers/` folders. Rejected because MVC does not provide sufficient separation for complex agentic tools and workflow layers, leading to bloated files.
* **Feature-Based Folder Layout**: Grouping all layers under feature folders (e.g. `chat/`, `ingestion/`). Rejected because cross-cutting concerns (like pgvector queries or metadata lookups) become difficult to share cleanly.

### Trade-offs
* **Structure vs. Simplicity**: We chose Clean Architecture over a simpler layout. This increases initial setup effort but is necessary to maintain clean code and prevent logical entanglement as the platform grows.

### Future Improvements
* **Monorepo Tooling**: Adopt monorepo management tools (like Nx or Turborepo) to manage frontend and backend dependency chains more efficiently.
* **Isolated Packages**: Package domain use cases as independent libraries that can be shared across multiple backend microservices.

### Best Practices
* **Zero External Dependencies in Domain**: Ensure the `domain/` directory contains only pure Python objects without references to external frameworks or databases (like SQLAlchemy or FastAPI).
* **Depend on Abstractions**: Lower-level modules (like database adapters) must depend on abstract interfaces defined in the domain layer, not the other way around.

---

## 2. Ingestion Plugin Architecture

### Purpose
To design a dynamic, extensible ingestion plugin system that allows CodeAtlas AI to support new programming languages and frameworks without modifying the core parsing pipelines.

### Responsibilities
* **Language Detection**: Identify file types and route them to correct parsing plugins.
* **AST Node Extraction**: Parse source code into abstract syntax trees (ASTs) using Tree-sitter configurations.
* **Relationship Mapping**: Resolve imports, class inheritances, interface implementations, and method calls.

### Ingestion Plugin Flow
```
[Repository Archive] ──► Ingestion Router ──► [Language Detector]
                                                     │
                                   ┌─────────────────┼─────────────────┐
                                   ▼ (Python)        ▼ (Java)          ▼ (React/JS)
                            [Python Plugin]   [Java Plugin]    [Javascript Plugin]
                                   │                 │                 │
                                   └─────────────────┼─────────────────┘
                                                     ▼
                                            [AST Entity Mapper]
                                                     │
                                                     ▼
                                            [PostgreSQL Database]
```

### Advantages
* **Extensible Design**: Developers can support a new language (e.g., Go or Rust) by writing a new plugin subclass without changing the main ingestion controller.
* **Dynamic Loading**: Plugins are loaded dynamically at runtime, keeping the core platform footprint small.
* **Language-Specific Customization**: Plugins can implement custom logic for specific languages (e.g., parsing decorator mappings in Python or annotations in Java).

### Limitations
* **Tree-sitter Dependency**: The plugin system requires native binary dependencies for Tree-sitter grammars, which must be compiled for the target OS during deployment.
* **Performance Variances**: Complex files can cause deep parsing loops, requiring timeouts to prevent pipeline hangs.

### Alternatives Considered
* **Single Monolithic Parser**: Writing a unified regex-based parser. Rejected because regular expressions cannot accurately capture complex, nested structures like inheritance or call graphs.
* **External Language Servers**: Running language-specific LSP instances. Rejected due to the extreme memory and runtime overhead of hosting dozens of running servers.

### Trade-offs
* **AST Accuracy vs. Indexing Speed**: Tree-sitter provides deep syntax trees, which are highly accurate but slower to parse than simple keyword tokenizers. We accept this speed trade-off to ensure high-quality retrieval.

### Future Improvements
* **Wasm-Based Parsers**: Compile Tree-sitter parsers to WebAssembly (Wasm) to standardise runtime dependencies and speed up parser executions.
* **Framework-Specific Analysis**: Add plugins to extract framework-specific relationships (such as routing maps in FastAPI or component dependency trees in React).

### Best Practices
* **Abstract the Base Plugin Class**: Define a clear abstract base class `BaseIngestPlugin` requiring implementation of `detect_language`, `parse_file`, and `extract_relations`.
* **Add Parse Timeouts**: Limit file parsing times to prevent corrupt or abnormally large files from blocking worker queues.

---

## 3. Development Roadmap & Sprint Planning

### Purpose
To map out the execution phases, milestones, development schedules, and sprint tasks needed to build and release the CodeAtlas AI platform.

### Responsibilities
* **Milestone Planning**: Define clear milestones aligned with project versions.
* **Sprint Breakdown**: Translate development phases into discrete tasks for sprint execution.

### Milestone Tracking (Phases 1-6)
* **Milestone 1 (v0.1.0-alpha - Architecture & Setup)**: Complete project structures, database migrations, docker environments, and auth APIs.
* **Milestone 2 (v0.2.0-alpha - Ingestion & Parsing)**: Implement ingestion routines, Tree-sitter parsers, AST mapping, and dependency builders.
* **Milestone 3 (v0.3.0-alpha - Knowledge Layer & Search)**: Integrate pgvector indexing, HNSW searches, hybrid query routing, and context builders.
* **Milestone 4 (v0.4.0-beta - AI Reasoning Platform)**: Implement AI Gateway, LangGraph Planner, MCP registries, and streaming chat systems.
* **Milestone 5 (v0.5.0-beta - Engineering Copilot & ML)**: Build ADR, test plan, onboarding generators, and machine learning prediction workers.
* **Milestone 6 (v1.0.0 - Production Readiness)**: Add evaluation frameworks, logging, dashboards, security audits, and production charts.

### Advantages
* **Clear Delivery Path**: Gives stakeholders and developers a clear view of progress and timelines.
* **Manageable Iterations**: Breaking tasks into sprints helps team members focus on immediate objectives.
* **Alignment with Metrics**: Each milestone includes verification steps to ensure quality standards are met before moving forward.

### Limitations
* **Schedule Fluctuations**: Complex integrations (like multi-agent reasoning loops) can cause scheduling delays that require sprint scope adjustments.
* **Resource Constraints**: Roadmaps assume consistent team capacity, which can change in real-world scenarios.

### Alternatives Considered
* **Ad-Hoc Agile Board**: Working off a single backlog backlog without structured phases. Rejected because building complex architectures requires sequence coordination (e.g. database schema setup must precede ingestion pipelines).

### Trade-offs
* **Strict Phases vs. Parallel Tasks**: We choose structured dependencies. This means developers cannot work on AI chat systems until the ingestion and database schemas are stable, which reduces concurrency but prevents duplicate work and alignment errors.

### Future Improvements
* **Automated Release Notes**: Automatically generate changelog records from Git commit histories during releases.
* **Continuous Integration Evaluation**: Run accuracy checks automatically in CI/CD pipelines before tagging releases.

### Best Practices
* **Keep Sprints Under Two Weeks**: Maintain regular, short feedback loops to catch architectural regressions early.
* **Establish Clear Definitions of Done (DoD)**: Require all tasks to have unit test coverage and updated documentation before being marked complete.

---

## 4. Risk & Security Strategy

### Purpose
To detail the security controls, risk mitigations, authentication flows, and data protections required to safeguard enterprise codebase intellectual property.

### Responsibilities
* **Credential Protection**: Prevent hardcoded passwords, tokens, and API credentials from being stored in databases or sent to LLMs.
* **Data Isolation**: Enforce workspace-level role permissions to ensure users only access repositories they have permission to view.
* **Threat Mitigation**: Protect the system against prompt injections, resource-exhaustion attacks, and server-side request forgery (SSRF).

### Advantages
* **Reduced Vulnerability Window**: Automated scanners catch sensitive data (like leaked passwords) in uploaded repositories before they can be stored in the index.
* **Secure Enterprise Auditing**: Logging all tool executions and data queries provides a clear audit trail for security compliance audits.
* **Isolated Processing**: Running code parsing inside non-root containers prevents unauthorized file system access on host servers.

### Limitations
* **Complexity of Secret Detection**: Identifying custom security tokens or credentials accurately can trigger occasional false positives, requiring manual review configurations.
* **Security Overhead**: Checking inputs through safety guardrails adds processing latency, which must be optimized to maintain good user experience.

### Alternatives Considered
* **Relying on Client Sanitization**: Expecting users to clean codebases before uploading them. Rejected due to the high risk of human error leading to leaked API keys or passwords.
* **Open System Layout**: Leaving tools open to run any system command. Rejected because it exposes the backend servers to complete compromise via prompt injection attacks.

### Trade-offs
* **Strict Isolation vs. Quick Setup**: We isolate code parsers from the main gateway. This requires more complex network configurations but is necessary to prevent security breaches if a parser is compromised.

### Future Improvements
* **Micro-virtualized Sandboxes**: Run all code execution tools inside micro-VMs (such as Firecracker) to isolate processes at the kernel level.
* **Zero-Knowledge Encryption**: Implement database column-level encryption so repository data is encrypted in transit and at rest, readable only by authorized users.

### Best Practices
* **Use Standard Secret Scanners**: Integrate open-source secret scanners (like Gitleaks or TruffleHog) directly into the file upload pipeline.
* **Enforce Principle of Least Privilege**: Ensure agent database users have only read and write permissions for target schemas, restricting access to administrative functions.

---

## 5. Version Management Strategy

### Purpose
To outline how CodeAtlas AI versions prompts, vector embeddings, database graphs, documentation, and reports to prevent system drift and ensure consistent responses.

### Responsibilities
* **Prompt Version Tracking**: Manage prompt template updates in the database with version numbers and migration rollback scripts.
* **Embedding Model Locking**: Lock snapshots to specific embedding model versions to prevent vector dimension mismatches.
* **Data Model Schema Upgrades**: Coordinate schema updates for metadata tables without losing existing repository indices.

### Version Mapping Matrix
```
+---------------------------------------------------------------------------------+
|                              VERSION MANAGEMENT                                 |
|                                                                                 |
|  +------------------------+  +------------------------+  +-------------------+  |
|  |     Prompt Version     |  |    Embedding Model     |  |  Schema Version   |  |
|  |     (v1.2 - Ingestion) |  |   (Gemini-Embed-v1.5)  |  |  (v0.3.0 - DDL)   |  |
|  +------------------------+  +------------------------+  +-------------------+  |
+---------------------------------------------------------------------------------+
```

### Advantages
* **Consistent Responses**: Version control prevents system updates from changing prompt layouts unexpectedly, reducing regression risk.
* **Prevents Index Corruption**: Locking embedding models ensures that queries are compared against compatible vector spaces, avoiding search errors.
* **Replayable Configurations**: Keeping version histories of prompts allows developers to test performance against previous baselines.

### Limitations
* **Dual Indexing Costs**: If an embedding model is upgraded, all existing repository files must be re-indexed using the new model, consuming CPU and memory.
* **Database Migration Overhead**: Upgrading schema structures on large production databases requires careful, step-by-step migration scripts to prevent locks and outages.

### Alternatives Considered
* **Auto-Updating Embedding APIs**: Using dynamic, auto-updating embedding endpoints. Rejected because changing model versions silently breaks existing vector indexes, corrupting search results.
* **Single Unversioned Config File**: Storing prompt templates in a single configuration file. Rejected because tracking changes, rolling back edits, and testing updates becomes error-prone.

### Trade-offs
* **Re-indexing Costs vs. Search Quality**: Upgrading embedding models requires reprocessing old snapshots. We accept this cost because upgrading models is necessary to take advantage of search quality improvements over time.

### Future Improvements
* **Dynamic Index Re-vectorizers**: Build background workers that automatically re-index databases in the background when a new embedding model is configured.
* **Automated Migration Validations**: Run schema check pipelines to verify database compatibility before executing migrations in production.

### Best Practices
* **Lock Third-Party Model APIs**: Use specific model versions (e.g. `gemini-1.5-pro-001`) in API calls rather than dynamic aliases (e.g. `gemini-1.5-pro-latest`).
* **Define Migration Rollbacks**: Every schema update script must have a corresponding fallback rollback script to allow quick recovery if a migration fails.
