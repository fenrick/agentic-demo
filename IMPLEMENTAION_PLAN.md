# Implementation Plan

## A. Environment & Scaffolding

1. **Project Initialization**

   * Initialise Git repo, configure `poetry` for Python ≥ 3.11.
   * Define folder layout (`/src`, `/tests`, `/workspace`, `/scripts`).
   * Add CI pipeline stub (lint, unit tests).

2. **Dependency Management**

   * Add core dependencies: `langgraph`, `openai`, `perplexity-api`, `sqlite3`, `python-docx`, `weasyprint`, `fastapi`, `uvicorn`.
   * Configure `.env` loader for `OPENAI_API_KEY`, `PERPLEXITY_API_KEY`, `MODEL_NAME`, `DATA_DIR`.

3. **Local Workspace Persistence**

   * Scaffold `AsyncSqliteSaver` integration.
   * Define initial SQLite schema migrations (state, documents, citations, logs).

---

## B. Orchestration Core (LangGraph StateGraph)

1. **State Model Definition**

   * Create a `State` dataclass: fields for `prompt`, `sources`, `outline`, `log`, version, etc.

2. **Graph Construction**

   * Instantiate a `StateGraph` with nodes: Planner, Researcher-Web, Content Weaver, Critic(s), Approver, Exporter.
   * Wire streaming policies (`.astream('values')`, `.astream('updates')`, etc).

3. **Edge Policies & Loop Logic**

   * Implement routing policy: Planner → Researcher until `confidence ≥ 0.9`.
   * Critic retry logic with max-3 loops on failures.
   * Fan-out/fan-in for Researcher-Web with semantic deduplication.

4. **Checkpointing & Resume**

   * Integrate `SqliteCheckpointSaver` so `graph.invoke(resume=True)` picks up state file.

---

## C. Retrieval & Citation Layer

1. **Perplexity & Fallback Search Agent**

   * Build `ResearcherWeb` node: calls Perplexity API; fallback to OpenAI search mode when offline.
   * Parse, rank by authority, return snippet + URL.

2. **Citation Object & Storage**

   * Define `Citation` model (`url`, `title`, `retrieved_at`, `licence`).
   * Persist citations in SQLite; link to state.

3. **Copyright Filter**

   * Implement allowlist domains (CC, gov, acad).
   * Discard or flag non-compliant results.

---

## D. Content Synthesis

1. **Content Weaver Agent**

   * Function-call LLM with JSON schema for (`learning_objectives`, `activities`, etc).
   * Stream token-wise markdown deltas (`stream(messages)`).

2. **Schema Enforcement**

   * Validate LLM output against JSON schema; reject/regenerate on schema errors.

3. **Markdown Conversion**

   * Build converter from schema → markdown outline + speaker notes + slide bullets.

---

## E. Quality Control

1. **Pedagogy Critic**

   * Check Bloom taxonomy coverage and cognitive-load balance.
   * Produce structured report of gaps.

2. **Fact Checker**

   * Integrate Cleanlab for probability-based hallucination detection.
   * Regex-scan for unsupported claims; flag lines.

3. **Loop-back Logic**

   * On critic failures, trigger regeneration of affected sections (max 3 retries).

4. **Audit Logging**

   * Emit `{agent, input_hash, output_hash, tokens, cost}` to SQLite logs.

---

## F. Persistence & Versioning

1. **State & Document Tables**

   * Finalise schemas for `state`, `documents`, `citations`, `logs`.

2. **Parquet Version Blobs**

   * Store each document version as Parquet; enable diff-friendly retrieval.

3. **Checkpoint Tests**

   * Write integration test: start graph, kill process, resume and verify state continuity.

---

## G. Exporters

1. **Markdown Exporter**

   * Render canonical markdown; include front-matter for `topic`, `model`, `commit_sha`.
   * Embed footnote citations.

2. **DOCX Exporter**

   * Use `python-docx` template: cover page, headers/footers.
   * Inject TOC and bibliography.

3. **PDF Exporter**

   * Wrap markdown → HTML → PDF via `weasyprint`; include branding assets.

4. **Downloads API**

   * FastAPI endpoint to retrieve `/downloads/{workspace}/{format}`.

---

## H. Browser-Based UX

1. **Backend SSE Endpoints**

   * Expose `/stream` for Server-Sent Events bound to `StateGraph.astream()`.
   * Control endpoints: `/run`, `/pause`, `/retry`, `/resume`.

2. **React + Tailwind Frontend**

   * **Panels**: Document (diff highlighting, popovers), Action Log (filters, search), Sources, Controls, Downloads.
   * Implement token-by-token typewriter effect for markdown.
   * Citation popover modal showing metadata & timestamp.

3. **State Sync**

   * Client subscribes to SSE; applies diffs to workspace store (e.g. Zustand or Redux).

---

## I. Deployment & Offline Mode

1. **FastAPI App**

   * Serve LangGraph endpoints, static frontend, downloads.

2. **Offline Flag**

   * `--offline` disables external calls; Researcher uses cached citations; Fact Checker skips web checks.

3. **Docker Profile (optional)**

   * Containerise for reproducible local dev; mount `DATA_DIR`.

---

## J. QA, Metrics & Governance

1. **Metric Collection**

   * Implement metrics aggregator: Pedagogical rubric score, hallucination rate, human edit time, token cost.
   * Webhook alerts for threshold breaches.

2. **RBAC & Security**

   * FastAPI roles (viewer, editor, admin) with JWT or API-key.
   * Encrypt SQLite via mounted encrypted volume.

3. **Audit Trail**

   * Compute and store SHA-256 of each state; immutable log for disputes.

---

## Next Steps (Spike & Validation)

1. **Rubric Validation**: Workshop with two faculties to refine pedagogical checks.
2. **Checkpoint Spike**: Measure resume latency with large state (\~10 MB).
3. **UI Diff Prototype**: Build minimal React component showing streaming diffs.

---