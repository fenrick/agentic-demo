# Implementation Plan

## A. Environment & Scaffolding

---

## A1. Git & Project Initialisation

1. **`README.md`**

- **Purpose**: Project overview, setup instructions, directory layout.
- **Sections to include**:
  - **Introduction**: “What this lecture-builder does.”
  - **Quickstart**: CLI commands to install and run.
  - **Architecture overview**: high-level bullet points.

1. **`.gitignore`**

- **Purpose**: Exclude Python build artefacts, virtual environments, workspace data.
- **Entries**:
  - `__pycache__/`
  - `.env`
  - `workspace/*`
  - `*.pyc`, `poetry.lock`, `.venv/`

1. **`pyproject.toml`**

- **Purpose**: Define project metadata, Python version, and dependencies stub.
- **Sections**:
  - `[tool.poetry]`: `name`, `version`, `description`, `authors`.
  - `[tool.poetry.dependencies]`: placeholder entries for `python>=3.11`, `pydantic-ai`, `openai`, etc.
  - `[tool.poetry.dev-dependencies]`: `pytest`, `black`, `flake8`, `isort`, `pre-commit`.

1. **`.pre-commit-config.yaml`**

- **Purpose**: Enforce code style on each commit.
- **Hooks**:
  - `black` (formatting),
  - `isort` (imports),
  - `flake8` (linting).

1. **Initial Commit**

- Run `git init` and commit:
  1. `README.md`
  2. `.gitignore`
  3. `pyproject.toml` (empty dependencies)
  4. `.pre-commit-config.yaml`

---

## A2. Environment Variables & Config Loader

1. **`.env.example`**

- **Purpose**: Template for required environment variables.
- **Variables listed**:
  - `OPENAI_API_KEY`
  - `PERPLEXITY_API_KEY`
  - `TAVILY_API_KEY` (optional)
  - `SEARCH_PROVIDER` (default: `perplexity`)
  - `LOGFIRE_API_KEY` (optional)
  - `LOGFIRE_PROJECT` (optional)
  - `MODEL` (default: `openai:o4-mini`)
  - `DATA_DIR` (default: `./workspace`)
  - `OFFLINE_MODE` (default: `false`)
  - `ENABLE_TRACING` (default: `true`)
  - `ALLOWLIST_DOMAINS` (JSON list, default: `["wikipedia.org", ".edu", ".gov"]`)
  - `ALERT_WEBHOOK_URL` (optional)

1. **`src/config.py`**

- **Class**: `Settings`
  - Subclass of `pydantic_settings.BaseSettings` with typed fields.
  - Automatically loads environment variables (and `.env` if present).
  - Validators normalize `data_dir` paths and parse `ALLOWLIST_DOMAINS` JSON.
- **Function**: `load_env(env_file: Path)`
  - Loads variables from a given file and returns `Settings`.
- **Function**: `load_settings()`
  - Returns a cached `Settings` instance for reuse across modules.

1. **`tests/test_config.py`**

- Covers loading from environment variables and `.env` files.
- Asserts default fallbacks for `data_dir` and `allowlist_domains`.
- Validates custom allowlist JSON and error handling.

---

## A3. Folder Structure & CI Pipeline Stub

1. **Directory Layout**

```bash
project-root/
├── src/
│ ├── core/ # State & orchestrator stubs
│ ├── agents/ # Agent function stubs
│ ├── persistence/ # DB models & repos
│ ├── web/ # FastAPI endpoint stubs
│ └── export/ # Exporter stubs
├── tests/ # Unit & integration tests
├── workspace/ # Local SQLite + cached data
├── docs/ # Design docs, API specs
├── .github/
│ └── workflows/
│ └── ci.yml # CI stub
├── .env.example
├── pyproject.toml
├── README.md
└── .pre-commit-config.yaml
```

1. **`ci.yml` (GitHub Actions)**

- **Job**: `build-and-test`
  - **Runs-on**: `ubuntu-latest`
  - **Steps**:
  1. **Checkout code** (`actions/checkout@v3`)
  2. **Setup Python** (`actions/setup-python@v4`) with version `3.11`
  3. **Install Poetry**
  4. **Cache** Poetry cache & `.venv`
  5. **Install dependencies** (`poetry install --no-interaction --no-ansi`)
  6. **Run linters** (`poetry run pre-commit run --all-files`)
  7. **Run tests** (`poetry run pytest --maxfail=1 --disable-warnings -q`)

1. **Local Test & Lint Scripts**

- **File**: `scripts/run_checks.sh`
  - **Invokes**: `poetry run pre-commit run --all-files` then `poetry run pytest`.

- **File**: `scripts/reset_workspace.sh`
  - **Deletes**: `${DATA_DIR}/*.db` and `${DATA_DIR}/cache/*` to start fresh.

---

## B. Orchestration Core (Custom Engine)

---

### B.1 State Model & Utilities

**File:** `src/core/state.py`

- **Class `State`**

- Holds all graph-wide data:
  - `prompt: str`
  - `sources: List[Citation]`
  - `outline: Optional[Outline]`
  - `log: List[ActionLog]`
  - `version: int`

- **Method `to_dict()`**
  - Serialise the current state into a plain dict for persistence.

- **Method `from_dict(raw: dict)`** (class method)
  - Rehydrate a `State` instance from a dict loaded from the database.

- **Function `increment_version(state: State)`**

- Bump the `version` counter whenever a mutation is saved.

- **Function `validate_state(state: State)`**

- Quick sanity check (e.g. prompt exists, version non-negative) before running the graph.

---

### B.2 Node Definitions & Registration

**Directory:** `src/core/nodes/`
Each node module defines a single `async` handler function and its input/output contract.

1. **Planner**

- **File:** `planner.py`
- **Function `run_planner(state: State) → PlanResult`**
  - Analyse `state.prompt`, produce learning goals, estimated confidence score.

- **Researcher-Web**

- **File:** `researcher_web.py`
- **Function `run_researcher_web(state: State) → List[CitationResult]`**
  - Fire off web searches and return ranked snippets + metadata.

- **Content Weaver**

- **File:** `content_weaver.py`
- **Function `run_content_weaver(state: State) → WeaveResult`**
  - Call LLM, apply JSON schema, stream back draft outline tokens.

- **Pedagogy Critic & Fact Checker**

- **File:** `critics.py`
- **Function `run_pedagogy_critic(state: State) → CritiqueReport`**
- **Function `run_fact_checker(state: State) → FactCheckReport`**
  - Validate pedagogy coverage and flag hallucinations.

- **Human-in-Loop Approver**

- **File:** `approver.py`
- **Function `run_approver(state: State) → StateEdits`**
  - Expose editable deltas; await user acceptance.

- **Exporter**

- **File:** `exporter.py`
- **Function `run_exporter(state: State) → ExportStatus`**
  - Trigger Markdown/DOCX/PDF renders and report completion.

#### Core Orchestrator

- **File:** `src/core/orchestrator.py`
- **Class `GraphOrchestrator`**
  - `run(state: State) -> State` — execute the pipeline for a given state.
  - `stream(state: State)` — yield progress events for each executed node.

---

### B.3 Edge Policies & Loop Logic

**File:** `src/core/policies.py`

- **Function `policy_retry_on_low_confidence(prev: PlanResult) → Literal["loop", "continue"]`**

- Returns `"loop"` if Planner’s confidence \< threshold and retries remain; otherwise `"continue"` to proceed to the Content Weaver.

- **Function `policy_retry_on_critic_failure(report: CritiqueReport|FactCheckReport) → bool`**

- Returns `true` when critics flag issues, to selectively re-invoke Content Weaver.

- **Function `merge_research_results(results: List[CitationResult]) → List[Citation]`**

- Semantic deduplication and authority ranking of parallel Researcher-Web outputs.

- **Function `retry_tracker(state: State, agent_name: str) → int`**

- Inspect state‐embedded counters to enforce “max 3 retries” for any given node.

---

### B.4 Checkpointing & Persistence Integration

**File:** `src/core/checkpoint.py`

- **Class `SqliteCheckpointManager`**

- **Constructor `(db_path: str)`**
  - Points to the SQLite file for snapshots.

- **Method `save_checkpoint(state: State)`**
  - Serialises `state.to_dict()` into a checkpoint table.

- **Method `load_checkpoint() → State`**
  - Reads the latest snapshot and returns a reconstructed `State`.

- **In `orchestrator.py`**, wiring:

- Instantiate an `AsyncSqliteSaver` with `DATA_DIR`.
- Execute the compiled graph via `graph.ainvoke(..., config={"checkpoint": saver, "resume": True})` so each node snapshot is persisted and runs can resume from any step.

---

## Step C: Retrieval & Citation Layer

---

### C.1 Perplexity Sonar Client & Offline Fallback

#### 1. `src/agents/researcher_web.py`

- **Class `PerplexityClient`**

- **`search(self, query: str) → List[RawSearchResult]`**
  Uses Pydantic‑AI to call the Perplexity Sonar model and return cited snippets + URLs.
- **`fallback_search(self, query: str) → List[RawSearchResult]`**
  Invoked when `OFFLINE_MODE` is true; loads from cache instead of HTTP.

- **Class `RawSearchResult`** (data container)

- Fields: `url: str`, `snippet: str`, `title: str`

#### 2. `src/agents/offline_cache.py`

- **`load_cached_results(query: str) → Optional[List[RawSearchResult]]`**
  Reads `${DATA_DIR}/cache/{sanitized_query}.json` if present.
- **`save_cached_results(query: str, results: List[RawSearchResult])`**
  Persists fresh API responses for offline reuse.

#### 3. `src/agents/researcher_web_runner.py`

- **`run_web_search(state: State) → List[CitationDraft]`**
  Coordinates:

1. Calls `PerplexityClient.search` or `.fallback_search`
1. Wraps each `RawSearchResult` in a preliminary `CitationDraft` (url + snippet + title)

---

### C.2 Citation Model & Persistence

#### 1. Data Model

##### `src/persistence/models.py`

- **Class `Citation`**

- `url: HttpUrl`
- `title: str`
- `retrieved_at: datetime`
- `licence: str`

#### 2. Database Schema

##### `migrations/versions/20250805_create_citations_action_logs_metrics_tables.py`

- Alembic migration to create table `citations` with columns matching `Citation` fields plus a workspace identifier.

#### 3. Repository Layer

##### `src/persistence/repositories/citation_repo.py`

- **Class `CitationRepo`**

- **`insert(self, citation: Citation) → None`**
  Upserts the citation record into SQLite.
- **`get_by_url(self, url: str) → Optional[Citation]`**
  Fetches an existing citation by URL (to avoid duplicates).
- **`list_by_workspace(self, workspace_id: str) → List[Citation]`**
  Returns all citations tied to a given lecture-builder workspace.

#### 4. Database Connector

##### `src/persistence/database.py`

- **`get_db_session() → AsyncGenerator[Connection, None]`**
  Yields an `aiosqlite` connection configured to the workspace database.

---

### C.3 Authority Ranking & Copyright Filtering

#### 1. Authority Scoring

##### `src/agents/researcher_web.py` (continued)

- **`rank_by_authority(results: List[CitationDraft]) → List[CitationDraft]`**
  Assigns each draft a score based on domain reputation, sorts descending.
- **`score_domain_authority(domain: str) → float`**
  Returns a heuristic score (e.g. government/university domains → high, blogs → low).

#### 2. Allowlist Filtering

##### `src/agents/copyright_filter.py`

- **`filter_allowlist(results: List[CitationDraft]) → (kept: List[CitationDraft], dropped: List[CitationDraft])`**
  Splits drafts into those whose domain appears in the configured allowlist (Creative Commons, `.edu`, `.gov`, etc.) and those to discard.
- **Config `ALLOWLIST_DOMAINS`** (in `src/config.py`)
  A list of trusted domain patterns.

#### 3. Pipeline Orchestration

##### `src/agents/researcher_pipeline.py`

- **`researcher_pipeline(query: str, state: State) → List[Citation]`**

1. Call `PerplexityClient.search` (or fallback).
1. Wrap into `CitationDraft`.
1. Apply `rank_by_authority`.
1. Apply `filter_allowlist`.
1. For each remaining draft:

- Enrich with `retrieved_at = now()`, lookup `licence` via simple HTTP HEAD if needed.
- Instantiate a `Citation` model.
- Persist via `CitationRepo.insert`.

1. Return the final `List[Citation]` for the orchestrator to merge into state.

---

#### Hand-Off to the Orchestrator

Once `researcher_pipeline` returns `List[Citation]`, the orchestrator will:

- Merge them into `state.sources`.
- Emit an `updates` event so the UI can show new citations in real time.

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

1. **Content Weaver Agent**
   2.1. Implement `async def content_weaver(state: State) -> WeaveResult:` that:

- Calls OpenAI via function-calling API, passing system + user prompts and schema.
- Streams partial tokens back via the orchestrator's `messages` channel.
  2.2. On completion, parse function output into Python model and validate against schema.
  2.3. Write unit tests mocking OpenAI responses (correct and schema-violating).

1. **Markdown Renderer**
   3.1. In `src/export/markdown.py`, write a converter:

```python
def from_schema(weave: WeaveResult) -> str:
 # build markdown sections: ## Objectives, ### Activity
 …
```

3.2. Unit-test that given a sample WeaveResult, the markdown includes proper headings, bullet lists, and footnote placeholders for citations.

---

## E. Quality Control

---

### E.1 Pedagogy Critic Agent

**File:** `src/agents/pedagogy_critic.py`
**Purpose:** Analyse the draft outline against a pedagogical rubric (Bloom’s taxonomy, activity variety, cognitive load).

- **`run_pedagogy_critic(state: State) → CritiqueReport`**
  • Orchestrator entry point.
  • Takes the current `state.outline` and returns a `CritiqueReport` summarising gaps and recommendations.

- **`analyze_bloom_coverage(outline: Outline) → BloomCoverageReport`**
  • Maps each learning objective and activity to one of Bloom’s six levels.
  • Flags any missing levels and computes a coverage score.

- **`evaluate_activity_diversity(outline: Outline) → ActivityDiversityReport`**
  • Checks for mix of lectures, discussions, exercises, assessments.
  • Ensures no single type exceeds a configured max-percentage (e.g. \<50% lecture).

- **`assess_cognitive_load(outline: Outline) → CognitiveLoadReport`**
  • Estimates total estimated time and complexity per segment.
  • Warns if any block exceeds recommended duration or density.

**Models:**

- `src/models/critique_report.py` defines `CritiqueReport`, `BloomCoverageReport`, etc.
- Tests in `tests/agents/test_pedagogy_critic.py` should supply various outlines and assert correct reports.

---

### E.2 Fact Checker Agent

**File:** `src/agents/fact_checker.py`
**Purpose:** Detect hallucinations and unsupported claims in generated text.

- **`run_fact_checker(state: State) → FactCheckReport`**
  • Entry point called after synthesis.
  • Scans `state.outline.markdown` (and speaker notes).

- **`assess_hallucination_probabilities(text: str) → List[SentenceProbability]`**
  • Uses Cleanlab or similar to assign each sentence a “confidence” score.
  • Returns sentences below a threshold.

- **`scan_unsupported_claims(text: str) → List[ClaimFlag]`**
  • Regex-based detection for un-cited assertions (e.g. “studies show…” without a footnote).
  • Flags line numbers and snippets.

- **`compile_fact_check_report(hallucinations, flags) → FactCheckReport`**
  • Aggregates both checks into a single report, with counts and detailed entries.

**Models:**

- `src/models/fact_check_report.py` defines `FactCheckReport`, `SentenceProbability`, `ClaimFlag`.
- Tests in `tests/agents/test_fact_checker.py` should cover both high-confidence and low-confidence cases, plus unsupported‐claim patterns.

---

### E.3 Regeneration Logic

**File:** `src/core/regenerator.py`
**Purpose:** Apply critic feedback to selectively re-invoke the Content Weaver for problematic sections.

- **`orchestrate_regeneration(state: State, report: CritiqueReport|FactCheckReport) → State`**
  • Examines the incoming report to decide which outline sections need rewriting.
  • Updates `state.retry_counts[section_id]`.

- **`get_sections_to_regenerate(report) → List[SectionIdentifier]`**
  • Extracts the IDs or indices of outline paragraphs/activities that failed checks.

- **`increment_retry_count(state: State, section_id: SectionIdentifier) → None`**
  • Increments a counter in `state.metadata` so we can enforce a max-3 retry policy.

- **`has_exceeded_max_retries(state: State, section_id: SectionIdentifier) → bool`**
  • Compares `retry_counts` to the configured limit (3) and returns true if no further retries are allowed.

- **`apply_regeneration(graph: StateGraph, state: State, sections: List[SectionIdentifier])`**
  • Triggers the `ContentWeaver` node only on the identified sections, leaving the rest untouched.

**Tests:**

- `tests/core/test_regeneration.py` should simulate critic reports with varying numbers of failures and verify that:

1. Only the flagged sections are re-sent to the weaver
1. Retry counts increment properly
1. The loop halts after three attempts

---

### E.4 Action Log Records

**File:** `src/persistence/logs.py`
**Purpose:** Capture a structured audit trail of every agent invocation.

- **`log_action(agent_name: str, input_hash: str, output_hash: str, tokens: int, cost: float, timestamp: datetime) → None`**
  • Writes a row into the `logs` table in SQLite.
  • Ensures immutability by never updating existing records.

- **`get_logs(workspace_id: str, date_from: date, date_to: date) → List[ActionLog]`**
  • Query interface for the UI or governance scripts to fetch logs for a time range.

- **`compute_hash(payload: Any) → str`**
  • Utility used by all agents to derive consistent SHA-256 hashes of inputs and outputs.

**Models:**

- `src/models/action_log.py` defines the `ActionLog` record structure.
- Tests in `tests/persistence/test_logs.py` should verify that calls to `log_action` correctly persist and that `get_logs` returns the expected slice.

---

## F. Persistence & Versioning

---

### F.1 Database Schema & Migrations

1. **Alembic Setup**

- **File:** `migrations/env.py`
  _Bootstraps Alembic with your project’s SQLAlchemy (or `aiosqlite`) settings._
- **File:** `alembic.ini`
  _Points Alembic at your SQLite file (`DATA_DIR/workspace.db`)._

1. **Create State Table Migration**

- **File:** `migrations/versions/20250804_create_state_table.py`
  - Defines a `state` table with columns:

  - `id` (primary key)
  - `payload_json` (TEXT)
  - `version` (INTEGER)
  - `updated_at` (TIMESTAMP)

1. **Create Documents Table Migration**

- **File:** `migrations/versions/20250804_create_documents_table.py`
  - Defines a `documents` table with columns:

  - `id` (primary key)
  - `state_id` (foreign key → `state.id`)
  - `parquet_blob` (BLOB)
  - `created_at` (TIMESTAMP)

1. **Alembic Revision Commands**

- Run `alembic revision --autogenerate -m "create state & documents tables"`
- Then `alembic upgrade head` to apply.

---

### F.2 Repository Layer & APIs

1. **StateRepo**

- **File:** `src/persistence/repos/state_repo.py`
- **Class:** `StateRepo`
  - `save_state(state: State) -> int`
    _Serialises the `State` object to JSON, inserts or updates a row in `state`, and returns its `id`._
  - `get_latest_state() -> State`
    _Fetches the row with the highest `version`, deserialises JSON back into a `State` instance._
  - `get_state_by_version(version: int) -> State`
    _Loads a specific version for audit or rollback._

1. **DocumentRepo**

- **File:** `src/persistence/repos/document_repo.py`
- **Class:** `DocumentRepo`
  - `save_document_version(state_id: int, blob: bytes) -> int`
    _Stores a Parquet blob for the given `state_id`; returns the new document row’s `id`._
  - `list_versions(state_id: int) -> List[DocumentMetadata]`
    _Returns metadata (id, created_at) for all blobs tied to a state._
  - `load_latest_document(state_id: int) -> bytes`
    _Fetches the most recent Parquet blob for rendering or diffing._

1. **PersistenceManager**

- **File:** `src/persistence/manager.py`
- **Class:** `PersistenceManager`
  - `checkpoint(state: State, outline: Outline) -> None`
    _Calls `StateRepo.save_state()`, serialises the `outline` via ParquetSerializer (next section), then `DocumentRepo.save_document_version()`._
  - `restore(version: Optional[int] = None) -> Tuple[State, Outline]`
    _Fetches state and matching outline blob, deserialises, and returns both objects._

---

### F.3 Parquet Versioning

1. **ParquetSerializer**

- **File:** `src/persistence/parquet_serializer.py`
- **Class:** `ParquetSerializer`
  - `serialize_outline(outline: Outline) -> bytes`
    _Converts the in-memory outline object into a Parquet-format byte string._
  - `deserialize_outline(blob: bytes) -> Outline`
    _Reads Parquet bytes back into the `Outline` data structure._

1. **Schema Validation**

- **File:** `src/persistence/parquet_schema.py`
  _Defines the Arrow schema used for every version, ensuring compatibility across reads/writes._

1. **Unit Tests**

- **File:** `tests/persistence/test_parquet_serializer.py`
  - Verify that `serialize_outline()` + `deserialize_outline()` yields an object equal to the original.
  - Test with edge cases: empty outline, large outlines.

---

### F.4 Resume & Recovery Testing

1. **Integration Test: Resume from Checkpoint**

- **File:** `tests/integration/test_resume_from_checkpoint.py`
- **Scenario:**
  1. Kick off a graph run up through the Content Weaver node.
  2. Simulate process crash (kill graph or clear in-memory state).
  3. Invoke `graph.invoke(resume=True)`.
  4. Assert that:
  - `PersistenceManager.restore()` returns the same `State` and `Outline`.
  - The Exporter can still generate valid Markdown from the restored outline.

1. **CLI Smoke Script**

- **File:** `scripts/test_resume.sh`
- **Steps:**
  1. Start FastAPI + the orchestrator with a sample prompt.
  2. Wait for “outline ready” event in logs.
  3. Kill the process.
  4. Restart with `--resume`.
  5. Poll `/export/…/md` endpoint and verify it returns non-empty Markdown.

1. **Error Injection**

- **File:** `tests/integration/test_corrupted_checkpoint.py`
- **Goal:** Ensure graceful error when the SQLite blob or Parquet is malformed.
- **Approach:**
  - Manually corrupt the BLOB in `documents`.
  - Call `restore()`, expect a well-defined exception or fallback behaviour (e.g. skip version, alert user).

---

## G. Exporters

---

### G1. Markdown Exporter

**File:** `src/export/markdown_exporter.py`
**Class:** `MarkdownExporter`

| Method                                             | Purpose                                                                                                                                                      |
| -------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `export(workspace_id: str) → str`                  | • Load latest outline, metadata, citations from SQLite. • Invoke `build_front_matter`, `render_outline`, `embed_citations`. • Return full Markdown document. |
| `build_front_matter(metadata: dict) → str`         | • Generate YAML front-matter (topic, model, commit SHA, date).• Ensures downstream tools (Pandoc) recognise metadata.                                        |
| `render_outline(outline: Outline) → str`           | • Walk the structured `Outline` model.• Emit headings (`##`, `###`) and bullet lists for objectives, activities, notes.                                      |
| `embed_citations(citations: List[Citation]) → str` | • Append footnote markers in text.• Render a “## Bibliography” section with numbered entries.                                                                |

**Tests:** `tests/test_markdown_exporter.py`

- `test_export_generates_markdown_structure`
- `test_front_matter_contains_required_fields`
- `test_citation_footnotes_and_bibliography_presence`

---

### G2. DOCX Exporter

**File:** `src/export/docx_exporter.py`
**Class:** `DocxExporter`

| Method                                                          | Purpose                                                                                                                                                  |
| --------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `export(workspace_id: str) → bytes`                             | • Load outline, metadata, citations.• Instantiate `python-docx` `Document` from template.• Call the helper methods below, then return the `.docx` bytes. |
| `generate_cover_page(doc: Document, metadata: dict)`            | • Insert title page: topic, author/date, branding logo.• Use styled placeholders in template.                                                            |
| `add_table_of_contents(doc: Document)`                          | • Insert a clickable TOC based on document headings.                                                                                                     |
| `populate_sections(doc: Document, outline: Outline)`            | • Iterate outline sections.• Add headings and bullet paragraphs, matching markdown converter.                                                            |
| `append_bibliography(doc: Document, citations: List[Citation])` | • Create a “Bibliography” heading.• Insert each citation as a paragraph or numbered list item.                                                           |

**Tests:** `tests/test_docx_exporter.py`

- `test_export_returns_valid_docx_bytes`
- `test_cover_page_contents_present`
- `test_toc_is_inserted`
- `test_bibliography_section_populated`

---

### G3. PDF Exporter

**File:** `src/export/pdf_exporter.py`
**Class:** `PdfExporter`

| Method                                    | Purpose                                                                                                   |
| ----------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| `export(workspace_id: str) → bytes`       | • Load markdown via `MarkdownExporter` or structured data.• Run pipeline: MD→HTML→PDF.• Return PDF bytes. |
| `convert_markdown_to_html(md: str) → str` | • Use a markdown library to render HTML.• Inject semantic CSS classes for styling.                        |
| `apply_css(html: str) → str`              | • Embed or reference the project’s print-CSS (covering fonts, margins, branding).                         |
| `render_pdf(html: str) → bytes`           | • Call WeasyPrint to produce a PDF from the styled HTML.                                                  |

**Tests:** `tests/test_pdf_exporter.py`

- `test_html_generation_from_markdown`
- `test_css_injection`
- `test_pdf_bytes_are_non_empty`

---

### G4. Citations JSON & Zip Export

#### G4.1 Citations JSON

**File:** `src/export/metadata_exporter.py`
**Function:** `export_citations_json(workspace_id: str) → bytes`

- **What:** Fetch all `Citation` records for the workspace and serialise them to JSON bytes.
- **Why:** Provides a machine-readable “citations.json” alongside human-readable exports.

**Test:** `tests/test_metadata_exporter.py`

- `test_export_citations_json_structure`

#### G4.2 Zip of All Formats

**File:** `src/export/zip_exporter.py`
**Class:** `ZipExporter`

| Method                                                       | Purpose                                                                                                                                           |
| ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| `collect_export_files(workspace_id: str) → Dict[str, bytes]` | • Invoke each exporter (`.export`) plus `export_citations_json`.• Return mapping of filenames (`lecture.md`, `lecture.docx`, etc.) to file bytes. |
| `generate_zip(files: Dict[str, bytes]) → bytes`              | • Package all given files into a single ZIP archive.• Return ZIP bytes.                                                                           |

**Test:** `tests/test_zip_exporter.py`

- `test_generate_zip_contains_all_expected_files`

---

### G5. FastAPI Export Endpoints

**File:** `src/web/api/export_endpoints.py`

| Function                                 | Purpose                                                                                                                                                    |
| ---------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `register_export_routes(app: FastAPI)`   | • Attach the five export routes below to the FastAPI `app`.                                                                                                |
| `get_markdown_export(workspace_id: str)` | • HTTP GET `/export/{workspace_id}/md`.• Calls `MarkdownExporter.export`, returns `text/markdown` with `Content-Disposition`.                              |
| `get_docx_export(workspace_id: str)`     | • HTTP GET `/export/{workspace_id}/docx`.• Calls `DocxExporter.export`, returns `application/vnd.openxmlformats-officedocument.wordprocessingml.document`. |
| `get_pdf_export(workspace_id: str)`      | • HTTP GET `/export/{workspace_id}/pdf`.• Calls `PdfExporter.export`, returns `application/pdf`.                                                           |
| `get_citations_json(workspace_id: str)`  | • HTTP GET `/export/{workspace_id}/citations.json`.• Returns JSON bytes from `export_citations_json`.                                                      |
| `get_all_exports(workspace_id: str)`     | • HTTP GET `/export/{workspace_id}/all`.• Calls `ZipExporter`, returns `application/zip`.                                                                  |

**Tests:** `tests/test_export_endpoints.py`

- `test_markdown_route_returns_200_and_markdown`
- `test_docx_route_returns_correct_content_type`
- `test_pdf_route_returns_pdf`
- `test_citations_route_returns_valid_json`
- `test_all_route_returns_zip_with_files`

---

## H. Browser-Based UX

---

### H1. SSE Backend

1. **`src/web/sse.py`**
   - `stream_workspace_events(workspace_id: str, event_type: str) -> AsyncGenerator[SseEvent]`
     • **What**: iterate over the main workflow and emit filtered `SseEvent` messages (`type`, `payload`, `timestamp`).
     • **Why**: centralises SSE logic so routes stay thin.

1. **`src/web/schemas/sse.py`**
   - `class SseEvent(BaseModel)` with fields `type: str`, `payload: dict`, `timestamp: datetime`
     • **What**: JSON schema for all SSE messages.
     • **Why**: ensures consistent typing for clients.

1. **`src/web/routes.py`**
   - `register_sse_routes(app: FastAPI)`
     • **Registers**:

     ```python
     @app.get("/stream/{workspace}", response_model=None)
     async def stream_events(workspace: str):
        return EventSourceResponse(stream_workspace_events(workspace, "state"))
     ```

     • **Why**: binds SSE generator to HTTP endpoint.

1. **`tests/web/test_sse.py`**
   - Test `test_sse_sequence()`
     • **What**: spin up test FastAPI app, connect via `httpx.AsyncClient` to `/stream/foo`, assert a known sequence of event types.
     • **Why**: validates end-to-end event streaming.

---

### H2. React App Scaffolding

1. **`frontend/src/main.tsx`**
   - **What**: bootstraps React, renders `<App />` into root.
   - **Why**: entrypoint for your SPA.

1. **`frontend/src/App.tsx`**
   - **What**: top-level layout; imports panels and initialises workspace store.
   - **Why**: glues together UI panels and global state.

1. **`frontend/src/store/useWorkspaceStore.ts`**
   - **Methods**:
     - `connect(workspaceId: string)` → opens SSE and subscribes
     - `updateState(event: SseEvent)` → dispatches to slices
     - Selectors: `documentState()`, `logEvents()`, `sources()`, `exportStatus()`

   - **Why**: single source of truth; panels subscribe here.

1. **`frontend/src/api/sseClient.ts`**
   - `connectToWorkspaceStream(token?: string, channel = "messages"): EventSource`
   - **Why**: encapsulates browser SSE setup (reconnect logic, backoff).

1. **Directory `frontend/src/components/`**
   - Create stub files for each panel (see H3–H6).
   - Each exports a default React component accepting props tied to the store.

---

### H3. Diff Highlighting & Typewriter (DocumentPanel)

1. **`frontend/src/utils/diffUtils.ts`**
   - `computeDiff(oldText: string, newText: string): DiffPatch[]`
   - `tokenize(text: string): string[]`
   - **Why**: reusable helpers to turn raw markdown into change sets.

1. **`frontend/src/components/DocumentPanel.tsx`**
   - **Props**: `text: string` (current markdown), `onAcceptDiff: (diffs)→void`
   - **Methods inside**:
     - `handleIncomingText(newText)` calls `computeDiff` + `animateDiff`
     - `animateDiff(diffs: DiffPatch[])` highlights insertions token-by-token

   - **Why**: shows live outline with diff highlighting and typewriter effect.

1. **`tests/frontend/utils/testDiffUtils.ts`**
   - Validate `computeDiff` output on sample before/after strings.

1. **`tests/frontend/components/DocumentPanel.test.tsx`**
   - Simulate prop changes, assert that newly inserted text is rendered with `.highlight` class for a brief period.

---

### H4. Citation Popover

1. **`frontend/src/api/citationClient.ts`**
   - `getCitation(workspaceId: string, citationId: string): Promise<Citation>`
   - **Why**: centralises fetch logic for metadata popover.

1. **`frontend/src/components/CitationPopover.tsx`**
   - **Props**: `citationId: string`
   - **State/Methods**:
     - `loadMetadata()` calls `getCitation` on mount
     - Renders `url`, `title`, `retrieved_at`, `licence` in a modal/popup

   - **Why**: provides inline “click-to-see” citation details.

1. **`tests/frontend/components/CitationPopover.test.tsx`**
   - Mock `citationClient.getCitation`, render popover, verify fields.

---

### H5. Controls

1. **`frontend/src/api/controlClient.ts`**
   - `run(workspaceId: string)`, `retry(workspaceId: string)`
   - **Why**: wrappers for the control endpoints.

1. **`frontend/src/components/ControlsPanel.tsx`**
   - **Buttons**: Run, Retry
   - **Handlers**:
     - `onRunClick()`, `onRetryClick()`, invoking respective `controlClient` methods and updating store.

   - **Why**: let users start and retry lecture generation jobs.

1. **`tests/frontend/components/ControlsPanel.test.tsx`**
   - Simulate clicks, verify correct API calls and disabled states.

---

### H6. Downloads Panel

1. **`frontend/src/api/exportClient.ts`**
   - `getStatus(workspaceId: string): Promise<ExportStatus>`
   - `getUrls(workspaceId: string): Promise<Record<"md"|"docx"|"pdf"|"zip", string>>`
   - **Why**: hides REST details for polling and link retrieval.

1. **`frontend/src/components/DownloadsPanel.tsx`**
   - **State/Methods**:
     - `startPolling()` on mount: calls `exportClient.getStatus` every 2s until `ready===true`
     - `renderLinks(urls)` once ready

   - **Why**: shows progress and final download buttons.

1. **`tests/frontend/components/DownloadsPanel.test.tsx`**
   - Mock status transitions (`pending` → `ready`), assert polling stops and links render.

---

## I. Deployment & Offline Mode

---

### I.1 FastAPI App Entrypoint

#### 1. `src/web/main.py`

- **`create_app()`**
  - Instantiate and configure the FastAPI application.
  - Load settings from `src/config.py`.
  - Register middleware (CORS, error handlers).

- **`setup_database(app)`**
  - Connect to SQLite, apply migrations (via Alembic).
  - Attach the DB session factory to `app.state.db`.

- **`setup_orchestrator(app)`**
  - Initialize the custom orchestrator and checkpointing module.
  - Store orchestrator instance on `app.state.orchestrator` for endpoint handlers.

- **`mount_frontend(app)`**
  - Serve the React build directory (`/frontend/dist`) at the root path.

- **`register_routes(app)`**
  - Include routers from:
    - `src/web/routes/stream.py`
    - `src/web/routes/control.py`
    - `src/web/routes/export.py`
    - `src/web/routes/citation.py`

- **`main()`**
  - Parse `--offline` flag (e.g. via `argparse` or Typer).
  - Set `Settings.OFFLINE_MODE` accordingly.
  - Launch Uvicorn server with `app = create_app()`.

#### 2. `src/config.py`

- **`load_settings()`**
  - Read environment variables (`OPENAI_API_KEY`, `PERPLEXITY_API_KEY`, `MODEL`, `DATA_DIR`, `OFFLINE_MODE`).
  - Validate types/defaults via Pydantic.
  - Expose a global `Settings` object.

#### 3. `src/persistence/database.py`

- **`init_db()`**
  - Create `aiosqlite` engine pointing at `${DATA_DIR}/workspace.db`.
  - Run Alembic migrations to create or upgrade tables.

- **`get_db_session()`**
  - Yield async DB sessions for request handlers.

---

### I.2 Docker & Compose

#### 1. `Dockerfile`

- **Base Image**
  - Python 3.11 slim + OS deps for WeasyPrint (e.g. `libpango`, `libcairo`).

- **Dependencies Installation**
  - Copy `pyproject.toml` & `poetry.lock`; run `poetry install --no-dev`.

- **Build Frontend**
  - Copy `frontend/`; run `npm ci` & `npm run build`.

- **App Copy & Entry**
  - Copy `src/` into container; set `WORKDIR`.
  - Define default `CMD ["uvicorn", "web.main:app", "--host", "0.0.0.0", "--port", "8000"]`.

#### 2. `docker-compose.yml`

- **Service: `app`**
  - Build context `.` using above `Dockerfile`.
  - Mount `./workspace:/app/data` for persistent SQLite.
  - Environment variables from `.env`.
  - Ports `8000:8000`.

- **Optional Service: `db-migrations`**
  - One-off container running `alembic upgrade head`.

---

### I.3 Local Dev Scripts

#### 1. `scripts/run.sh`

- **Purpose**: start the entire stack locally without Docker.
- **Steps**:
  1. Source `.env`.
  2. Poetry environment: `poetry run alembic upgrade head` (migrations).
  3. Poetry run: `uvicorn web.main:app --reload`.
  4. Pass through `--offline` if provided (`./run.sh --offline`).

#### 2. `scripts/reset_db.sh`

- **Purpose**: nuke and rebuild the SQLite workspace.
- **Steps**:
  1. Delete `${DATA_DIR}/workspace.db`.
  2. Run `alembic downgrade base` then `alembic upgrade head`.
  3. Optionally clear `${DATA_DIR}/cache/*`.

#### 3. `scripts/build_frontend.sh`

- **Purpose**: compile the React/Tailwind UI.
- **Steps**:
  1. `cd frontend && npm ci && npm run build`.
  2. Copy `frontend/dist` into `src/web/static`.

---

### I.4 Offline Mode Toggle

#### 1. In `create_app()` (main.py)

- Read `Settings.OFFLINE_MODE` and:
  - For search routes: bind `ResearcherWebClient` to either `ChatPerplexity` or `CacheBackedResearcher`.
  - For FactChecker: disable external URL fetches and license checks if `OFFLINE_MODE=True`.

#### 2. In Agents

- **`CacheBackedResearcher.search()`**
  - First look in `${DATA_DIR}/cache/{query}.json`; if missing, error fast.

- **`FactChecker.verify_sources()`**
  - If offline, skip HTTP calls and mark “unchecked” but pass.

---

## J. QA, Metrics & Governance

---

### J.1 Metrics Collector

**Goal:** Record key performance metrics at each agent run and expose them for monitoring.

1. **File:** `src/metrics/collector.py`
   - **Class:** `MetricsCollector`
     - **Method:** `record(metric_name: str, value: float)`
       - _What:_ Incrementally logs a metric (e.g. token count, cost) into an in-memory buffer or lightweight store.

     - **Method:** `flush_to_db()`
       - _What:_ Persists buffered metrics into SQLite (table `metrics`).

2. **File:** `src/metrics/repository.py`
   - **Class:** `MetricsRepository`
     - **Method:** `save(metric: MetricRecord)`
       - _What:_ Inserts a single metric row into the `metrics` table.

     - **Method:** `query(time_range: TimeRange) -> List[MetricRecord]`
       - _What:_ Fetches metrics for dashboards or alerts.

3. **File:** `src/web/metrics_endpoint.py`
   - **Function:** `get_metrics()`
     - _What:_ FastAPI GET handler on `/metrics`; pulls recent metrics via `MetricsRepository.query()` and renders in Prometheus format.

4. **Tests:**
   - `tests/test_metrics_collector.py`
     - Verifies `record()` and `flush_to_db()` correctly writes to SQLite.

   - `tests/test_metrics_endpoint.py`
     - Mocks some metric rows and asserts the HTTP response contains valid Prometheus lines.

---

### J.2 Threshold Alerts

**Goal:** After each lecture run, ensure metrics meet targets; if not, fire a webhook.

1. **File:** `src/metrics/alerts.py`
   - **Class:** `AlertManager`
     - **Method:** `evaluate_thresholds(workspace_id: str) -> AlertSummary`
       - _What:_ Aggregates metrics for the given workspace, compares against configuration (e.g. pedagogical ≥ 90 %, hallucination ≤ 2 %, cost ≤ 0.60 A\$).

     - **Method:** `send_webhook(alert: AlertSummary)`
       - _What:_ POSTs alert details to a configured webhook URL (from settings).

2. **File:** `src/config/thresholds.yaml`
   - **Contents:**
     - `pedagogical_score: 0.90`
     - `max_hallucination_rate: 0.02`
     - `max_cost_per_lecture: 0.60`

3. **File:** `src/web/alert_endpoint.py`
   - **Function:** `post_alerts(workspace_id: str)`
     - _What:_ FastAPI POST handler at `/alerts/{workspace}` that invokes `AlertManager.evaluate_thresholds()`, then `send_webhook()` if any breach.

4. **Tests:**
   - `tests/test_alert_evaluation.py`
     - Supplies synthetic metric sets to `evaluate_thresholds()` and checks correct breach flags.

   - `tests/test_alert_webhook.py`
     - Mocks an HTTP server and asserts `send_webhook()` posts the right payload.

---

### J.3 RBAC Middleware

**Goal:** Enforce role-based access on API routes: viewer, editor, admin.

1. **File:** `src/web/auth.py`
   - **Function:** `get_current_user(token: str) -> UserContext`
     - _What:_ Decodes JWT or API key into a `UserContext` object with `role` attribute.

   - **Function:** `require_role(required: Literal["viewer","editor","admin"])`
     - _What:_ Returns a FastAPI dependency that raises 403 unless `current_user.role ≥ required`.

2. **File:** `src/web/dependencies.py`
   - **Function:** `ensure_viewer(user=Depends(get_current_user))`
     - _What:_ Alias for `require_role("viewer")`.

   - **Function:** `ensure_editor(user=Depends(get_current_user))`
     - _What:_ Alias for `require_role("editor")`.

   - **Function:** `ensure_admin(user=Depends(get_current_user))`
     - _What:_ Alias for `require_role("admin")`.

3. **File:** `src/web/routes/*.py`
   - **Usage:**
     - In `export` routes: add `dependencies=[Depends(ensure_viewer)]`.
     - In `run/retry` routes: `dependencies=[Depends(ensure_editor)]`.
     - In governance or metrics endpoints: `dependencies=[Depends(ensure_admin)]`.

4. **Tests:**
   - `tests/test_rbac.py`
     - Parametrised tests that simulate tokens with different roles and assert 200 vs. 403 responses on key endpoints.

---

### J.4 Audit Trail Verification

**Goal:** Provide a tamper-evident listing of saved state hashes and a CLI tool to compare them.

1. **File:** `src/audit/trail.py`
   - **Class:** `AuditTrailManager`
     - **Method:** `list_hashes(workspace_id: str) -> List[StateHashRecord]`
       - _What:_ Queries the `state` table for each version’s stored SHA-256 hash and timestamp.

     - **Method:** `compare_states(hash1: str, hash2: str) -> DiffSummary`
       - _What:_ Retrieves the two serialized state blobs and reports whether they match or not (and which fields differ).

2. **File:** `src/web/audit_endpoint.py`
   - **Function:** `get_audit_list(workspace_id: str)`
     - _What:_ FastAPI GET on `/audit/{workspace}`; returns the list of hashes and timestamps.

   - **Function:** `compare_audit(workspace_id: str, h1: str, h2: str)`
     - _What:_ GET on `/audit/{workspace}/compare?h1=…&h2=…`; returns `DiffSummary`.

3. **File:** `cli/audit_cli.py`
   - **Command:** `python -m audit_cli list --workspace X`
     - _What:_ Prints all state hashes to console in a table.

   - **Command:** `python -m audit_cli compare --workspace X --h1 … --h2 …`
     - _What:_ Calls `AuditTrailManager.compare_states()` and prints whether identical or shows diff summary.

4. **Tests:**
   - `tests/test_audit_trail.py`
     - Inserts two known state blobs, computes expected hashes, and verifies `list_hashes()` and `compare_states()` behave correctly.

---

## K: Validate & Confirm

---

### K.1 Enforce OpenAI o4-mini for All Agents

> **Objective:** Guarantee every LLM call uses `o4-mini` by default.

1. **`src/config.py`**
   - **Field:** `MODEL: str = "openai:o4-mini"`
     _Default model string; never null._

2. **`src/core/orchestrator.py`**
   - **Method:** `validate_model_configuration()`
     _Runs at startup to assert `config.MODEL == "openai:o4-mini"`, or raise a clear error._

3. **`src/agents/model_utils.py`**
   - **Function:** `init_model()` centralizes Pydantic AI model creation.
     _Reads `settings.model` and constructs the provider/model for API calls._

4. **Acceptance:**
   - Startup log prints “Using LLM engine o4-mini”
   - Unit test in `tests/test_model_config.py` covers a mis-set environment var.

---

### K.2 Surface CritiqueReport Metrics in UI

> **Objective:** Push pedagogy/fact-check scores to a new “Quality” tab via SSE, with colour coding for thresholds.

1. **`src/agents/pedagogy_critic.py`**
   - **Method:** `generate_critique_report(state: State) → CritiqueReport`
     _Already returns metrics; no change._

2. **`src/web/sse_quality_stream.py`**
   - **Function:** `quality_stream(workspace_id: str)`
     _Subscribes to Critic node outputs, wraps each `CritiqueReport` as SSE event with type `"quality"`._
   - **Integration:** Mount to FastAPI under `GET /stream/{workspace}/quality`.

3. **`src/store/qualityStore.js`**
   - **Action:** `receiveQualityMetrics(report)`
     _Ingests SSE payloads into React state._

4. **`src/components/QualityTab.jsx`**
   - **Component:** `QualityTab`
     _Renders a table/list of metrics, applies green/orange/red styling based on each score vs. its threshold._

5. **Acceptance:**
   - Academics see a new “Quality” tab next to “Document” and “Log.”
   - Scores below threshold are red, above are green.

---

### K.3 Add Citation-Style Configuration

> **Objective:** Allow users to supply a CSL file (e.g. APA, Harvard) and have all exporters honour it.

1. **`src/config.py`**
   - **Field:** `CSL_PATH: Optional[str] = None`
     _Path to user-provided CSL file._

2. **`src/export/exporter_base.py`**
   - **Method:** `set_citation_style(self, csl_path: str)`
     _Loads CSL into a `citeproc-python` processor instance on the exporter._

3. **`src/export/markdown.py`**
   - **Class:** `MarkdownExporter(ExporterBase)`
     - **Override:** `render_citations(self, citations: List[Citation]) → str`
       _Passes citations through `citeproc-python` using the loaded CSL._

4. **`src/export/docx.py`**
   - **Class:** `DocxExporter(ExporterBase)`
     - **Override:** `apply_citations(self)`
       _Formats footnotes via `citeproc-python` with the CSL._

5. **`src/export/pdf.py`**
   - **Class:** `PdfExporter(ExporterBase)`
     - **Override:** `apply_citations(self)`
       _Same as DOCX but in the HTML → PDF pipeline._

6. **`src/web/routes/config_routes.py`**
   - **Route:** `POST /config/csl`
     _Accepts file upload, saves to `config.CSL_PATH`, and triggers a reload of all exporter instances._

7. **Acceptance:**
   - Engineer can upload an APA or Harvard CSL via UI; all exports reflect that style.

---

### K.4 Log Panel & CSV Download

> **Objective:** Expose the persisted action log next to the DocumentPanel and allow CSV export.

1. **`src/persistence/log_repo.py`**
   - **Method:** `export_logs_csv(workspace_id: str) → str`
     _Queries `logs` table and serialises rows to a CSV string._

2. **`src/web/routes/log_routes.py`**
   - **Route:** `GET /logs/{workspace_id}.csv`
     _Returns `export_logs_csv(...)` with `text/csv` headers._

3. **`src/components/LogPanel.jsx`**
   - **Component:** `LogPanel`
     _Fetches `/logs/{workspace}` as JSON for inline display; shows columns: agent, timestamp, tokens, cost._

4. **`src/components/DownloadCsvButton.jsx`**
   - **Component:** `DownloadCsvButton`
     _Triggers a download from `/logs/{workspace}.csv` when clicked._

5. **Acceptance:**
   - Users can scroll through the log in-app and click “Download CSV” to get the raw audit data.

---

### K.5 Robust SSE & Reconnect UX

> **Objective:** Harden the SSE client with exponential back-off, heartbeat pings, and a reconnect toast.

1. **`src/web/middleware/sse_client.js`**
   - **Function:** `connectWithBackoff(url: string, onMessage, onError)`
     _Attempts initial `EventSource`; on connection failure or `error` event, retries with back-off delays (e.g. 1s, 2s, 4s…)._

   - **Function:** `startHeartbeat(eventSource)`
     _Every 30 s, sends a dummy ping; if no `open` event in window, triggers `eventSource.close()` and restarts back-off._

2. **`src/store/connectionStore.js`**
   - **Action:** `setConnectionStatus(status: "connected"|"disconnected"|"reconnecting")`
   - **State:** holds current SSE status for UI use.

3. **`src/components/SSEProvider.jsx`**
   - **Component:** `SSEProvider`
     _Initialises `connectWithBackoff`, wires `onopen`/`onerror` to update `connectionStore`, and calls `startHeartbeat`._

4. **`src/components/Toast.jsx`**
   - **Component:** `Toast`
     _Listens to `connectionStore`; when status transitions to `"reconnecting"`, displays a dismissible “Attempting to reconnect…” toast._

5. **Acceptance:**
   - Network interruption triggers the toast and automatic reconnection attempts.
   - Once reconnected, a brief “Reconnected” message appears and normal SSE events resume.

---
