# Implementation Plan

## A. Environment & Scaffolding

1. **Git & Poetry Setup**
   1.1. Initialize Git repo with `git init` and create a `.gitignore` for Python/Poetry artifacts.
   1.2. Create `pyproject.toml` via `poetry init` specifying Python ≥3.11.
   1.3. Add basic `pre-commit` configuration to run `black`, `isort`, `flake8`.
   1.4. Commit an initial skeleton (`README.md`, `src/`, `tests/`, `.env.example`).

2. **.env & Config Loader**
   2.1. Add `python-dotenv` as a dependency.
   2.2. Create `src/config.py` with a `Settings` Pydantic model reading `OPENAI_API_KEY`, `PERPLEXITY_API_KEY`, `MODEL_NAME`, `DATA_DIR`, `OFFLINE_MODE`.
   2.3. Write a unit test verifying all settings default correctly when env vars are missing or present.

3. **Folder Structure & CI Stub**
   3.1. Create directories:

   ```
   src/
     core/
     agents/
     persistence/
     web/
     export/
   tests/
   workspace/
   docs/
   ```

   3.2. Add GitHub Actions workflow `ci.yml` that installs Poetry, runs `poetry install`, `poetry run pytest --maxfail=1 --disable-warnings -q`.

---

## B. Orchestration Core (LangGraph StateGraph)

1. **State Dataclass & Types**
   1.1. In `src/core/state.py`, define a Pydantic/`@dataclass` `State` with fields:

   ```python
   prompt: str
   sources: List[Citation]
   outline: Optional[Outline]  # schema-defined
   log: List[ActionLog]
   version: int
   ```

   1.2. Write unit tests checking JSON serialization & default values.

2. **LangGraph Instantiation**
   2.1. In `src/core/orchestrator.py`, import `StateGraph` from LangGraph.
   2.2. Define each node stub as a Python async function:

   ```python
   async def planner(state: State) -> PlanResult: …
   async def researcher_web(state: State) -> List[CitationResult]: …
   # etc.
   ```

   2.3. Declare the graph edges and streaming channels:

   ```python
   graph = StateGraph(State)
   graph.add_node(planner, name="Planner", streams="values")
   graph.add_node(researcher_web, name="Researcher", streams="updates")
   # …
   graph.add_edge("Planner", "Researcher", policy=…)
   ```

3. **Edge Policies & Loop Logic Implementation**
   3.1. Write code for Planner→Researcher loop: if `plan.confidence < 0.9`, re-invoke Researcher.
   3.2. For Critic nodes, wrap outputs in a retry decorator with `max_retries=3`.
   3.3. Implement Researcher fan-out: spawn N web calls in parallel (e.g. via `asyncio.gather`), then dedupe by URL similarity.

4. **Checkpoint Saver Integration**
   4.1. Add `pip install langgraph-checkpoint-sqlite` to dependencies.
   4.2. In `orchestrator.py`, configure

   ```python
   from langgraph_checkpoint_sqlite import SqliteCheckpointSaver
   saver = SqliteCheckpointSaver(path=f"{DATA_DIR}/checkpoint.db")
   graph.set_checkpoint_saver(saver)
   ```

   4.3. Write an integration test: start graph, kill after first node, resume with `graph.invoke(resume=True)`, assert state is restored.

---

## C. Retrieval & Citation Layer

1. **Perplexity API Client**
   1.1. In `src/agents/researcher_web.py`, implement `PerplexityClient` with methods `search(query: str) -> List[SearchResult]`.
   1.2. Add fallback: if `OFFLINE_MODE`, load `workspace/cache/{query}.json`.
   1.3. Write unit tests mocking both online and offline branches.

2. **Citation Model & Storage**
   2.1. Define `Citation` Pydantic model in `src/persistence/models.py`:

   ```python
   url: HttpUrl
   title: str
   retrieved_at: datetime
   licence: str
   ```

   2.2. Create SQLite table `citations` via Alembic migration file: fields matching the model.
   2.3. Implement `CitationRepo.insert(citation: Citation)` and `get_by_url(url)` with `aiosqlite`.

3. **Authority Ranking & Filtering**
   3.1. After collecting results, score each URL by domain authority (e.g. simple domain allowlist lookup).
   3.2. Filter out non-CC/government/uni domains. Log filtered URLs for audit.
   3.3. Unit-test ranking logic with sample URL list.

---

## D. Content Synthesis

1. **JSON Schema for Lecture**
   1.1. Write `lecture_schema.json` specifying required fields:

   ```json
   {
     "type":"object",
     "properties": {
       "learning_objectives": { "type":"array", "items": { "type":"string" } },
       …
     },
     "required": ["learning_objectives","activities","duration_min"]
   }
   ```

   1.2. Hook up `jsonschema` validator in `src/agents/content_weaver.py`.

2. **Content Weaver Agent**
   2.1. Implement `async def content_weaver(state: State) -> WeaveResult:` that:

   * Calls OpenAI via function-calling API, passing system + user prompts and schema.
   * Streams partial tokens back via LangGraph’s `.stream("messages")`.
     2.2. On completion, parse function output into Python model and validate against schema.
     2.3. Write unit tests mocking OpenAI responses (correct and schema-violating).

3. **Markdown Renderer**
   3.1. In `src/export/markdown.py`, write a converter:

   ```python
   def from_schema(weave: WeaveResult) -> str:
       # build markdown sections: ## Objectives, ### Activity
       …
   ```

   3.2. Unit-test that given a sample WeaveResult, the markdown includes proper headings, bullet lists, and footnote placeholders for citations.

---

## E. Quality Control

1. **Pedagogy Critic Agent**
   1.1. In `src/agents/pedagogy_critic.py`, implement bloom-coverage check:

   * Map each objective/activity to Bloom levels; ensure all six domains are hit.
   * Return a `CritiqueReport` listing missing levels.
     1.2. Stream report via `.stream("debug")`.
     1.3. Test with synthetic `Outline` missing certain domains.

2. **Fact Checker Agent**
   2.1. Integrate `cleanlab` to assign probability scores to each sentence.
   2.2. Run regex patterns for citations (e.g. “\[1]”) vs. “unsupported” phrases.
   2.3. Return flagged lines; stream via `.stream("debug")`.
   2.4. Test using sample text with known “unsupported claim”.

3. **Regeneration Logic**
   3.1. In orchestrator, catch Critic failures, slice out affected subsections, and re-invoke Content Weaver only on those.
   3.2. Maintain a `retry_count` in state to enforce max-3.
   3.3. Unit-test loop: simulate 3 failures and assert it stops retrying.

4. **Action Log Records**
   4.1. After each agent runs, compute `input_hash`, `output_hash`, count tokens and cost from OpenAI response.
   4.2. Insert a row into `logs(agent, input_hash, output_hash, tokens, cost, timestamp)`.
   4.3. Write a query function to retrieve logs for a given workspace and date range.

---

## F. Persistence & Versioning

1. **State & Document Tables**
   1.1. Create Alembic migrations for tables:

   * `state(id, payload_json, version, updated_at)`
   * `documents(id, state_id, parquet_blob, created_at)`
     1.2. Implement `StateRepo.save(state: State)` and `DocumentRepo.save(version_blob)`.

2. **Parquet Blobs**
   2.1. Use `pyarrow` to serialize the current `outline` object to a Parquet in-memory buffer.
   2.2. Store buffer as BLOB in SQLite.
   2.3. Test: round-trip read-back yields identical schema and content.

3. **Resume Testing**
   3.1. End-to-end test: drive graph through Plan→Research, kill process mid-synthesis, restart with `resume=True`, confirm markdown exporter still produces the same outline.

---

## G. Exporters

1. **Markdown Export API**
   1.1. Implement FastAPI route `GET /export/{workspace}/md` that:

   * Loads latest `outline` from DB.
   * Calls `from_schema()` to produce markdown.
   * Returns as `text/markdown` with `Content-Disposition`.

2. **DOCX Generation**
   2.1. In `src/export/docx.py`, load a `template.docx` with placeholder fields.
   2.2. Use `python-docx` to fill in: title, TOC, each section, bibliography as footer.
   2.3. Expose `GET /export/{workspace}/docx` in FastAPI.

3. **PDF via WeasyPrint**
   3.1. Convert markdown → HTML via `markdown` lib + custom CSS.
   3.2. Call `weasyprint.HTML(string=html).write_pdf()`.
   3.3. Expose `GET /export/{workspace}/pdf`.

4. **Metadata & Citations JSON**
   4.1. Bundle `citations.json` alongside each export.
   4.2. Zip all formats in `GET /export/{workspace}/all` endpoint.

---

## H. Browser-Based UX

1. **SSE Backend**
   1.1. Create `/stream/{workspace}` SSE endpoint in FastAPI, hooking into `graph.astream()`.
   1.2. Serialize each event with fields `{type, payload, timestamp}`.
   1.3. Write unit tests using `httpx` to open SSE and assert sequence of events.

2. **React App Scaffolding**
   2.1. `npx create-react-app` (or Vite) with TypeScript.
   2.2. Install `tailwindcss`, set up `tailwind.config.js`.
   2.3. Stub components: `DocumentPanel`, `LogPanel`, `SourcesPanel`, `Controls`, `Downloads`.

3. **Diff Highlighting & Typewriter**
   3.1. In `DocumentPanel`, on each SSE “values” or “messages”, compute diff from prior text (use `diff-match-patch`).
   3.2. Animate insertions token-by-token; highlight changed words for 2 seconds.
   3.3. Unit-test diff algorithm against sample before/after strings.

4. **Citation Popover**
   4.1. Render footnote markers; on click fetch full citation metadata via `GET /citations/{id}`.
   4.2. Show modal with `url`, `title`, `retrieved_at`, `licence`.
   4.3. Integration-test with React Testing Library.

5. **Controls & Model Selector**
   5.1. “Run” button hits `POST /run/{workspace}`, disabling while running.
   5.2. “Pause” sends `POST /pause`; “Retry” calls `POST /retry`.
   5.3. Dropdown to choose `o4-mini` or `o3`, bound to `Settings.MODEL_NAME`.

6. **Downloads Panel**
   6.1. Poll `GET /export/{workspace}/status` until ready, then display links for Markdown, DOCX, PDF, ZIP.
   6.2. Show progress bar for each format.

---

## I. Deployment & Offline Mode

1. **FastAPI App Entrypoint**
   1.1. Create `main.py` initializing Config, DB, Graph, and mounting React build under `/`.
   1.2. Add CLI flag `--offline` to toggle search and fact-check behavior.

2. **Dockerfile & Compose**
   2.1. Write `Dockerfile` installing system deps for WeasyPrint, copying app, running `uvicorn main:app`.
   2.2. Draft `docker-compose.yml` mounting `./workspace` and passing env vars.

3. **Local Dev Script**
   3.1. `scripts/run.sh` to spin up Docker or local Uvicorn with `poetry run`.
   3.2. `scripts/reset_db.sh` to drop and re-create SQLite schema.

---

## J. QA, Metrics & Governance

1. **Metrics Collector**
   1.1. In each agent wrapper, record metrics:

   ```python
   metrics.record("tokens", count); metrics.record("cost", cost)
   ```

   1.2. Expose `/metrics` endpoint in Prometheus format.

2. **Threshold Alerts**
   2.1. After each lecture completes, evaluate metrics against targets ≥90% pedagogical, ≤2% hallucination.
   2.2. If breach, `POST` to a configurable webhook URL.

3. **RBAC Middleware**
   3.1. Implement FastAPI dependency checking JWT claims for `role` ∈ {viewer, editor, admin}.
   3.2. Protect routes accordingly (`export` open to viewer+, `run` to editor+, admin for governance endpoints).

4. **Audit Trail Verification**
   4.1. Create endpoint `/audit/{workspace}` that lists SHA-256 hashes of each saved state.
   4.2. Offer a “compare” utility in CLI to diff two states by hash.

---
