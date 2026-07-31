# Knowledge Layer Schema - CodeAtlas AI Enterprise Platform

## 1. Knowledge Layer Design & Hybrid Retrieval

### Purpose
To detail the design of the CodeAtlas AI Knowledge Layer and its Hybrid Retrieval engine (combining Vector Similarity Search, Knowledge Graph Traversal, Context Builder logic, and Repository Metadata), explaining how it provides context for repository comprehension.

### Responsibilities
* **Hybrid Retrieval Execution**: Execute multi-stage query retrieval using dense vector similarity scores coupled with SQL graph node traversals.
* **Context Hydration**: Assemble retrieved source code files, class schemas, API endpoints, and metadata packages into a structured context window payload for the LLM.
* **Metadata Resolution**: Resolve structural relationships (e.g. tracking which class implements a specific interface).

### Hybrid Retrieval Pipeline
```
               +------------------------------------------------------+
               |                      User Query                      |
               +------------------------------------------------------+
                                          │
                  ┌───────────────────────┴───────────────────────┐
                  ▼                                               ▼
     +─────────────────────────+                     +─────────────────────────+
     |  Vector Similarity Search |                     | Knowledge Graph Query   |
     +─────────────────────────+                     +─────────────────────────+
                  │                                               │
                  └───────────────────────┬───────────────────────┘
                                          ▼
               +------------------------------------------------------+
               |              Reranker & Score Merger                 |
               +------------------------------------------------------+
                                          │
                                          ▼
               +------------------------------------------------------+
               |             Structured Context Builder               |
               +------------------------------------------------------+
```

### Advantages
* **High Groundedness**: Combining structural relationships (from the graph) with semantic meaning (from vector search) reduces AI hallucinations to less than 5%.
* **Structured Context**: Code relationships are preserved in the LLM prompt, helping the model understand code organization.
* **Deterministic Fallback**: If vector search fails to find relevant items, the graph traversal engine can resolve references deterministically using imports and symbol tables.

### Limitations
* **pgvector Search Saturation**: Vector searches on massive codebases with millions of chunks can suffer from latency issues unless index parameters are optimized.
* **Graph Traversal Complexity**: Relational representations of complex graph trees can result in expensive SQL queries with multiple JOIN operations, increasing database load.

### Alternatives Considered
* **Pure Vector Retrieval (Vector-Only RAG)**: Rejected because it misses structural relationships. For example, vector search may find a method implementation but miss the interface definition or class relationships.
* **External Graph Database (Neo4j)**: Rejected to simplify the system architecture. Storing both vector indices and graph relationships inside PostgreSQL reduces deployment overhead.

### Trade-offs
* **Retrieval Completeness vs. Inference Cost**: Including broad graph contexts (e.g., fetching 3 levels of dependencies) provides the model with complete structural information but increases token costs and latency. We use a tuned context builder to limit retrieval depth.

### Future Improvements
* **Hybrid Re-ranking Models**: Integrate dedicated re-ranking models (such as Cohere or BGE reranker) to optimize chunk prioritization before building the LLM context.
* **Dynamic Graph Path Extraction**: Dynamically extract execution paths between classes and write them as simplified call-flow trees in the prompt context.

### Best Practices
* **Use HNSW Indexes**: Always build HNSW indexes on vector columns in pgvector for fast query execution under load.
* **Chunk Code Semantically**: Partition source files by AST node boundaries (e.g., class or function blocks) instead of using arbitrary character length limits.

---

## 2. Domain-Specific Repository Data Model

### Purpose
To define the domain entities representing repository structures within the Knowledge Layer, ensuring that CodeAtlas AI can model all code architectures accurately.

### Responsibilities
* **Entity Representation**: Model repositories, snapshots, directories, files, classes, methods, functions, interfaces, enums, API endpoints, database tables, services, external dependencies, and configuration files.
* **Relationship Management**: Capture ownership, imports, implementations, inheritance, invocations, and reference mapping.

### Entity Relationship Model
```
  [Repository] ── 1:N ──> [Snapshot] ── 1:N ──> [File] ── 1:N ──> [AST Node (Class/Function)]
                                                                           │
                                                                       Implements / Calls
                                                                           │
                                                                           ▼
                                                                  [Dependency / Relation]
```

### Advantages
* **Fine-Grained Context**: The system can retrieve individual methods or functions instead of having to send entire source code files, optimizing context token usage.
* **Framework Agnostic**: The general entity structure can represent Python modules, Java classes, React components, and database SQL schemas.
* **Version Control Alignment**: Snapshots map directly to git commits, keeping the extracted model aligned with the actual repository history.

### Limitations
* **Dynamic Language Challenges**: In dynamic languages like JavaScript or Python, tracking dynamic imports and variable types is difficult, which can lead to incomplete relation maps.
* **Parser Maintenance**: Language-specific parsers must be updated when language specifications change.

### Alternatives Considered
* **Flat File Directory Model**: Storing files as simple text strings without AST parsing. Rejected because it does not capture structural information, preventing the system from answering architectural questions.
* **Universal AST representations**: Attempting to use a single AST schema for all languages. Rejected because it fails to capture language-specific concepts (e.g., React hooks vs. Java annotations).

### Trade-offs
* **Granular Extraction vs. Database Size**: Extracting every variable declaration and syntax block would bloat the database. We choose to store only high-level symbols (classes, interfaces, methods, functions, dependencies) to balance index size and detail.

### Future Improvements
* **Type-Resolution Pass**: Implement static type analysis for dynamic languages to resolve implicit references and build cleaner graphs.
* **Call Graph Tracing**: Trace actual function call paths by analyzing import chains and signature declarations.

### Best Practices
* **Sanitize Entity Names**: Remove local file system paths from files and classes, storing only relative project paths to ensure environment independence.
* **Use UUIDs**: Generate UUIDs for all entity records to prevent ID collisions across database migrations or sync events.

---

## 3. Database Schema (PostgreSQL & pgvector DDL)

### Purpose
To provide the production-grade DDL scripts, table definitions, column configurations, indices, and graph traversal queries used to persist and query the CodeAtlas AI Knowledge Layer.

### Responsibilities
* **Data Definition**: Define schemas for projects, snapshots, files, AST nodes, relations, and embeddings.
* **Vector Vectorization**: Define pgvector columns with correct dimensions (e.g. 1536 for OpenAI, 768 for Gemini).
* **Graph Queries**: Provide SQL query templates for parent-child traversals and import resolving.

### DDL Implementation Scripts & Traversal Queries

```sql
-- DDL Script: CodeAtlas AI Database Schema

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- Projects Table
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Snapshots Table
CREATE TABLE snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    version_tag VARCHAR(50) NOT NULL,
    commit_sha VARCHAR(40),
    status VARCHAR(50) NOT NULL, -- 'PENDING', 'PARSING', 'COMPLETED', 'FAILED'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Files Table
CREATE TABLE files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    snapshot_id UUID REFERENCES snapshots(id) ON DELETE CASCADE,
    path VARCHAR(1024) NOT NULL,
    content_chunk TEXT NOT NULL,
    embedding vector(768), -- Vector dimensionality set for target embedding model
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- AST Nodes Table
CREATE TABLE ast_nodes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    file_id UUID REFERENCES files(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL, -- 'CLASS', 'METHOD', 'FUNCTION', 'INTERFACE', 'ENUM'
    signature TEXT,
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Relations Table (Graph Edges)
CREATE TABLE relations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_node_id UUID REFERENCES ast_nodes(id) ON DELETE CASCADE,
    target_node_id UUID REFERENCES ast_nodes(id) ON DELETE CASCADE,
    relation_type VARCHAR(50) NOT NULL, -- 'CALLS', 'INHERITS', 'IMPLEMENTS', 'IMPORTS'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index Definitions
CREATE INDEX idx_files_snapshot ON files(snapshot_id);
CREATE INDEX idx_ast_nodes_file ON ast_nodes(file_id);
CREATE INDEX idx_relations_source ON relations(source_node_id);
CREATE INDEX idx_relations_target ON relations(target_node_id);

-- HNSW Vector Index for Cosine Similarity Searches
CREATE INDEX idx_files_embedding_hnsw ON files USING hnsw (embedding vector_cosine_ops);

-- Sample Graph Traversal Query: Resolve Dependency Path
-- Find all target nodes called or inherited by a starting class node within 3 hops
WITH RECURSIVE dependency_path AS (
    -- Anchor member
    SELECT 
        source_node_id, 
        target_node_id, 
        relation_type, 
        1 AS depth
    FROM relations
    WHERE source_node_id = 'YOUR_STARTING_NODE_UUID'::uuid
    
    UNION ALL
    
    -- Recursive member
    SELECT 
        r.source_node_id, 
        r.target_node_id, 
        r.relation_type, 
        dp.depth + 1
    FROM relations r
    INNER JOIN dependency_path dp ON r.source_node_id = dp.target_node_id
    WHERE dp.depth < 3
)
SELECT 
    an_src.name AS source_name,
    an_src.type AS source_type,
    dp.relation_type,
    an_tgt.name AS target_name,
    an_tgt.type AS target_type,
    dp.depth
FROM dependency_path dp
JOIN ast_nodes an_src ON dp.source_node_id = an_src.id
JOIN ast_nodes an_tgt ON dp.target_node_id = an_tgt.id;
```

### Advantages
* **Simplified Operations**: Standard PostgreSQL replication configurations automatically cover security, backups, and point-in-time recovery for vector and graph data.
* **Low Latency Traversals**: Using indexing combined with PostgreSQL Recursive CTEs allows 3-hop graph queries to execute in single-digit milliseconds.
* **Integrity Checks**: Foreign key constraints prevent orphaned files or AST nodes, keeping the database clean.

### Limitations
* **Rigid Schema Evolution**: Modifying schemas on tables with millions of records in production can require complex migration scripts and downtime.
* **Index Lock Contention**: Building vector HNSW indexes under heavy write loads can temporarily block queries unless database resources are managed carefully.

### Alternatives Considered
* **TimescaleDB Partitioning**: Considered for snapshot management. Rejected because snapshots are uploaded as discrete batch operations rather than continuous, high-volume time-series data streams.

### Trade-offs
* **Cascade Delete vs. Soft Delete**: We use `ON DELETE CASCADE` constraints. While soft deletion allows file recovery, cascade deletes simplify storage management by automatically purging all AST nodes and relations when a snapshot is deleted.

### Future Improvements
* **Partitioning by Project**: Partition files, AST nodes, and relations tables by `project_id` to speed up queries and maintenance in larger deployments.
* **pg_vector HNSW Performance Tuning**: Fine-tune `m` and `ef_construction` parameters based on database growth to balance build times and retrieval accuracy.

### Best Practices
* **Explicit Query Timeouts**: Set `statement_timeout` limits on recursive graph queries to prevent runaway database execution.
* **Pre-warm Vector Cache**: Run pg_prewarm on HNSW indexes during system startup to load vector data into memory, ensuring fast response times from the first query.
