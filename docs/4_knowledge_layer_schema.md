# Knowledge Layer Architecture & Retrieval Schema

This document details the architecture, design patterns, schemas, and workflows implemented for the **CodeAtlas AI Knowledge Layer** (Phase 3). 

---

## 1. Knowledge Layer Architecture Overview

The retrieval pipeline coordinates multiple independent modules to transform raw repository files into structured, token-bounded contexts suitable for LLM consumption:

```
                  ┌──────────────────────────────────────────┐
                  │                User Query                │
                  └──────────────────────────────────────────┘
                                       │
                                       ▼
                  ┌──────────────────────────────────────────┐
                  │       Retrieval Cache Lookup (Hit) ──────┼─────────┐
                  └────────────────────┬─────────────────────┘         │
                                       │ (Miss)                        │
                                       ▼                               │
                  ┌──────────────────────────────────────────┐         │
                  │          Embedding Generator             │         │
                  └────────────────────┬─────────────────────┘         │
                                       │ (Vector)                      │
                                       ▼                               │
                  ┌──────────────────────────────────────────┐         │
                  │             Vector Store                 │         │
                  │       (Cosine Similarity Search)         │         │
                  └────────────────────┬─────────────────────┘         │
                                       │ (Top-K Chunks)                │
                                       ▼                               │
                  ┌──────────────────────────────────────────┐         │
                  │          Graph Expander (BFS)            │         │
                  └────────────────────┬─────────────────────┘         │
                                       │ (Expanded Nodes)              │
                                       ▼                               │
                  ┌──────────────────────────────────────────┐         │
                  │            Ranking Engine                │         │
                  │     (Graph Centrality & term boost)      │         │
                  └────────────────────┬─────────────────────┘         │
                                       │ (Ranked Chunks)               │
                                       ▼                               │
                  ┌──────────────────────────────────────────┐         │
                  │             Context Builder              │         │
                  │        (Deduplicate & Token Limit)       │         │
                  └────────────────────┬─────────────────────┘         │
                                       │ (Formed Prompt)               │
                                       ├───────────────────────────────┘
                                       ▼
                  ┌──────────────────────────────────────────┐
                  │               API Response               │
                  └──────────────────────────────────────────┘
```

---

## 2. Pluggable Embedding Pipeline

To prevent vendor lock-in, the embedding layer uses a provider pattern:

### Directory Structure
```text
backend/app/knowledge/embeddings/
├── base_embedding_provider.py
├── sentence_transformer_provider.py
├── embedding_factory.py
└── embedding_service.py
```

### Components
1. **[BaseEmbeddingProvider](file:///d:/CodeAtlas%20AI/backend/app/knowledge/embeddings/base_embedding_provider.py)**: Abstract class defining formatting requirements for dimensions, names, and vectorizations.
2. **[SentenceTransformerProvider](file:///d:/CodeAtlas%20AI/backend/app/knowledge/embeddings/sentence_transformer_provider.py)**: Implements local inference using `all-MiniLM-L6-v2` yielding **384-dimensional** embeddings. Incorporates an offline mock fallback (deterministic text hashing) for unit test efficiency.
3. **[EmbeddingFactory](file:///d:/CodeAtlas%20AI/backend/app/knowledge/embeddings/embedding_factory.py)**: Resolves provider name strings to active instances.
4. **[EmbeddingService](file:///d:/CodeAtlas%20AI/backend/app/knowledge/embeddings/embedding_service.py)**: High-level wrapper that use cases interact with directly.

---

## 3. Vector Store Design

Supports multi-database environments with automatic capability checks:

### Directory Structure
```text
backend/app/knowledge/vector_store/
├── base_vector_store.py
├── pgvector_store.py
├── sqlite_vector_store.py
└── vector_store_factory.py
```

### Dual-Dialect Support
- **[PgVectorStore](file:///d:/CodeAtlas%20AI/backend/app/knowledge/vector_store/pgvector_store.py) (Production)**: Connects to PostgreSQL, utilizing the `pgvector` extension and indexing (`HNSW` with cosine distance operator `<=>`).
- **[SqliteVectorStore](file:///d:/CodeAtlas%20AI/backend/app/knowledge/vector_store/sqlite_vector_store.py) (Testing/Local Dev)**: Reads float vectors serialized as JSON strings in `sqlite` and computes cosine similarities in Python memory for isolated database assertions.
- **[SafeVector](file:///d:/CodeAtlas%20AI/backend/app/adapters/models/embedding_model.py)**: Custom SQLAlchemy `TypeDecorator` mapping schema definitions dynamically to `VECTOR` (PostgreSQL) or `TEXT` (SQLite) at migration time.

---

## 4. Knowledge Graph Schema

Models file relationships, configurations, and AST structures using relational tables.

### Directory Structure
```text
backend/app/knowledge/graph/
├── graph_types.py
├── graph_repository.py
├── graph_builder.py
├── graph_queries.py
└── graph_traversal.py
```

### Node Classifications
- **REPOSITORY**: Project source root.
- **SNAPSHOT**: Git commit reference.
- **FOLDER**: Directories mapping structure.
- **FILE**: Code files.
- **CLASS**: Structural class declarations.
- **INTERFACE / ENUM**: Structural abstractions.
- **METHOD / FUNCTION**: Invocable blocks.
- **CONFIG_FILE / API_ENDPOINT**: Settings or API bindings.

### Edge Relationship Definitions
- **CONTAINS**: Hierarchy representation (e.g. Repository -> Snapshot -> Folder -> File).
- **DEFINES**: Scope markers (e.g. File -> Class -> Method).
- **IMPORTS**: Relative imports (e.g. File -> File).
- **DEPENDS_ON**: External packages or libraries.
- **CALLS**: Method/Function executions.
- **EXTENDS / IMPLEMENTS**: Interface inheritance relationships.

---

## 5. Hybrid Retrieval Workflow

Orchestrated by the **[HybridRetriever](file:///d:/CodeAtlas%20AI/backend/app/knowledge/hybrid_retriever.py)**:

1. **Caching**: Check database cache for query match on the current snapshot version.
2. **Vector Retrieval**: Embed the user query and query the vector store for top-K matching code chunks.
3. **Graph Expansion**: Look up the graph node corresponding to each retrieved chunk. Execute a **BFS Traversal** (via [GraphTraversal](file:///d:/CodeAtlas%20AI/backend/app/knowledge/graph/graph_traversal.py)) up to depth D, gathering related classes, base files, and import targets.
4. **Metadata Hydration**: Join with code chunks and files tables to load content strings and relative paths.
5. **Re-ranking**: Pass candidates to the **[RankingEngine](file:///d:/CodeAtlas%20AI/backend/app/knowledge/ranking.py)**, boosting matching symbol names, folder scopes, and highly-connected graph nodes.
6. **Prompt Assembly**: Build prompt blocks using the **[ContextBuilder](file:///d:/CodeAtlas%20AI/backend/app/knowledge/context_builder.py)**, adhering strictly to token budgets.

---

## 6. Context Builder & Ranking Strategy

### Token Budgets
The context builder enforces token constraints using a character-based token estimator (`len(text) // 4`). Chunks are loaded in order of priority until the target budget (e.g. 4000 tokens) is reached, preventing truncation at the LLM gateway.

### Ranking Weights
The final score of a chunk is recalculated as:
$$\text{Score} = \text{CosineSimilarity} + \text{TermMatchBoost} + \text{TypeBoost} + \text{GraphCentralityBoost}$$
* Direct name match: $+0.15$
* File/Folder path match: $+0.12$
* Entity type matches query intent (e.g. query asks for class, matches `CLASS` chunk): $+0.10$
* Graph degree centrality (highly connected hubs): $+0.02 \times \ln(\text{degree} + 1)$

---

## 7. Knowledge Search REST APIs

All routes are fully authenticated and versioned under `/api/v1/`:

* **`POST /api/v1/search`**: Executes global query vectorization, traversal, and retrieval context building.
* **`GET /api/v1/repositories/{id}/knowledge`**: Returns summary graph statistics, averages, degree details, and sample nodes.
* **`GET /api/v1/repositories/{id}/context`**: Generates and returns a prompt block context string for a query.
* **`GET /api/v1/repositories/{id}/graph`**: Lists all graph nodes and edges.
* **`GET /api/v1/repositories/{id}/graph/statistics`**: Returns metrics (nodes count, edges count, connected component subgraphs count, average degree).
* **`GET /api/v1/repositories/{id}/graph/node/{node_id}`**: Retrieves metadata and properties for a specific graph node.
* **`GET /api/v1/repositories/{id}/search`**: Routes semantic query searches scoped to a single repository.
* **`GET /api/v1/repositories/{id}/search/similar`**: Finds similar code chunks given a source chunk ID.
* **`GET /api/v1/repositories/{id}/embeddings`**: Lists active chunk embeddings metadata.
