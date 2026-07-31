# CodeAtlas AI Product Roadmap

This roadmap details the timeline and development milestones for CodeAtlas AI, aligning with the versioning framework and plan.

---

## Development Milestones

### Phase 1: Foundation (v0.2.0-alpha)
* Establish basic API gateway routes and database connections.
* Implement user authentication (JWT + RBAC).
* Build workspace and repository snapshot metadata tables.

### Phase 2: Static Analysis Pipeline (v0.3.0-alpha)
* Integrate Tree-sitter parsers for Python, Java, and JavaScript/TypeScript.
* Build the ingestion router to detect repository languages.
* Write AST extraction code to identify code symbols and mappings.

### Phase 3: Knowledge Layer & Hybrid Retrieval (v0.4.0-beta)
* Setup pgvector HNSW database indexes.
* Build the Hybrid Retrieval engine to merge semantic search and SQL recursive CTE relationships.
* Design the prompt context builder.

### Phase 4: Agent Reasoning Engine (v0.5.0-beta)
* Integrate the Planner-Orchestrator, Task Router, and Guardrails logic.
* Set up the Model Context Protocol (MCP) registry for dynamic tool use.
* Implement WebSocket streaming for query responses.

### Phase 5: Engineering Copilot & Machine Learning (v0.6.0-beta)
* Build generation endpoints for ADRs, test plans, and onboarding guides.
* Implement predictive machine learning features (maintainability and bug risk models).
* Connect local model support via Ollama routing.

### Phase 6: Production Release (v1.0.0)
* Implement cost router, billing trackers, and metrics dashboards.
* Write Docker Compose setups and production Kubernetes manifests.
* Conduct security vulnerability audits.

---

## Future Release Pipeline (V2 & V3)

The following capabilities are out of scope for Version 1, but are planned for future major releases:

### Version 2.0 (Developer Integration)
* **IDE Extensions**: Native extensions for VS Code and JetBrains IDEs.
* **CI/CD Integration**: Automatic execution of quality assessments via GitHub Actions and GitLab CI.
* **Cloud Repository Sync**: Live workspace synchronization with GitHub and GitLab.
* **Automated PR Generation**: Agentic loops to submit pull requests directly to repository branches.

### Version 3.0 (Enterprise Scale)
* **Distributed Graph Database**: Migration from PostgreSQL graph tables to a distributed database layout (e.g. Neo4j).
* **Multi-Repository Analysis**: Cross-repository analysis to map dependencies across microservices.
* **Fine-Tuned Custom Models**: Local training pipelines to fine-tune small model weights on custom enterprise code bases.
* **Multi-Tenant SaaS Engine**: Dedicated SaaS deployment models.
* **Collaborative Editing Canvas**: Real-time collaborative document editing.
