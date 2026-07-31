# System Architecture - CodeAtlas AI Enterprise Platform

## 1. High-Level & Low-Level Architecture

### Purpose
To define the structural organization of CodeAtlas AI, explaining how the client front-end communicates with the API gateway, and how the gateway coordinates activities across the static analysis, AI reasoning, and predictive machine learning modules.

### Responsibilities
* **Structural Division**: Map out front-end interface web portals, reverse proxies, REST APIs, message brokers, caching nodes, background task engines, and storage systems.
* **Component Boundaries**: Ensure that processing pipelines remain isolated, and that direct dependencies between the AI generation and ML prediction layers are strictly forbidden.

### Architecture Topology
```
           +-----------------------------------------------------------------+
           |                           User Client                           |
           +-----------------------------------------------------------------+
                                            │ (HTTPS)
                                            ▼
           +-----------------------------------------------------------------+
           |                        FastAPI Web Gateway                      |
           +-----------------------------------------------------------------+
                                            │
       ┌────────────────────────────────────┼───────────────────────────────────┐
       │ (Asynchronous Tasks)               │ (Synchronous Read/Write)          │ (Model Gateway API)
       ▼                                    ▼                                   ▼
+───────────────+                    +───────────────+                   +───────────────+
| Celery Tasks  |                    |  PostgreSQL   |                   |  AI Gateway   |
| (Redis Queue) |                    |  + pgvector   |                   |   & Router    |
+───────────────+                    +───────────────+                   +───────────────+
```

### Advantages
* **Loose Coupling**: Components communicate through standard protocols (gRPC/REST/AMQP), making individual services replaceable.
* **Resilient Scaling**: Large static code analysis processes do not impact conversational response times because task processing is offloaded to worker pools.
* **Data Flow Clarity**: Data moves from ingestion to parsing, indexing, and retrieval in a strict linear pipeline.

### Limitations
* **Network Overhead**: Multiple micro-services increase network hop latencies compared to a single monolith.
* **Operational Overhead**: Managing separate database backends, caching services, and brokers increases DevOps complexity.

### Alternatives Considered
* **Monolithic Django Architecture**: Rejected. While Django is mature, its synchronous ORM design is ill-suited for handling high-concurrency event streams, websocket-based streaming tokens, and async workers simultaneously.
* **Direct Serverless Model Executions**: Executing Tree-sitter parsers inside AWS Lambda. Rejected due to cold-start delays, file size restrictions, and latency requirements.

### Trade-offs
* **Relational Graph Storage vs. Pure Graph Database**: Relational schema layouts in PostgreSQL (using tables for nodes/edges) were selected over a dedicated Neo4j instance. This limits graph-traversal speed for deeply recursive queries (>5 hops) but simplifies transactional safety and reduces infrastructure sprawl.
* **Async Ingestion vs. Immediate Feedback**: Users upload repository snapshots and must wait for indexing to finish. This adds minor latency to the user experience but prevents server resource depletion.

### Future Improvements
* **Transition to Temporal Orchestration**: Swap Celery for Temporal to get robust workflow state tracking, retry loops, and visual execution trees.
* **Shared Memory Inter-Process Ingestion**: Utilize Apache Arrow or shared RAM structures for high-volume AST token streaming between the parsing and embedding steps.

### Best Practices
* **Enforce Database Connection Pooling**: Use Pgbouncer to manage connections from highly concurrent worker clusters.
* **Timeout Policies**: Every external model HTTP request must have a strict connect and read timeout configuration (typically 3s connect, 15s read).

---

## 2. Microservice Architecture

### Purpose
To detail the individual services that compose the CodeAtlas AI platform, defining their responsibilities, operational boundaries, interfaces, and communication models.

### Responsibilities
* **Ingestion/Indexing Service**: Receives repository archives, verifies integrity, extracts directories, and initiates ingestion pipelines.
* **Parsing Service (AST-Extractor)**: Employs Tree-sitter plugins to parse raw source code files into Abstract Syntax Trees, capturing metadata, inheritance, and imports.
* **Analysis Service (Static & ML)**: Executes deterministic code complexity, linting, maintainability predictions, and security scans.
* **Agent Orchestration Service**: Hosts the LangGraph planner agent, guardrail evaluations, and tool invocation registries.
* **Web API Gateway**: Handles client routing, WebSocket connections for streaming responses, session management, and rate limiting.

### Advantages
* **Independent Scalability**: Ingestion and AST parsers, which are CPU-bound, can be scaled separately from the IO-bound API gateway.
* **Fault Isolation**: A crash in the static analysis engine does not crash the conversational chat or the main API service.
* **Technological Autonomy**: Individual microservices can use specific runtimes (e.g., Python for AI/ML components and Node.js or Go for high-throughput AST extraction).

### Limitations
* **Data Consistency Risks**: Distributed transactions are complex to coordinate.
* **Distributed Debugging Difficulty**: Tracing user requests across multiple service boundaries requires centralized logging systems.

### Alternatives Considered
* **Single Process System**: Packaging all engines into a single container. Rejected due to the risk of resource starvation (e.g., a heavy ML prediction process consuming all CPU, starving API requests).

### Trade-offs
* **Internal APIs REST vs. gRPC**: We chose standard HTTP/JSON REST internal interfaces over gRPC for Version 1. This increases payload sizes and serialization overhead but simplifies integration, development, and testing.

### Future Improvements
* **gRPC Upgrade**: Migrate inner-service communications to gRPC with HTTP/2 multiplexing for higher efficiency.
* **Service Mesh Integration**: Adopt Linkerd or Istio for mTLS security, automated retries, and request tracing.

### Best Practices
* **Health Checks**: Every microservice must expose a `/health` endpoint checking database, cache, and broker connections.
* **Idempotent API Handlers**: Ensure indexing requests are idempotent; submitting the same snapshot twice should safely return the existing snapshot record.

---

## 3. Workflow Orchestration Design (Celery-to-Temporal Abstraction)

### Purpose
To design an abstract interface layer (`WorkflowEngine`) that decouples the application from Celery and Redis APIs, allowing a future migration to Temporal without requiring changes to the core business logic.

### Responsibilities
* **Engine Decoupling**: Wrap task declaration, status tracking, queue routing, and payload serialization into a generic adapter pattern.
* **Worker Execution**: Coordinate asynchronous parsing, metadata extraction, embedding generation, and indexing tasks.

### Workflow Abstraction Schema
```
                        +----------------------------+
                        |   WorkflowEngine (Interface)|
                        +----------------------------+
                                      ▲
                                      │ Implements
                       ┌──────────────┴──────────────┐
                       │                             │
        +────────────────────────────+ +────────────────────────────+
        |   CeleryWorkflowEngine     | |   TemporalWorkflowEngine   |
        |   (Version 1 Adapter)      | |   (Future Adapter)         |
        +────────────────────────────+ +────────────────────────────+
```

### Advantages
* **Zero Vendor Lock-in**: CodeAtlas remains decoupled from Celery APIs, allowing the platform to run on simple Redis message queues in V1 and migrate to robust orchestrators later.
* **Simplified Testing**: Developers can mock out the `WorkflowEngine` interface during testing to run tasks synchronously, removing the need for a live Celery broker during unit tests.

### Limitations
* **Feature Minimization**: The abstraction must target the lowest common denominator between Celery and Temporal. High-end, Celery-specific optimizations or Temporal-specific state queries cannot be exposed directly.
* **Interface Overhead**: Adds a layer of indirection that developers must learn.

### Alternatives Considered
* **Direct Celery SDK Integration**: Importing `@app.task` across the entire ingestion codebase. Rejected because it tightly couples the business logic to Celery, making future orchestration changes costly.
* **Immediate Asyncio Tasks**: Using Python's `asyncio.create_task` inside the API process. Rejected due to lack of persistence, monitoring, and horizontal worker scaling.

### Trade-offs
* **Infrastructure Overhead**: Celery + Redis requires maintaining two additional servers in V1. However, this is significantly simpler to host and configure locally than a full Temporal cluster.

### Future Improvements
* **Temporal Migration Implementation**: Build the Temporal adapter using the official `temporalio` Python SDK, mapping Celery tasks to Temporal Workflows and Activities.
* **Dynamic Step Retries**: Implement exponential backoff retry algorithms directly in the workflow engines, handled dynamically based on failure types.

### Best Practices
* **Pass Primitive Parameters**: Avoid passing heavy database model objects through the workflow engine. Pass simple IDs and let the worker fetch the data within its transactional scope.
* **Trace Task Context**: Ensure that correlation IDs (span IDs) are serialized and passed across task boundaries to maintain trace continuity.

---

## 4. Scalability Strategy

### Purpose
To establish the scaling protocols, indexing strategies, and hardware optimization paths required to handle high concurrency and large data volumes.

### Responsibilities
* **Database Scaling**: Define horizontal read replicas, connection pooling, and table partitioning.
* **Vector Index Optimization**: Optimize pgvector configurations to keep nearest-neighbor retrieval speeds sub-50ms under heavy load.
* **Worker Scaling**: Design auto-scaling rules for the ingestion and parsing workers.

### Advantages
* **Predictable Growth**: Clear scaling vectors permit capacity planning.
* **Cost-Efficient Resource Allocation**: Elastic scale targets compute resources to where they are needed most during high ingestion loads.

### Limitations
* **Database Write Bottleneck**: PostgreSQL primary write performance is bounded by disk speed and locking mechanisms, restricting absolute write scaling.
* **Vector Query Latency**: As vector databases grow, search speeds degrade unless index construction parameters (like HNSW options) are tuned periodically.

### Alternatives Considered
* **Separate Vector Database (e.g. Pinecone/Milvus)**: Rejected. While they scale vector queries exceptionally well, they introduce data synchronization issues and break transaction boundaries with the repository metadata.
* **NoSQL Metadata Store**: Storing metadata in MongoDB. Rejected due to lack of robust foreign key constraint enforcement and complex relational joins.

### Trade-offs
* **pgvector HNSW vs. IVFFlat Indexes**: HNSW (Hierarchical Navigable Small World) was chosen over IVFFlat. HNSW has longer build times and higher memory overhead, but it offers superior query latency and retrieval accuracy.
* **Horizontal Replication vs. Vertical Sharding**: We choose horizontal read-scaling with primary-replica nodes rather than sharding databases by repository. Sharding introduces complex query patterns and increases cross-tenant management complexity.

### Future Improvements
* **Time-Series Partitioning**: Partitioning snapshot and analysis tables by creation date to speed up database housekeeping operations.
* **GPU-Accelerated Embedding Extraction**: Moving local embedding models (e.g., HuggingFace transformers) to GPU instances to accelerate vector generation.

### Best Practices
* **Limit Vector Dimensionality**: Use dense, high-performance embedding models (e.g., 768 or 1536 dimensions) to balance representation accuracy and vector query speed.
* **Auto-Scale Workers by Queue Metrics**: Set auto-scaling rules based on message queue length and queue age, rather than CPU utilization alone.

---

## 5. Deployment Strategy

### Purpose
To outline the environments, container configurations, and orchestration structures required to safely deploy CodeAtlas AI in both development and production.

### Responsibilities
* **Environment Provisioning**: Provide standard Docker Compose structures for local testing.
* **Production Orchestration**: Define Kubernetes manifests, routing tables, configurations, and secrets management structures.

### Advantages
* **Reproducible Environments**: Docker guarantees that developers run the exact same runtime versions as the production cloud.
* **Automated Self-Healing**: Kubernetes handles liveness/readiness checks, automatically restarting failed instances and distributing traffic.

### Limitations
* **Kubernetes Complexity**: Setting up a production-grade Kubernetes cluster requires specialized platform engineering skills.
* **State Management**: Databases, cache nodes, and brokers require persistent volume configurations, which must be managed carefully to prevent data loss during restarts.

### Alternatives Considered
* **Bare-Metal Manual Install**: Writing shell scripts to install Python, Node.js, Redis, and PostgreSQL directly on target VMs. Rejected due to reproducibility and drift issues.
* **Serverless Deployment (Cloud Run/Fargate)**: Rejected due to long-running task constraints and local storage access performance requirements for indexing tasks.

### Trade-offs
* **Self-Hosted Database vs. Managed Services**: For production, managed databases (e.g. AWS RDS PostgreSQL) are preferred over running PostgreSQL inside Kubernetes. This adds cost but offloads backups, patching, and failover mechanics.

### Future Improvements
* **Helm Chart Packaging**: Package the entire system into a single Helm chart to simplify third-party deployments.
* **GitOps Continuous Deployment**: Implement ArgoCD or Flux to automatically sync the cluster configuration with git repositories.

### Best Practices
* **Do Not Store Secrets in Code**: Inject all credentials (database URLs, LLM API keys) via environment variables using Kubernetes secrets.
* **Resource Request and Limit Settings**: Always define CPU/Memory requests and limits on every container to prevent resource starvation.
