# Design Document

## 1. Purpose and Scope

This document provides a **detailed, explicit** design specification for the Lecture Builder Agent. It describes all system components, data models, workflows, interfaces, non-functional requirements, and dependencies. No assumptions are made about prior knowledge; every element is defined.

### 1.1 Objectives

- Define architecture and module responsibilities.
- Specify data schemas and storage strategies.
- Detail agent workflows and orchestration logic.
- Describe integration points (APIs, UI, persistence).
- Enumerate non-functional requirements (performance, security, compliance).
- Reference supporting documentation for deeper diagrams and policies.

### 1.2 Out of Scope

- Implementation code examples.
- Detailed UI mockups (see ARCHITECTURE.md).
- Security policies beyond summary (see SECURITY.md).

---

## 2. System Overview

The Lecture Builder Agent transforms a single-topic prompt into a fully fleshed, university-grade lecture or workshop package. Key characteristics:

- **Local-first**: Offline capability via cached corpora and local models.
- **Multi-agent orchestration**: Managed by LangGraph.
- **Streaming updates**: Real-time document evolution in a browser UX.
- **Persistence**: State and logs in SQLite (or Postgres).
- **Export**: Markdown, DOCX, PDF with full citations and metadata.

Component interactions are visualized in ARCHITECTURE.md.

---

## 3. Agent Workflows

Each agent is a LangGraph node. Workflow phases:

| Phase        | Agent              | Input                                    | Output                                       | Retry Logic                            |
| ------------ | ------------------ | ---------------------------------------- | -------------------------------------------- | -------------------------------------- |
| 1. Plan      | Curriculum Planner | `prompt`                                 | `State.learning_objectives`, `State.modules` | None                                   |
| 2. Search    | Researcher-Web × N | `learning_objectives`                    | `State.citations[]`, `State.snippets[]`      | On network/error, retry 2×             |
| 3. Synthesis | Content Weaver     | `State.modules`, `State.citations`       | `State.outline` (JSON schema)                | On schema-failure, regenerate up to 3× |
| 4. Critique  | Pedagogy Critic    | `State.outline`                          | `State.critique_report`                      | None                                   |
|              | Fact Checker       | `State.outline`                          | `State.factcheck_report`                     | Retry flagged segments 3×              |
| 5. Approve   | Human-in-Loop      | Full `State`                             | `State.outline` (accepted edits)             | Manual                                 |
| 6. Publish   | Exporter           | Final `State.outline`, `State.citations` | Markdown, DOCX, PDF files                    | None                                   |

Agents communicate via typed state transitions and stream deltas to the frontend.

---

## 4. Orchestration Layer

### 4.1 LangGraph Orchestrator

- Graph topology defined in `langgraph.json` and loaded at runtime.
- Maintains a `State` class with attributes:
  - `prompt: str`
  - `learning_objectives: List[str]`
  - `modules: List[Module]`
  - `citations: List[Citation]`
  - `snippets: List[TextSnippet]`
  - `outline: OutlineSchema`
  - `critique_report: CritiqueReport`
  - `factcheck_report: FactCheckReport`
  - `action_log: List[ActionRecord]`

### 4.2 Checkpointing

- **SQLite**: `SqliteCheckpointSaver` stores serialized `State` snapshots with timestamp.
- **Resume**: Graph can invoke with `resume=True` to continue after crash.
- **Optional Postgres**: Swap saver to `PostgresCheckpointSaver` for concurrent loads.

### 4.3 Edge Policies & Concurrency

- **Confidence threshold**: Nodes emit `confidence` scores; Planner halts if <0.8.
- **Retry loops**: Predicated on failure codes in node outputs.
- **Parallel Researcher**: Fan-out N concurrent searches; merge via semantic deduplication.

---

## 5. Data Model

### 5.1 SQL Schema (SQLite)

- **Table `state_snapshots`**: `id (UUID)`, `timestamp (ISO8601)`, `state_blob (JSON)`.
- **Table `citations`**: `id`, `url`, `title`, `retrieved_at`, `license`, `agent_name`.
- **Table `snippets`**: `id`, `citation_id`, `text`, `agent_name`.
- **Table `documents`**: `version_id`, `parent_version_id`, `timestamp`, `parquet_blob`.
- **Table `action_log`**: `record_id`, `agent_name`, `input_hash`, `output_hash`, `tokens_used`, `cost_usd`.
- **Table `critique_report`**: `version_id`, `bloom_coverage_score`, `activity_diversity_score`, `notes`.
- **Table `factcheck_report`**: `version_id`, `unsupported_claim_count`, `regex_flags`, `cleanlab_scores`.

### 5.2 Entity Definitions

- **Module**: `{id, title, duration_min, learning_objectives}`
- **Citation**: `{url, title, retrieved_at (ISO8601), license, source_agent}`
- **OutlineSchema**: JSON schema defining `modules[]` with `activities[]`, `speaker_notes`, and `slides[]`.

Further ER diagrams in ARCHITECTURE.md.

---

## 6. Retrieval & Citation

### 6.1 Web Search Providers

- **Clients**: `ChatPerplexity` from `langchain_perplexity` or `TavilySearchAPIWrapper` from `langchain_community`, exposed via the `SearchClient` abstraction.
- **Query templates**: Include objective keywords, `--QDF=3` for recency boost.
- **Rate limiting**: Token bucket, configurable via env var.

### 6.2 Caching & Offline Support

- **Local cache table**: `cache_key`, `response_blob`, `fetched_at`.
- **Offline fallback**: Query local dense index built from CC-BY abstracts (50k docs).

### 6.3 Citation Processing

- **Allowlist domains** and **SPDX classifier** filter entries.
- **Citation object**: `{url, title, retrieved_at, license, snippet_ids[]}`.
- Stored in `citations` table; injected as numeric footnotes in markdown.

---

## 7. Content Synthesis

### 7.1 Model Interface

- **OpenAI Function Calls**: Use `function_call` to enforce outline JSON.
- **Model parameters**: `temperature=0.2`, `max_tokens=2048`, `stream=True` for synthesizer.

### 7.2 Schema-Driven Generation

- **Outline JSON Schema** (`schemas/outline.json`): defines modules, activities, durations.
- **Validation**: `jsonschema` enforces before writing to state.

### 7.3 Streaming Protocols

- **LangGraph streams**:
  - `stream(messages)`: token-level markdown chunks.
  - `stream(values)`: structured state snapshots (e.g. objectives).
  - `stream(updates)`: citation updates.
  - `stream(debug)`: critic warnings and fact-check flags.

---

## 8. Quality Control

### 8.1 Pedagogy Critic

- **Inputs**: `OutlineSchema`
- **Checks**:
  - Coverage across Bloom levels (remember, apply, analyze, evaluate, create).
  - At least one `activity` per module of type `discussion`, `exercise`, `quiz`.
  - Total cognitive load ≤ 100 units (configurable).

- **Output**: `CritiqueReport` stored in table.

### 8.2 Fact Checker

- **Methods**:
  - Regex patterns for unsupported claims (e.g. no source after statistic).
  - Cleanlab classifier probability ≤ 0.05 triggers flag.

- **Retry policy**: regenerate flagged segments up to 3 attempts.
- **Output**: `FactCheckReport`.

---

## 9. Persistence & Versioning

### 9.1 Document Versioning

- Each accepted outline is serialized as Parquet and stored in `documents` table.
- `parent_version_id` links to previous version, enabling diff retrieval.

### 9.2 Checkpoint Strategy

- Checkpoints taken after each agent completes.
- Retention policy: keep last 50 checkpoints per workspace.

---

## 10. Exporters

### 10.1 Markdown Exporter

- Converts `OutlineSchema` → Markdown using Jinja templates.
- Footnotes appended with citation metadata (`[n]: url (license)`).

### 10.2 DOCX Exporter

- Templates in `backend/export/docx_templates/`.
- Covers:
  - Cover page with `title`, `subtitle`, `author`, `date`.
  - Header/footer branding blocks.
  - Styles for headings, bullet lists, tables.

### 10.3 PDF Exporter

- Uses WeasyPrint:
  - Renders HTML version of Markdown (via `markdown2`).
  - Bundles Noto font family.
  - MathJax pre-render for LaTeX fragments.

### 10.4 Package Signing

- After export, generate `manifest.json` with file SHA-256s.
- Optionally sign with GPG key if configured.

---

## 11. Web UX

### 11.1 Frontend Components

- **DocumentPanel**: displays streamed markdown with diff highlights.
- **LogPanel**: lists `action_log` entries, filterable by agent and severity.
- **SourcesPanel**: shows citation snippets with `license` badges.
- **ControlsPanel**: run/pause/retry, model selector, export buttons.
- **QualityTab**: visual gauges for pedagogy and fact-check scores.

### 11.2 Streaming Implementation

- **SSE endpoints**:
  - `/stream/state`
  - `/stream/actions`
  - `/stream/citations`

- **Client**: `stream.ts` subscribes and dispatches updates to React store.

### 11.3 Accessibility

- WCAG 2.1 AA compliance:
  - ARIA roles on panels.
  - Contrast ratios > 4.5:1.
  - Keyboard navigation for diff toggles.

---

## 12. Deployment & Configuration

### 12.1 Environment

- **Python** ≥ 3.11
- **Node.js** ≥ 18
- **Poetry** for backend; **npm** for frontend.

### 12.2 Environment Variables

| Name                 | Purpose                                    | Required?              |
| -------------------- | ------------------------------------------ | ---------------------- |
| `OPENAI_API_KEY`     | OpenAI authentication                      | Yes                    |
| `PERPLEXITY_API_KEY` | Perplexity Sonar authentication           | No (if using Tavily)   |
| `TAVILY_API_KEY`     | Tavily search authentication              | No (if using Perplexity) |
| `SEARCH_PROVIDER`    | `perplexity` or `tavily`                   | No (default `perplexity`) |
| `MODEL_NAME`         | `o4-mini` or `o3`                          | No (default `o4-mini`) |
| `DATA_DIR`           | Path for SQLite DB, cache, workspace files | No (default `./data`)  |
| `DATABASE_URL`       | Postgres connection string (optional)      | No                     |
| `GPG_SIGN_KEY`       | Key ID for package signing (optional)      | No                     |

### 12.3 Startup Commands

1. **Backend**: `poetry run uvicorn backend.main:app --reload`
2. **Frontend**: `cd web && npm run dev`
3. **Testing**: `pytest`, `npm test`, `k6 run performance/script.js`

---

## 13. Non-Functional Requirements

| Category          | Requirement                                                             | Verification                               |
| ----------------- | ----------------------------------------------------------------------- | ------------------------------------------ |
| **Performance**   | 95th percentile prompt-to-first-stream < 2s under 50 concurrent users   | k6 performance tests                       |
| **Security**      | Secrets stored in Vault or `.env` with CI gating; DB encrypted at rest  | Manual review (SECURITY.md), audit scripts |
| **Reliability**   | Resume graph after crash in <500ms; checkpoint retention ≥ 50 snapshots | Automated resilience tests                 |
| **Compliance**    | Audit trail unalterable; role-based access enforced                     | `backend/cli/audit.py` verification        |
| **Accessibility** | WCAG 2.1 AA compliance on frontend                                      | Lighthouse CI audits                       |

---

## 14. References and Next Steps

- **ARCHITECTURE.md** — ER diagrams, sequence charts, component diagram
- **SECURITY.md** — Threat model, vault integration, encryption details
- **TEST_PLAN.md** — Test cases matrix, performance benchmarks
- **GOVERNANCE.md** — SLO definitions, metrics collection, dashboard config

**Next Step**: Review design with cross-functional team. Finalize data model and edge case handling before development continues. Ensure alignment with security and UX guidelines.
