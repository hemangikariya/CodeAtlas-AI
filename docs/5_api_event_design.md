# API & Event Design - CodeAtlas AI Enterprise Platform

## 1. AI Gateway, Model Registry & Cost Router

### Purpose
To detail the design of the AI Gateway, Model Registry, and Cost Router, explaining how CodeAtlas AI dynamically routes LLM requests based on cost, model capabilities, task complexity, and reliability.

### Responsibilities
* **Unified Interface**: Expose a single API client wrapper for multiple LLM providers (Google Gemini, Anthropic Claude, OpenAI, and local Ollama models).
* **Cost Routing**: Direct tasks dynamically (e.g. sending complex reasoning tasks to Gemini Pro/Claude and quick syntax checks to Gemini Flash).
* **Token & Cost Tracking**: Log token usage and calculate real-time model costs per project and user session.

### Routing Logic Flow
```
                     +----------------------------------------+
                     |              Agent Task                |
                     +----------------------------------------+
                                          │
                                          ▼
                     +----------------------------------------+
                     |       Complexity Classification        |
                     +----------------------------------------+
                                    ┬          ┬
                        ┌───────────┘          └───────────┐
            Complexity: High                    Complexity: Low
                        ▼                                  ▼
             +─────────────────────+            +─────────────────────+
             |   Gemini 1.5 Pro    |            |  Gemini 1.5 Flash   |
             |   Claude 3.5 Sonnet |            |  Ollama (Local Llama)|
             +─────────────────────+            +─────────────────────+
```

### Advantages
* **Optimized Token Costs**: Dynamic routing can reduce model API billing by up to 40% by avoiding the use of expensive models for simple tasks.
* **Failover Resilience**: If an API provider goes down, the Cost Router automatically fails over to an alternative model provider (e.g. failing over from Claude to Gemini).
* **Local Ingress Support**: Supports local models via Ollama, allowing offline development and testing.

### Limitations
* **Different Output Formats**: Different models can return variations in JSON formatting or code styles, which can cause parsers to fail.
* **Routing Overhead**: Analyzing task complexity before routing adds a minor latency delay to each query.

### Alternatives Considered
* **Single Model Locking**: Locking the entire platform to a single model provider (e.g., Anthropic Claude). Rejected because it limits cost optimizations and exposes the platform to provider-specific outages.
* **Static Config-Based Routing**: Hardcoding model assignments in config files. Rejected because it cannot adapt to runtime API failures or change dynamically based on query length.

### Trade-offs
* **Model Variety vs. Consistency**: Supporting multiple model backends requires keeping complex prompt templates and response parsers updated. We use unified output schemas to maintain consistency.

### Future Improvements
* **Automated Fine-Tuning Loops**: Collect user-approved responses to train smaller, local models, reducing reliance on commercial APIs over time.
* **Predicted Token Scaling**: Implement predictive models to estimate response tokens before sending queries, optimizing model selection.

### Best Practices
* **Enforce Strict Rate Limits**: Implement sliding-window rate limiters per model to stay within provider API limits.
* **Store Raw Telemetry**: Log exact input and output token counts, response times, and status codes for auditing.

---

## 2. Prompt Management System & Feature Flags

### Purpose
To outline the prompt versioning mechanisms and feature flag controls used to manage prompt templates and configuration updates in production without requiring code redeployments.

### Responsibilities
* **Prompt Versioning**: Persist prompt templates in the database, allowing version rollbacks and dynamic hydration of runtime variables.
* **Feature Flags**: Manage system features (such as experimental parsers or new LLM models) using runtime configurations.

### Advantages
* **No-Downtime Prompt Edits**: Product managers and prompt engineers can update template text in the database and release it immediately without waiting for a backend deployment.
* **Safe A/B Testing**: Run prompt experiments by directing a percentage of traffic to new templates to verify accuracy improvements.
* **Quick Feature Rollbacks**: Instantly disable faulty features or APIs using toggle switches in the database config.

### Limitations
* **Schema Drift**: If a prompt template is updated but requires input variables that the backend does not provide, the execution will crash.
* **Cache Management**: Database-stored prompts must be cached aggressively, requiring a cache invalidation pipeline to ensure updates take effect immediately.

### Alternatives Considered
* **Hardcoded String Templates**: Defining prompt strings directly in Python modules. Rejected because updating prompts requires complete CI/CD rebuilds and deployments.
* **Git-Based Prompt Configs**: Storing prompts in YAML files within the repo. Rejected because it still requires code commits and deployments to update templates in production.

### Trade-offs
* **Prompt Independence vs. Strict Coupling**: Storing templates in the database decouples them from code but introduces the risk of runtime errors if templates and code variables drift. We address this using strict validator schemas.

### Future Improvements
* **Visual Prompt Sandbox**: Build an admin UI dashboard where engineers can test prompt edits against golden evaluation datasets before saving changes.
* **Automated Prompt Compilers**: Integrate optimization libraries (like DSPy) to compile and refine prompts automatically based on feedback metrics.

### Best Practices
* **Verify Templates in CI/CD**: Run automated validation checks during build steps to ensure database prompt templates match backend schemas.
* **Configure Failback Defaults**: Always define fallback prompt templates in code files to ensure the system works even if the database is unavailable.

---

## 3. Evaluation Framework & Dashboard

### Purpose
To define the evaluation framework, logging layouts, and metric calculations used to track and display model performance and data quality in the dashboard.

### Responsibilities
* **Accuracy Tracking**: Calculate groundedness, hallucination rate, and retrieval precision metrics.
* **Telemetry Collection**: Capture and store tracing data for every agent step and tool invocation.
* **Metrics Dashboard**: Display token consumption, cost trends, and system accuracy metrics.

### Advantages
* **Clear Accuracy Visibility**: Gives engineering teams concrete data on system accuracy, helping identify prompt regressions.
* **Trace-Level Debugging**: Tracing individual agent steps makes it easier to find why a specific response failed.
* **Accurate Cost Allocation**: Cost dashboards help monitor budget usage across projects.

### Limitations
* **LLM-As-A-Judge Costs**: Using an LLM to evaluate production responses for accuracy and hallucination adds to API usage costs.
* **Noisy Evaluation Metrics**: Subjective checks (like code quality or relevance) can yield inconsistent scores depending on the evaluator model used.

### Alternatives Considered
* **Post-Hoc Manual Audits**: Relying entirely on manual code audits to evaluate responses. Rejected because it does not scale and cannot catch regressions before code changes go to production.

### Trade-offs
* **Real-time Assessment vs. Resource Overhead**: Evaluating every conversation step in real-time adds latency. We choose to evaluate a randomized sample of queries in production, while running full evaluations only during release checks.

### Future Improvements
* **Automated Grounding Databases**: Build automated test benches that run QA regressions on synthetic codebase datasets.
* **User Feedback Loops**: Use user ratings (thumbs up/down) to automatically prioritize failing interactions for manual review and inclusion in evaluation datasets.

### Best Practices
* **Isolate Tracing Data**: Write telemetry logs to dedicated time-series databases or logging pipelines to avoid performance impacts on the main application database.
* **Use Fixed Scoring Rubrics**: Standardize evaluation prompts for judge models, using clear guidelines and few-shot examples to maintain consistent scoring.

---

## 4. API Design (OpenAPI REST Specifications)

### Purpose
To detail the REST API endpoints, payload models, and response formats that client applications use to interact with CodeAtlas AI.

### Responsibilities
* **Project API**: Handlers to create projects, upload repositories, and monitor processing states.
* **Chat API**: Expose WebSocket endpoints for streaming responses, conversation history, and feedback.
* **Copilot API**: Endpoints to generate ADRs, onboarding guides, test plans, and refactoring recipes.

### API Endpoints Spec (OpenAPI Schema)

```yaml
openapi: 3.0.3
info:
  title: CodeAtlas AI API Gateway
  description: Enterprise REST API for software intelligence and engineering copilot systems.
  version: 1.0.0
paths:
  /api/v1/projects:
    post:
      summary: Create a new project workspace
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                name:
                  type: string
                description:
                  type: string
              required:
                - name
      responses:
        '201':
          description: Project created successfully
  /api/v1/projects/{projectId}/snapshots:
    post:
      summary: Upload repository archive and trigger ingestion snapshot
      parameters:
        - name: projectId
          in: path
          required: true
          schema:
            type: string
            format: uuid
      requestBody:
        required: true
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                file:
                  type: string
                  format: binary
                version_tag:
                  type: string
              required:
                - file
                - version_tag
      responses:
        '202':
          description: Upload accepted, snapshot indexing started
          content:
            application/json:
              schema:
                type: object
                properties:
                  snapshot_id:
                    type: string
                    format: uuid
                  status:
                    type: string
  /api/v1/chat:
    post:
      summary: Send query to Repository Chat
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                project_id:
                  type: string
                  format: uuid
                message:
                  type: string
                stream:
                  type: boolean
              required:
                - project_id
                - message
      responses:
        '200':
          description: Chat response payload (or stream connection initiation)
  /api/v1/copilot/adr:
    post:
      summary: Generate Architecture Decision Record (ADR)
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                project_id:
                  type: string
                  format: uuid
                title:
                  type: string
                context:
                  type: string
                decisions:
                  type: string
              required:
                - project_id
                - title
                - context
      responses:
        '200':
          description: Generated ADR markdown record
```

### Advantages
* **Standardized Interfaces**: Using OpenAPI allows frontend developers to automatically generate API client libraries, reducing coordination overhead.
* **Easy API Testing**: Exposing interactive Swagger UI docs simplifies testing for QA and third-party integrations.

### Limitations
* **File Upload Limitations**: Standard multipart file uploads can fail on extremely large repositories. We recommend using presigned URLs or chunked upload strategies for repositories over 500MB.
* **Connection Management**: Streaming WebSocket chats require active connection tracking on the gateway to clean up disconnected sockets.

### Alternatives Considered
* **GraphQL Interface**: Rejected. While GraphQL allows clients to request exact fields, REST is easier to scale, secure, cache, and document for enterprise use.

### Trade-offs
* **JSON Payloads vs. Protocol Buffers**: We chose JSON payloads for REST ease-of-use. This increases serialization latency compared to Protobuf, but makes development, debugging, and testing much simpler.

### Future Improvements
* **Presigned Upload Pipelines**: Implement endpoints that return S3/GCS presigned URLs, allowing clients to upload archives directly to object storage instead of routing through the API gateway.
* **Server-Sent Events (SSE)**: Migrate token streaming from WebSockets to Server-Sent Events (SSE) to simplify load balancer setups.

### Best Practices
* **Consistent Error Formats**: Ensure all error responses use a standardized JSON schema containing an error code, message, and details list.
* **Version Endpoints**: Always prefix paths with version designations (e.g. `/api/v1`) to prevent breaking changes when updates are released.

---

## 5. Event Flow

### Purpose
To design the event schema layouts and asynchronous messaging sequence that coordinate task execution from `RepositoryUploaded` to `AnalysisCompleted`.

### Responsibilities
* **Event Dispatching**: Broadcast event payloads to the message broker when state transitions occur.
* **Data Flow Coordination**: Ensure workers process tasks in the correct order: detect language, parse AST symbols, extract dependencies, generate embeddings, and build the knowledge graph.

### Ingestion Event Flow
```
[RepositoryUploaded] ──► [LanguageDetected] ──► [ASTParsed] ──► [DependenciesExtracted] ──► [EmbeddingsGenerated] ──► [AnalysisCompleted]
```

### Event Schemas

```json
{
  "event_type": "RepositoryUploaded",
  "event_id": "1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
  "timestamp": "2026-07-31T10:35:00Z",
  "payload": {
    "project_id": "8c56-3e28f04e26fc",
    "snapshot_id": "c7244b6e-2934-44af",
    "storage_path": "uploads/projects/8c56-3e28f04e26fc/c7244b6e-2934-44af.zip",
    "file_size_bytes": 1420560
  }
}
```

```json
{
  "event_type": "AnalysisCompleted",
  "event_id": "9f8e7d6c-5b4a-3f2e-1d0c-9b8a7f6e5d4c",
  "timestamp": "2026-07-31T10:38:15Z",
  "payload": {
    "project_id": "8c56-3e28f04e26fc",
    "snapshot_id": "c7244b6e-2934-44af",
    "files_indexed": 342,
    "ast_nodes_extracted": 1420,
    "relations_mapped": 2840,
    "predictions": {
      "average_maintainability_score": 82.5,
      "files_high_bug_risk_count": 4
    }
  }
}
```

### Advantages
* **Decoupled Workloads**: Event publishers do not need to know which services consume their events, making it easy to add new event handlers (e.g. adding a security scanning consumer).
* **Audit Logs**: Recording the event stream provides a clear history of how a snapshot was processed.

### Limitations
* **Out-of-Order Events**: In highly concurrent worker environments, events can sometimes arrive out of order, requiring state validation logic in consumers.
* **Message Broker Dependency**: The system's ingestion pipeline depends on the availability of the broker (Redis/Celery), requiring careful broker health monitoring.

### Alternatives Considered
* **Direct Function Calls**: Workers calling next steps via HTTP API requests. Rejected because a failure in a later step (like embedding generation) would require complex rollback logic in the calling service.

### Trade-offs
* **At-Least-Once Delivery**: We configure our worker tasks for at-least-once delivery. This means tasks must be idempotent to handle occasional message duplication.

### Future Improvements
* **Apache Kafka Migration**: Upgrade the message broker to Apache Kafka or RabbitMQ for persistent event storage and stream replay capabilities.
* **Dead Letter Queue (DLQ) Auto-Retries**: Implement intelligent retry systems that rerun failed events automatically if the failure was caused by a temporary database timeout.

### Best Practices
* **Include Tracing IDs**: Always include a correlation ID in every event header to track operations across service boundaries.
* **Keep Payloads Small**: Pass resource IDs in event payloads rather than embedding large payloads (like raw file contents).
