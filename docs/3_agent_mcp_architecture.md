# Agent & MCP Architecture - CodeAtlas AI Enterprise Platform

## 1. Multi-Agent Architecture

### Purpose
To define the multi-agent cognitive architecture of CodeAtlas AI, detailing how the Planner-Orchestrator, Task Router, AI Guardrails, and Response Synthesizer coordinate to execute complex software engineering requests.

### Responsibilities
* **Planner-Orchestrator**: Break down user requests into discrete execution steps.
* **Task Router**: Map steps to specialized tools or agent nodes.
* **AI Guardrails Layer**: Validate prompt safety, identify data leaks, enforce tool permissions, and ensure outputs conform to target JSON schemas.
* **Response Synthesizer**: Collect results from various tools and compile them into a clear, cohesive markdown response.

### System Diagram
```
                     +──────────────────────────────────────────+
                     |                User Query                |
                     +──────────────────────────────────────────+
                                          │
                                          ▼
                     +──────────────────────────────────────────+
                     |            AI Guardrails Layer           |
                     +──────────────────────────────────────────+
                                          │
                                          ▼
                     +──────────────────────────────────────────+
                     |           Planner-Orchestrator           |
                     +──────────────────────────────────────────+
                                          │
                                          ▼
                     +──────────────────────────────────────────+
                     |                Task Router               |
                     +──────────────────────────────────────────+
                                     ┬    ┬    ┬
                   ┌─────────────────┘    │    └─────────────────┐
                   ▼                      ▼                      ▼
           +───────────────+      +───────────────+      +───────────────+
           |  Search Tool  |      | Analysis Tool |      |  Copilot Tool |
           +───────────────+      +───────────────+      +───────────────+
```

### Advantages
* **Decomposed Reasoning**: Breaking down complex tasks into simple steps prevents model confusion and reduces hallucination rates.
* **Granular Security Controls**: Guardrails check prompts and tool outputs separately, catching security risks before they can affect the system or reach the user.
* **Adaptability**: The modular routing design allows developers to add new tools without needing to refactor the main orchestrator loop.

### Limitations
* **Compounded Latency**: A multi-agent chain with guardrails and routing loops takes longer to complete than a single, direct LLM call.
* **Error Cascade**: If the Planner-Orchestrator creates an incorrect initial plan, subsequent agents will execute invalid actions, leading to a failed response.

### Alternatives Considered
* **Single monolithic prompt**: Relying on one large prompt containing all tools. Rejected due to rapid context degradation, tool call confusion, and high error rates under complex requests.
* **Hardcoded Routing Code**: Routing calls based on simple keyword matches. Rejected because it lacks the flexibility needed to handle complex natural language queries.

### Trade-offs
* **Latency vs. Security Guardrails**: We choose to run all inputs and outputs through the Guardrails Layer. This adds a slight latency penalty but is necessary to prevent prompt injection and data leaks in enterprise environments.

### Future Improvements
* **Self-Correction Loops**: Add execution feedback loops that allow agents to self-correct and rewrite plans if a tool returns an error.
* **Parallel Tool Execution**: Enable the Task Router to run independent tools in parallel, reducing overall execution time.

### Best Practices
* **Keep Guardrails Strict**: If a prompt fails safety checks, halt execution immediately and return a standardized error instead of sending the payload to other agents.
* **Track Execution Limits**: Set maximum limits on orchestrator loops (e.g., max 5 iterations) to prevent runaway agent execution loops.

---

## 2. Agent Memory Layer

### Purpose
To outline the multi-tier memory architecture of CodeAtlas AI, describing how conversation, repository, session, and long-term project contexts are stored and retrieved.

### Responsibilities
* **Conversation Memory**: Store the active chat log to maintain conversation continuity.
* **Repository Memory**: Provide a structural index of classes, files, and dependencies.
* **Session Memory**: Track short-term operations, active filters, and temporal configurations.
* **Project Memory (Long-Term)**: Retain project-specific rules, style guides, and user preferences across multiple sessions.

### Memory Hierarchy
```
+---------------------------------------------------------------------------------+
|                               AGENT MEMORY LAYER                                |
|                                                                                 |
|  +------------------------+  +------------------------+  +-------------------+  |
|  |   Conversation Memory  |  |    Repository Memory   |  |   Session Memory  |  |
|  |   (Redis Cache - TTL)  |  | (PostgreSQL - Vector)  |  | (HTTP Session)    |  |
|  +------------------------+  +------------------------+  +-------------------+  |
|  +---------------------------------------------------------------------------+  |
|  |                            Project Memory (Long-Term)                     |  |
|  |                            (PostgreSQL Relational DB)                     |  |
|  +---------------------------------------------------------------------------+  |
+---------------------------------------------------------------------------------+
```

### Advantages
* **Efficient Context Management**: Separating memory into tiers prevents context window overload while keeping critical information accessible.
* **Fast State Retrieval**: Using Redis for short-term conversation memory keeps chat latency low.
* **Cross-Session Persistence**: Project memory ensures developer preferences (e.g. style rules) persist without requiring setup for every new session.

### Limitations
* **Context Decay**: Managing long conversations can exceed context limits, requiring summaries that may lose subtle details.
* **Cache Staleness**: If the repository changes, cache layers must be updated to prevent agents from using outdated structural information.

### Alternatives Considered
* **Pure Vector-Based Memory**: Storing all conversation history as vectors. Rejected because vector retrieval can lose exact chronological order, causing the model to lose track of recent conversation steps.
* **Passing Entire History**: Sending all conversation history with every message. Rejected because it wastes tokens and degrades performance as chat length grows.

### Trade-offs
* **Precise Chronology vs. Context Size**: We use sliding context windows combined with summarization. This keeps token costs manageable but means very old messages may be summarized or lost.

### Future Improvements
* **Dynamic Graph Memory**: Implement Graph-based conversation memory to map ideas and code entities discussed across conversations.
* **Semantic Context Hydration**: Automatically hydrate conversation memory with relevant snippets from past chats based on semantic similarity.

### Best Practices
* **Strict TTL Policies**: Set clear expiration times (e.g., 24 hours) on short-term Redis cache records to manage memory storage costs.
* **Sanitize Cached Context**: Strip credentials and PII from raw conversation logs before storing them in memory databases.

---

## 3. Tool Registry (MCP Architecture)

### Purpose
To detail the Model Context Protocol (MCP) tool registry, outlining how tools are dynamically discovered, validated, and executed by the agent framework.

### Responsibilities
* **Tool Discovery**: Expose schema formats defining tool signatures, arguments, and return types.
* **Dynamic Invocation**: Receive tool execution requests from the Task Router and dispatch them to target services.
* **Permission Constraints**: Enforce access control rules before executing tools (e.g. restricting write actions).

### MCP Schema Sample
```json
{
  "name": "search_repository_entities",
  "description": "Search class, method, and function declarations in the index by name",
  "input_schema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Name of the entity to search"
      },
      "entity_type": {
        "type": "string",
        "enum": ["class", "method", "function", "interface"]
      }
    },
    "required": ["query"]
  }
}
```

### Advantages
* **Standardized Protocol**: Using MCP ensures compatibility with any LLM client or provider that supports the standard.
* **Dynamic Expansion**: Developers can register new tools in the registry without having to update the core agent prompt or orchestrator.
* **Secure Isolation**: Tools run in isolated environments with strict input validation rules.

### Limitations
* **Payload Serialization Limits**: Large tool outputs (e.g. full directory listings) must be compressed or paginated to avoid overwhelming the model.
* **Strict Schema Adherence**: Minor formatting mismatches in tool calls can fail validation, halting agent execution.

### Alternatives Considered
* **Custom Tool Formats**: Building a proprietary tool registry system. Rejected because it lacks standard tooling support and increases integration overhead.
* **Hardcoded Tools in Agent Prompt**: Describing tools as text inside the main prompt. Rejected because it consumes context tokens and makes dynamic updates difficult.

### Trade-offs
* **Schema Strictness vs. Agent Flexibility**: We enforce strict schema validation for all tool inputs. This can lead to occasional tool call failures if the agent makes minor syntax errors, but prevents invalid parameters from causing backend crashes.

### Future Improvements
* **Sandboxed Tool Environments**: Run complex execution tools in isolated micro-containers to prevent security risks.
* **Adaptive Tool Selection**: Implement routing models that learn which tools are most effective for specific queries, reducing unnecessary calls.

### Best Practices
* **Validate Every Parameter**: Always run schema checks on tool inputs before execution, even if the model claims the input is valid.
* **Descriptive Tool Errors**: When a tool fails, return a clear, descriptive error so the agent understands the failure and can try to correct it.

---

## 4. Sequence Diagrams

### Purpose
To document the message flows and component interactions for repository indexing, security scanning, copilot planning, and repository chat.

### Sequence Flows

#### Repository Indexing & AST Parsing Flow
```
User Client         Web API Gateway      Workflow Engine      AST Service       PostgreSQL DB
    │                      │                    │                  │                  │
    │─── Upload Zip ──────>│                    │                  │                  │
    │                      │─── Schedule Task ─>│                  │                  │
    │<── Status (202) ─────│                    │─── Parse AST ───>│                  │
    │                      │                    │                  │─── Write AST ───>│
    │                      │                    │<── AST Stored ───│                  │
    │                      │<── Task Complete ──│                  │                  │
```

#### Engineering Copilot Planning Flow
```
User Client         Web API Gateway      Planner-Agent       Tool Registry        LLM Engine
    │                      │                    │                  │                  │
    │── Create ADR Plan ──>│                    │                  │                  │
    │                      │─── Initiate Plan ─>│                  │                  │
    │                      │                    │─── Query Schema >│                  │
    │                      │                    │                  │─── Fetch Prompt >│
    │                      │                    │<── Prompt Formed ───────────────────│
    │                      │                    │─── Generate ADR ───────────────────>│
    │                      │                    │<── ADR Markdown ────────────────────│
    │                      │<── Stream Plan ────│                  │                  │
    │<── Show ADR Output ──│                    │                  │                  │
```

### Advantages
* **Clear Execution Paths**: Sequence flows make it easier to trace asynchronous events and debug network bottlenecks.
* **Concurrency Visualization**: Helps identify parallel execution opportunities (e.g. concurrent embedding generation and AST parsing).

### Limitations
* **Static View**: Diagrams represent typical execution paths and may not show all edge cases or error conditions.
* **Maintenance Cost**: As APIs and service boundaries evolve, diagrams must be updated to keep them accurate.

### Alternatives Considered
* **Textual Flow Descriptions**: Writing out system interactions in paragraphs. Rejected because visual diagrams are easier for developers and architects to interpret.

### Trade-offs
* **Simple Flow Representation vs. Complete Detail**: The diagrams focus on primary system boundaries. We trade extreme low-level call details to keep the diagrams readable and maintainable.

### Future Improvements
* **Dynamic Trace Generation**: Generate runtime interaction diagrams from OpenTelemetry traces for real-time visualization.
* **Interactive Architecture Visualizer**: Build interactive sequence charts directly in the developer dashboard to show system state during executions.

### Best Practices
* **Standardize Lifelines**: Keep service lifelines consistent across all diagrams to make them easy to follow.
* **Highlight Async Boundaries**: Use distinct notations (e.g., dotted lines) to clearly distinguish asynchronous task steps from synchronous HTTP calls.
