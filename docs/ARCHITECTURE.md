# Architecture Overview

This document provides a **comprehensive** and **explicit** description of the Lecture Builder Agent’s architecture. It details component responsibilities, interactions, data flows, interfaces, and deployment topology. All dependencies and protocols are specified.

---

## 1. High-Level Architecture

```plaintext
┌──────────────────┐        ┌─────────────────────────┐        ┌─────────────────┐
│  User Browser    │  SSE   │       FastAPI Server     │  OpenAI API │ Citation Cache  │
│ (React + Tailwind)│◀──────▶│ (LangGraph Orchestrator) │◀──────────▶│ (SQLite or PG)   │
└──────────────────┘        └─────────────────────────┘        └─────────────────┘
         │                             │                                    │
         │ HTTP Websocket / REST       │ HTTP / gRPC                        │ HTTP
         ▼                             ▼                                    ▼
┌──────────────────┐        ┌─────────────────────────┐        ┌─────────────────┐
│ Downloads API    │        │ Perplexity Search API   │        │ Local Dense     │
│ (Markdown/DOCX/PDF)│        │ (HTTP JSON)            │        │ Retrieval Index │
└──────────────────┘        └─────────────────────────┘        └─────────────────┘
```

- **FastAPI Server**: exposes REST endpoints, SSE streams, websocket connections. Hosts LangGraph orchestrator.
- **LangGraph**: coordinates multi-agent workflows as a directed graph of nodes and edges. Maintains in-memory and persisted `State` snapshots.
- **SQLite/Postgres**: checkpoint storage for graph state, citations, logs, and document versions.
- **Perplexity Search API**: external source for research; fallback to local dense retrieval index.
- **Downloads API**: on-demand generation of final outputs in Markdown, DOCX, PDF.
- **Browser Client**: subscribes to SSE streams for document updates, citations, and action logs.

---

## 2. Component Diagram

### 2.1 Backend Components

1. **API Layer (FastAPI)**
   - **Endpoints**:
     - `POST /run` — start new lecture build job
     - `GET /resume/{job_id}` — resume after crash
     - `SSE /stream/state` — state snapshots
     - `SSE /stream/actions` — action log
     - `SSE /stream/citations` — new citations
     - `GET /download/{job_id}/{format}` — retrieve final artifact

2. **LangGraph Orchestrator**
   - **Graph Definition**: `backend/graph.py`
   - **Nodes**: Planner, Researcher-Web, Content Weaver, Pedagogy Critic, Fact Checker, Exporter
   - **Checkpoint Saver**: `SqliteCheckpointSaver` or `PostgresCheckpointSaver`
   - **Edge Policies**: confidence thresholds, retry loops

3. **Retrieval Layer**
   - **PerplexitySearchClient**: HTTP JSON wrapper with rate limiting
   - **Cache Manager**: reads/writes to `retrieval_cache` table
   - **Dense Retriever**: optional fallback using `faiss` index of CC-BY abstracts

4. **Synthesis Layer**
   - **OpenAIClient**: wraps function-call chat completions with streaming
   - **Schema Validator**: enforces `schemas/outline.json`
   - **Stream Manager**: channels LangGraph streams to HTTP SSE

5. **Quality Control**
   - **PedagogyCritic**: Bloom taxonomy coverage algorithm
   - **FactChecker**: Cleanlab integration and regex rules
   - **Report Manager**: writes to `critique_report` and `factcheck_report`

6. **Export Layer**
   - **MarkdownRenderer**: Jinja templates
   - **DocxRenderer**: `python-docx` templates
   - **PdfRenderer**: WeasyPrint with MathJax pre-render
   - **Signer**: optional GPG signing of ZIP manifest

7. **Storage Layer**
   - **SQLite / Postgres**: `state_snapshots`, `citations`, `action_log`, `documents`, `critique_report`, `factcheck_report`
   - **Parquet Storage**: binary blobs for document versions

8. **Metrics & Monitoring**
   - **Prometheus Client**: instrumented in backend
   - **Health Check Endpoint**: `GET /healthz`

### 2.2 Frontend Components

- **React App**: `web/src`
  - **DocumentPanel**: token-level Markdown renderer with diff highlights
  - **LogPanel**: chronological action entries with filters
  - **SourcesPanel**: citation list and snippet previews
  - **QualityTab**: gauge charts for pedagogy and fact-check scores
  - **Controls**: run, pause, retry, model selector, export dropdown

- **SSE Client**: `web/src/services/stream.ts` subscribes and dispatches to Redux or Zustand store
- **Download Buttons**: trigger GET requests to `/download/...`

---

## 3. Data Flow Sequences

### 3.1 Initial Job Execution

1. **User submits topic** via `POST /run`.
2. **FastAPI** enqueues job and returns `job_id`.
3. **LangGraph.invoke(job_id)** triggers:
   - **Planner** generates `learning_objectives`, `modules` → `stream(values)`.
   - **Researcher-Web** fans out N parallel queries to Perplexity API → `stream(updates)`.
   - **Content Weaver** streams token messages → `stream(messages)`.
   - **Critics** emit `stream(debug)` warnings.

4. **Frontend** receives SSE streams, updates panels in real time.
5. **Exporter** writes final files and signals completion.
6. **Browser** enables download buttons.

### 3.2 Resume After Crash

1. **User calls** `GET /resume/{job_id}`.
2. **FastAPI** reloads latest checkpoint (`SqliteCheckpointSaver`) and re-invokes remaining agents.
3. **SSE** streams catch up from last `state_version`.

### 3.3 Citation Cache Hit/Miss

1. **Researcher-Web** checks `retrieval_cache` table for query key.
2. If **hit**, returns cached response, marks `retrieval_cache.hit_count++`.
3. If **miss**, calls Perplexity API, writes response to cache & timestamp.
4. **Citation objects** created and written to `citations` table.

---

## 4. Deployment Topology

```plaintext
              ┌─────────────────────────┐
              │ Kubernetes Cluster      │
              │ ┌─────────────┐         │
              │ │Ingress NGINX│◀────────▶│
              │ └─────────────┘         │
              │     ▼                   │
              │ ┌─────────┐ ┌─────────┐ │
              │ │Backend  │ │Frontend │ │
              │ │(FastAPI)│ │(Vite)   │ │
              │ └─────────┘ └─────────┘ │
              │     │                   │
              │     ▼                   │
              │ ┌─────────┐             │
              │ │Postgres │             │
              │ └─────────┘             │
              │     │                   │
              │     ▼                   │
              │ ┌─────────┐             │
              │ │Prometheus│            │
              │ └─────────┘             │
              └─────────────────────────┘
```

- **Ingress** routes `/api/*` to FastAPI, `/` to frontend.
- **Backend** pods scale based on CPU and SSE connections.
- **Postgres** single Primary + Read Replicas for heavy load.
- **Prometheus** scrapes metrics; **Grafana** dashboards visualize performance.

---

## 5. Interfaces and Protocols

| Interface             | Protocol                               | Format         | Direction           |
| --------------------- | -------------------------------------- | -------------- | ------------------- |
| `/run`, `/resume`     | HTTP REST                              | JSON           | Client → Server     |
| SSE Streams           | SSE                                    | JSON messages  | Server → Client     |
| `/download`           | HTTP REST                              | Binary stream  | Client ← Server     |
| LangGraph invocations | In-process Call                        | Python objects | Orchestrator        |
| Perplexity API        | HTTP REST                              | JSON           | Server → Perplexity |
| OpenAI API            | HTTP REST                              | JSON           | Server → OpenAI     |
| DB Access             | SQL over TCP (PG) or File I/O (SQLite) | SQL            | Server ↔ DB        |

---

## 6. Security and Compliance

- **Authentication**: JWT tokens for API endpoints.
- **Authorization**: RBAC enforced in FastAPI middleware.
- **Transport Security**: TLS for all HTTP and SSE traffic.
- **Secrets**: Managed by HashiCorp Vault; mounted as env vars.
- **Data Encryption**: SQLCipher for SQLite; TLS to Postgres.
- **Audit Logging**: Immutable `action_log` with SHA-256 chain.

---

## 7. Observability

- **Metrics**: Prometheus counters and histograms for request latency, model-call durations, SSE throughput.
- **Logging**: Structured JSON logs via `loguru` with correlation IDs.
- **Tracing**: OpenTelemetry instrumentation for function calls and external HTTP requests.
- **Health Checks**: `GET /healthz` returns 200 if DB and cache are reachable.

---

## 8. Scalability Considerations

- **Backend Scaling**: Stateless nodes; horizontal scaling behind load balancer.
- **LangGraph**: supports sharding of job queues by `job_id`.
- **Database**: scale Postgres with read replicas; use connection pooling.
- **Cache**: Memcached or Redis can replace SQLite cache for high throughput.
- **SSE**: use sticky sessions or Distributed Pub/Sub (e.g. Redis Streams) for multi-pod streaming.

---

## 9. Glossary of Terms

- **SSE**: Server-Sent Events, unidirectional streaming over HTTP.
- **LangGraph**: Graph-based orchestration framework for agent workflows.
- **State**: Typed object representing the current job snapshot.
- **Module**: A lecture segment with duration and activities.
- **OutlineSchema**: JSON schema dictating lecture content structure.
- **Citation**: Metadata bundle for source attribution.
- **PedagogyCritic**: Agent enforcing educational best practices.
- **FactChecker**: Agent ensuring factual accuracy.

---

For detailed sequence diagrams, ER models, and component diagrams, see **ARCHITECTURE_DIAGRAMS/** directory:

- `erd.png` — Entity-Relationship Diagram
- `sequence_build.png` — Build Flow Sequence Diagram
- `component_overview.png` — Component Interaction Diagram

This architecture fully specifies every interface, component, and interaction necessary to implement, deploy, and maintain the Lecture Builder Agent in production-quality scenarios.
