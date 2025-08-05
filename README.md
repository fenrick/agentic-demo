# Lecture Builder Agent

A local-first, multi-agent system that generates high‑quality, university‑grade lecture and workshop outlines (with supporting materials) from a single topic prompt. Orchestrated by LangGraph and implemented in Python, the system integrates OpenAI o4‑mini/o3 models, pluggable web search (Perplexity Sonar or Tavily) via LangChain, and a React‑based UX. Full state, citations, logs, and intermediates persist in SQLite (with optional Postgres fallback). Exports include Markdown, DOCX, and PDF.

---

## Table of Contents

- [Lecture Builder Agent](#lecture-builder-agent)
  - [Table of Contents](#table-of-contents)
  - [Key Features](#key-features)
  - [Architecture Overview](#architecture-overview)
  - [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
    - [Configuration](#configuration)
    - [Running Locally](#running-locally)
  - [Component Breakdown](#component-breakdown)
    - [Orchestration (LangGraph)](#orchestration-langgraph)
    - [Retrieval \& Citation](#retrieval--citation)
    - [Content Synthesis](#content-synthesis)
    - [Quality Control](#quality-control)
    - [Persistence \& Versioning](#persistence--versioning)
    - [Frontend UX](#frontend-ux)
    - [Exporters](#exporters)
  - [Storage Options](#storage-options)
  - [Configuration \& Environment Variables](#configuration--environment-variables)
  - [Logging \& Tracing](#logging--tracing)
  - [Testing \& QA](#testing--qa)
  - [Operational Governance](#operational-governance)
  - [Roadmap \& Next Steps](#roadmap--next-steps)
  - [Contributing](#contributing)
  - [License](#license)
  - [Additional Documentation](#additional-documentation)

---

## Key Features

- **Multi-Agent Workflow**: Planner, Researcher, Synthesiser, Pedagogy Critic, Fact Checker, Human-in-Loop, and Exporter nodes working in a LangGraph state graph.
- **Streaming UI**: Token-level draft streaming with diff highlights; action/reasoning log streaming via SSE.
- **Robust Citations**: Pluggable Perplexity or Tavily search, citation metadata stored in SQLite, Creative Commons and university domain filtering.
- **Local-First**: Operates offline using cached corpora and fallback to local dense retrieval.
- **Flexible Exports**: Markdown (canonical), DOCX (python-docx), PDF (WeasyPrint), with cover page, TOC, and bibliography.
- **Audit & Governance**: Immutable action logs, SHA‑256 state hashes, role‑based access, optional database encryption.

---

## Architecture Overview

The system comprises:

1. **LangGraph StateGraph**: Manages typed `State` objects through nodes and edges. Handles checkpointing in SQLite.
2. **Agents**:
   - **Curriculum Planner**: Defines learning objectives and module structure.
   - **Researcher-Web**: Executes parallel Perplexity Sonar/OpenAI searches, dedupes and ranks sources.
   - **Content Weaver**: Generates Markdown outline, speaker notes, slide bullets.
   - **Pedagogy Critic**: Verifies Bloom taxonomy coverage, activity diversity, cognitive load.
   - **Fact Checker**: Scans for hallucinations via Cleanlab/regex.
   - **Exporter**: Renders final deliverables.

3. **Web UX**: React + Tailwind, SSE-driven, panels for document, log, sources, and controls.
4. **Storage Layer**: SQLite for state, logs, citations; optional Postgres via repository abstraction.
5. **Export Pipeline**: Pandoc-ready Markdown, python-docx, WeasyPrint PDF.

### Stream Channels

Agents emit events over several LangGraph channels that the frontend can
subscribe to:

- `messages` – token-level content such as LLM outputs.
- `debug` – diagnostic information and warnings.
- `values` – structured state snapshots.
- `updates` – citation and progress updates.

---

## Getting Started

### Prerequisites

- Python 3.11 or later
- Node.js 18+ (for frontend)
- `poetry` (recommended) or `pipenv`
- OpenAI API key
- Perplexity or Tavily API key

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/your-org/lecture-builder-agent.git
   cd lecture-builder-agent
   ```

2. Backend dependencies:

   ```bash
   poetry install
   ```

3. Frontend dependencies:

   ```bash
   cd frontend
   npm install
   ```

4. Build the frontend:

   ```bash
   ./scripts/build_frontend.sh
   ```

   This generates the static assets in `frontend/dist` that the FastAPI server serves.

### Configuration

Copy the sample environment file and provide your secrets:

```bash
cp .env.example .env
# Edit .env:
# OPENAI_API_KEY=sk-...
# PERPLEXITY_API_KEY=...
# TAVILY_API_KEY=...
# SEARCH_PROVIDER=perplexity  # or 'tavily'
# MODEL_NAME=o4-mini
# DATA_DIR=./workspace
# LANGCHAIN_API_KEY=...
# LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
```

### Running Locally

1. **Start the backend** (FastAPI + LangGraph):

   ```bash
   ./scripts/run.sh [--offline]
   ```

   This helper invokes Uvicorn with:

   ```bash
   poetry run uvicorn web.main:create_app --reload
   ```

2. **Start the frontend**:

   ```bash
   cd frontend
   npm run dev
   ```

3. Open your browser at `http://localhost:3000` and enter a topic to begin.

---

## Component Breakdown

### Orchestration (LangGraph)

- **StateGraph setup** in `src/core/orchestrator.py`.
- **Checkpointing** via `AsyncSqliteSaver`.
- **Edge policies** enforce confidence thresholds and retry loops.

### Retrieval & Citation

- **SearchClient** abstraction in `src/agents/researcher_web.py` supporting Perplexity and Tavily
- Citation objects stored in `state.citations` table.
- Filtering by domain allowlist and SPDX license checks.

### Content Synthesis

- **OpenAIFunctionCaller** utilizes function-call pattern for outline JSON.
- Schema enforcement in `schemas/outline.json`.
- Token streaming via LangGraph `stream(messages)`.

### Quality Control

- **PedagogyCritic** outputs a `CritiqueReport` object with Bloom coverage.
- **FactChecker** flags lines using Cleanlab probabilities and regex rules.
- Integration tests in `tests/quality/`.

### Persistence & Versioning

- SQLite schema managed in `src/persistence/`.
- Parquet blobs for document versions.
- Optional Postgres: swap `storage/sqlite.py` with `storage/postgres.py`.

### Frontend UX

- React app (`frontend/src/`): Panels for Document, Log, Sources.
- SSE client in `frontend/src/services/stream.ts`.
- Diff highlighting via `diff-match-patch`.

### Exporters

- Markdown: direct from outline JSON → Markdown converter.
- DOCX: generated via `src/export/docx_exporter.py`.
- PDF: headless WeasyPrint configured in `src/export/pdf_exporter.py`.

---

## Storage Options

- **SQLite** (default): single `workspace.db` file in `DATA_DIR`.
- **Postgres**: set `DATABASE_URL` and install `psycopg2`; update config.

### Database Migrations

Schema changes are managed with Alembic. After pulling new code, apply
migrations to your workspace database:

```bash
alembic upgrade head
```

To create a new migration after modifying models:

```bash
alembic revision --autogenerate -m "add new table"
```

The command reads `alembic.ini` and writes migration scripts to
`migrations/versions/`.

---

## Configuration & Environment Variables

| Variable             | Description                        | Default                                  |
| -------------------- | ---------------------------------- | ---------------------------------------- |
| `OPENAI_API_KEY`     | API key for OpenAI                 | (required)                               |
| `PERPLEXITY_API_KEY` | API key for Perplexity Sonar       | Required if `SEARCH_PROVIDER=perplexity` |
| `TAVILY_API_KEY`     | API key for Tavily search          | Required if `SEARCH_PROVIDER=tavily`     |
| `SEARCH_PROVIDER`    | `perplexity` or `tavily`           | `perplexity`                             |
| `LANGCHAIN_API_KEY`  | API key for LangSmith tracing      |                                          |
| `LANGCHAIN_ENDPOINT` | LangSmith API endpoint             | `https://api.smith.langchain.com`        |
| `MODEL_NAME`         | Model to use (`o4-mini` or `o3`)   | `o4-mini`                                |
| `DATA_DIR`           | Path for SQLite DB, cache, logs    | (required)                               |
| `OFFLINE_MODE`       | Run without external network calls | `false`                                  |

---

## Logging & Tracing

- **Logging:** JSON-formatted logs are emitted via Loguru. The helper
  `core.logging.get_logger(job_id, user_id)` binds contextual identifiers so
  downstream systems can correlate events.
- **Tracing:** OpenTelemetry is initialized at startup, instrumenting FastAPI
  and outbound HTTP requests. Spans propagate through all agent nodes and can
  be exported using any standard OpenTelemetry exporter.

---

## Testing & QA

- **Unit tests**: `pytest` in `tests/`
- **Integration tests**: mock LangGraph runs in CI.
- **Performance tests**: `k6` scripts in `performance/`
- **Accessibility**: Lighthouse audit configured in CI pipeline.

---

## Operational Governance

- Metrics emitted via Prometheus client in `src/metrics/`.
- Alerts: configurable thresholds for latency, error rates, unsupported-claim rate.
- Audit: verify hash chain integrity using CLI tools.

---

## Roadmap & Next Steps

Refer to [ROADMAP.md](./docs/ROADMAP.md) for sprint plans and milestones.

---

## Contributing

We welcome contributions! Please review:

- [CONTRIBUTING.md](./docs/CONTRIBUTING.md)
- [CODE_OF_CONDUCT.md](./docs/CODE_OF_CONDUCT.md)
- [ISSUE_TEMPLATE.md](./.github/ISSUE_TEMPLATE.md)
- [PULL_REQUEST_TEMPLATE.md](./.github/PULL_REQUEST_TEMPLATE.md)

---

## License

This project is licensed under the [MIT License](./LICENSE).

---

## Additional Documentation

- **DESIGN.md** — Detailed design decisions and component diagrams
- **ARCHITECTURE.md** — Data model, state graph definitions, and sequence diagrams
- **SECURITY.md** — Security posture, secrets management, and encryption options
- **TEST_PLAN.md** — Test cases, performance benchmarks, and QA checklist
- **GOVERNANCE.md** — SLOs, metrics dashboard configuration, and audit procedures
- [**CLI_REFERENCE.md**](./docs/CLI_REFERENCE.md) — Commands for running, testing, and maintenance tasks
