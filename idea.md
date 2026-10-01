# Conversa

> **Tagline:** A persistent, stateful relationship-strategy agent and conversation planning simulator.

## 1. Core Concept

**Conversa** is an agentic, stateful AI strategy application that maintains a living model of an ongoing conversation and updates that model after every interaction. Rather than acting as a simple text generator, Conversa functions as a conversation planner. It reasons over stored context, generates strategic messages, critiques its own outputs, and adapts its approach over a defined multi-turn "conversation horizon."

The system operates strictly as an isolated, manual-input tool. It does not sync directly with messaging apps, preserving user privacy and architectural simplicity. The LLM is not the system itself; it is an intelligent component inside a deterministic software architecture.

## 2. Core Architecture Principles

The entire project relies on strict separation of concerns to ensure consistency, debuggability, and state integrity:

| Component | Responsibility |
| :--- | :--- |
| **MEMORY** | What happened / what is known |
| **STATE** | What is true right now |
| **STRATEGY** | What approach should be taken (Structured) |
| **GENERATION** | What should be said (Prose) |
| **CRITIC** | Does the output satisfy the strategy? |
| **EVENTS** | What changed in the system |
| **BRANCH** | What would happen in an isolated hypothetical |

## 3. Database & Storage Architecture

**PostgreSQL is the absolute source of truth.** To prevent the AI from hallucinating permanent facts, all structured data, states, events, and memories live in Postgres. For the MVP, **pgvector** is used for embeddings, avoiding the complexity of a separate Vector DB until scale demands it.

### Event-Driven State
Instead of mutating rows in place, the Conversation State is versioned and driven by an **Event Store**. 
- Events (`MESSAGE_RECEIVED`, `DRAFT_ACCEPTED`, `MEMORY_CORRECTED`) yield a new `state_version`.
- This ensures full auditability, time-travel debugging, and robust replay capabilities.

### Optimistic Concurrency
To prevent race conditions (e.g., a user updates an assumption in one tab while accepting a draft in another), the database uses optimistic concurrency. Updates require a matching `state_version` or they throw a conflict, forcing a reload of the latest state.

## 4. The Memory System & Context Building

### The Memory Lifecycle
Memories (Episodic and Semantic) are not just raw vectors. They contain **provenance and confidence** metadata:
`Observation` → `Candidate Memory` → `Confidence Score` → `User Confirmation` → `Active Memory`.
This prevents the system from locking in incorrect inferences. Users can deprecate or correct memories, which updates the status rather than silently overwriting historical evidence.

### Hybrid Retrieval & The Context Builder
Pure vector search is insufficient. Conversa uses a **Hybrid Retrieval Engine**:
`Semantic Similarity + Recency Weighting + Confidence Weighting + Entity Matching`.

To prevent token explosion as conversations grow to 500+ messages, a **Context Builder** strictly gates what the LLM sees into three layers:
1. **Always:** Current state, latest messages, objective.
2. **Usually:** Conversation summary, active assumptions, unresolved topics.
3. **On-Demand:** Highly scored historical memories, specific old events.

## 5. Agent Orchestration: Strategy & Bounded Loops

### Strategy vs. Generation Separation
The Planner and Generator are completely decoupled. 
1. The **Strategy Planner** produces a *structured JSON object* (via Pydantic validation) defining the approach, tone, directness, and constraints. 
2. The **Response Generator** translates this strict JSON strategy into natural language.
This means debugging is isolated: we can explicitly test if the *strategy* was wrong or if just the *prose* was bad.

### Bounded Self-Critique Loop
An open-ended agent loop leads to unpredictable latency and token burn. Conversa uses a **Bounded State Machine** (Max 2 Revisions):
`Generate` → `Critique (Structured JSON scores)` → `Pass? (If No, Revise)` → `Final`.
If the revision fails again, the system halts and returns the best available candidate alongside the Critic's noted weaknesses.

## 6. Branching & Simulation

"What-If" branching is a core feature, but branches are strictly isolated from the canonical state. 
- Branches use a **Snapshot + Delta** architecture. They inherit the canonical message history and append only the simulated branch messages.
- A branch has its own simulated state and never contaminates `conversation_states` unless a user explicitly accepts and merges a real action.

## 7. Engineering & Production Readiness

- **API & Backend:** FastAPI orchestrates the routing and agent workers.
- **Intelligent Model Routing (Cost Optimization):** To prevent astronomical token costs in high-volume interactions, Conversa employs a hybrid model routing strategy:
  - **GPT-5.6 Sol (Flagship):** Reserved exclusively for the **Strategy Planner**. This tier handles the heavy cognitive load of multi-turn reasoning, psychological planning, and state analysis.
  - **GPT-5.6 Luna (Efficient):** Handles all frequent, scoped, and high-volume tasks: extracting memories, summarizing contexts, retrieving/ranking vectors, drafting the prose responses, and running the self-critique evaluation loop. This drives costs down significantly (e.g., $0.20/1M input) without degrading the core strategic reasoning.
- **Observability:** Every generation logs the `request_id`, `state_version`, `retrieved_memory_ids`, `strategy`, `critic_result`, `latency`, and `token_usage` to ensure the system's reasoning is fully auditable.
- **Robust Testing:** 
  - *Unit:* Memory deduplication, schema validation, state transitions.
  - *Integration:* Full message pipeline (Extract → Retrieve → Plan → Generate → Critic → State Update).
  - *Long-Horizon Simulation:* 50-turn automated tests verifying that objectives persist, contradictions are avoided, deleted memories don't resurface, and the persona remains stable.

## 8. Development Roadmap

### MVP (V1)
- **Synchronous Execution:** Simple request/response API.
- **Database:** PostgreSQL + pgvector (Unified storage).
- **Core Loop:** Manual input → Context Builder → Strategy Planner → Generator → Critic → User Acceptance → State Event.
- **UI:** Next.js Dashboard with the Conversation Workspace and Strategy Rationale sidebars.

### V2 & Beyond
- Hybrid Retrieval (combining vector with recency/confidence math).
- Advanced What-If Branches (Snapshot + Delta mechanics).
- Asynchronous Job Queues (Background workers / WebSockets for lower perceived latency).
- Advanced Simulation & Predictive Branching.

## 9. UI / UX Flow (Modern LLM-Style Interface)

The interface abandons clunky, multi-panel dashboards in favor of a sleek, familiar ChatGPT-style layout, heavily customized for strategic conversational planning.

### The Sidebar (Left)
- **Previous Conversations:** A history list of all active or past cases.
- **New Conversation:** Button to initialize a new strategy session.

### Main Screen: Initialization (New Case)
When starting a new conversation, the main screen presents a clean, vertical form:
1. **Target Profile (Optional fields):** Name, Gender, Place of first meeting, Relationship dynamic. *(Architecture rule: If a field is left blank, the agent gracefully ignores it and does not hallucinate details to fill the gap).*
2. **Current Situation:** The target's Last Message.
3. **Strategic Goal:** The Objective (e.g., "Get her to agree to a date") and length constraints (e.g., "Max 2 lines").
4. **Action:** A prominent `[Start]` button to kick off the state machine.

### Main Screen: The Conversation Feed (Subsequent Turns)
Once started, the UI transitions into a vertical chat feed consisting of recurring block clusters:
1. **Target's Input Block:** Shows her latest response. **Crucially, this is editable** so the user can fix typos or tweak exactly what she said before the AI processes it.
2. **Additional Context Block:** A quick input field for the user to add subtext (e.g., *"She is joking here"*).
3. **Agent Output Block:** Displays the Agent's Strategy Rationale and the Final Drafted Message.
4. **Action Row:** 
   - `[Rerun Agent]` (Regenerate the strategy/draft if the user dislikes the approach).
   - `[Accept & Advance]` (Locks the message into the state history and awaits her next reply).
