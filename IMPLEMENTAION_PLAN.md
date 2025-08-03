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

2. **`.gitignore`**

- **Purpose**: Exclude Python build artefacts, virtual environments, workspace data.
- **Entries**:
  - `__pycache__/`
  - `.env`
  - `workspace/*`
  - `*.pyc`, `poetry.lock`, `.venv/`

3. **`pyproject.toml`**

- **Purpose**: Define project metadata, Python version, and dependencies stub.
- **Sections**:
  - `[tool.poetry]`: `name`, `version`, `description`, `authors`.
  - `[tool.poetry.dependencies]`: placeholder entries for `python>=3.11`, `langgraph`, `openai`, etc.
  - `[tool.poetry.dev-dependencies]`: `pytest`, `black`, `flake8`, `isort`, `pre-commit`.

4. **`.pre-commit-config.yaml`**

- **Purpose**: Enforce code style on each commit.
- **Hooks**:
  - `black` (formatting),
  - `isort` (imports),
  - `flake8` (linting).

5. **Initial Commit**

- Run `git init` and commit:
  1.  `README.md`
  2.  `.gitignore`
  3.  `pyproject.toml` (empty dependencies)
  4.  `.pre-commit-config.yaml`

---

## A2. Environment Variables & Config Loader

1. **`.env.example`**

- **Purpose**: Template for required environment variables.
- **Variables listed**:
  - `OPENAI_API_KEY`
  - `PERPLEXITY_API_KEY`
  - `MODEL_NAME` (default: `o4-mini`)
  - `DATA_DIR` (default: `./workspace`)
  - `OFFLINE_MODE` (default: `false`)

2. **`src/config.py`**

- **Class**: `Settings`
  - **Method**: `load_from_env()`

  - Reads `.env` (via python-dotenv) plus real `os.environ`.
  - Fills attributes: `openai_api_key`, `perplexity_api_key`, `model_name`, `data_dir`, `offline_mode`.
  - **Method**: `validate()`

  - Checks required keys present, valid directory path for `data_dir`.
  - Raises on missing/invalid values.

3. **`tests/test_config.py`**

- **Test function**: `test_settings_defaults()`
  - Clears env vars, calls `Settings.load_from_env()`, asserts default values.

- **Test function**: `test_settings_override()`
  - Sets env vars in test, calls `load_from_env()`, asserts those override defaults.

- **Test function**: `test_settings_validate_errors()`
  - Provides invalid `DATA_DIR`, expects `validate()` to raise.

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

2. **`ci.yml` (GitHub Actions)**

- **Job**: `build-and-test`
  - **Runs-on**: `ubuntu-latest`
  - **Steps**:
  1.  **Checkout code** (`actions/checkout@v3`)
  2.  **Setup Python** (`actions/setup-python@v4`) with version `3.11`
  3.  **Install Poetry**
  4.  **Cache** Poetry cache & `.venv`
  5.  **Install dependencies** (`poetry install --no-interaction --no-ansi`)
  6.  **Run linters** (`poetry run pre-commit run --all-files`)
  7.  **Run tests** (`poetry run pytest --maxfail=1 --disable-warnings -q`)

3. **Local Test & Lint Scripts**

- **File**: `scripts/run_checks.sh`
  - **Invokes**: `poetry run pre-commit run --all-files` then `poetry run pytest`.

- **File**: `scripts/reset_workspace.sh`
  - **Deletes**: `workspace/*.db` and `workspace/cache/*` to start fresh.

---

## B. Orchestration Core (LangGraph StateGraph)

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

- **Method `initialize_graph()`**
  - Instantiate a `StateGraph<State>` and register all nodes with their stream channels (`values`, `updates`, `messages`, `debug`).

- **Method `register_edges()`**
  - Wire node-to-node transitions, referencing policies (see B.3).

- **Method `start(initial_prompt: str)`**
  - Create initial `State`, invoke the first Planner run, and begin streaming.

- **Method `resume()`**
  - Load check-pointed state, hook into an existing graph instance, and continue where it left off.

---

### B.3 Edge Policies & Loop Logic

**File:** `src/core/policies.py`

- **Function `policy_retry_on_low_confidence(prev: PlanResult) → bool`**

- Returns `true` if Planner’s confidence \< threshold, to loop back into Researcher.

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

- Instantiate `SqliteCheckpointManager` with `DATA_DIR`.
- Pass it into `GraphOrchestrator`, so every node completion triggers `save_checkpoint()`.

---

## Step C: Retrieval & Citation Layer

---

### C.1 Perplexity API Client & Offline Fallback

#### 1. `src/agents/researcher_web.py`

- **Class `PerplexityClient`**

- **`search(self, query: str) → List[RawSearchResult]`**
  Calls the Perplexity API, returns raw snippets + URLs.
- **`fallback_search(self, query: str) → List[RawSearchResult]`**
  Invoked when `OFFLINE_MODE` is true; loads from cache instead of HTTP.

- **Class `RawSearchResult`** (data container)

- Fields: `url: str`, `snippet: str`, `title: str`

#### 2. `src/agents/offline_cache.py`

- **`load_cached_results(query: str) → Optional[List[RawSearchResult]]`**
  Reads `workspace/cache/{sanitized_query}.json` if present.
- **`save_cached_results(query: str, results: List[RawSearchResult])`**
  Persists fresh API responses for offline reuse.

#### 3. `src/agents/researcher_web_runner.py`

- **`run_web_search(state: State) → List[CitationDraft]`**
  Coordinates:

1.  Calls `PerplexityClient.search` or `.fallback_search`
2.  Wraps each `RawSearchResult` in a preliminary `CitationDraft` (url + snippet + title)

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

##### `src/persistence/migrations/XXXX_create_citations_table.py`

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

##### `src/persistence/db.py`

- **`get_db_session() → AsyncGenerator[Connection, None]`**
  Yields an `aiosqlite` connection configured to the workspace’s SQLite file.

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

1.  Call `PerplexityClient.search` (or fallback).
2.  Wrap into `CitationDraft`.
3.  Apply `rank_by_authority`.
4.  Apply `filter_allowlist`.
5.  For each remaining draft:

- Enrich with `retrieved_at = now()`, lookup `licence` via simple HTTP HEAD if needed.
- Instantiate a `Citation` model.
- Persist via `CitationRepo.insert`.

6.  Return the final `List[Citation]` for the orchestrator to merge into state.

---

#### Hand-Off to the Orchestrator

Once `researcher_pipeline` returns `List[Citation]`, your LangGraph node will:

- Merge them into `state.sources`.
- Emit a `stream(updates)` event, so the UI can show new citations in real time.

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

- Calls OpenAI via function-calling API, passing system + user prompts and schema.
- Streams partial tokens back via LangGraph’s `.stream("messages")`.
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

1.  Only the flagged sections are re-sent to the weaver
2.  Retry counts increment properly
3.  The loop halts after three attempts

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
  _Points Alembic at your SQLite file (`DATA_DIR/checkpoint.db`)._

2. **Create State Table Migration**

- **File:** `migrations/versions/20250804_create_state_table.py`
  - Defines a `state` table with columns:

  - `id` (primary key)
  - `payload_json` (TEXT)
  - `version` (INTEGER)
  - `updated_at` (TIMESTAMP)

3. **Create Documents Table Migration**

- **File:** `migrations/versions/20250804_create_documents_table.py`
  - Defines a `documents` table with columns:

  - `id` (primary key)
  - `state_id` (foreign key → `state.id`)
  - `parquet_blob` (BLOB)
  - `created_at` (TIMESTAMP)

4. **Alembic Revision Commands**

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

2. **DocumentRepo**

- **File:** `src/persistence/repos/document_repo.py`
- **Class:** `DocumentRepo`
  - `save_document_version(state_id: int, blob: bytes) -> int`
    _Stores a Parquet blob for the given `state_id`; returns the new document row’s `id`._
  - `list_versions(state_id: int) -> List[DocumentMetadata]`
    _Returns metadata (id, created_at) for all blobs tied to a state._
  - `load_latest_document(state_id: int) -> bytes`
    _Fetches the most recent Parquet blob for rendering or diffing._

3. **PersistenceManager**

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

2. **Schema Validation**

- **File:** `src/persistence/parquet_schema.py`
  _Defines the Arrow schema used for every version, ensuring compatibility across reads/writes._

3. **Unit Tests**

- **File:** `tests/persistence/test_parquet_serializer.py`
  - Verify that `serialize_outline()` + `deserialize_outline()` yields an object equal to the original.
  - Test with edge cases: empty outline, large outlines.

---

### F.4 Resume & Recovery Testing

1. **Integration Test: Resume from Checkpoint**

- **File:** `tests/integration/test_resume_from_checkpoint.py`
- **Scenario:**
  1.  Kick off a graph run up through the Content Weaver node.
  2.  Simulate process crash (kill graph or clear in-memory state).
  3.  Invoke `graph.invoke(resume=True)`.
  4.  Assert that:
  - `PersistenceManager.restore()` returns the same `State` and `Outline`.
  - The Exporter can still generate valid Markdown from the restored outline.

2. **CLI Smoke Script**

- **File:** `scripts/test_resume.sh`
- **Steps:**
  1.  Start FastAPI + LangGraph with a sample prompt.
  2.  Wait for “outline ready” event in logs.
  3.  Kill the process.
  4.  Restart with `--resume`.
  5.  Poll `/export/…/md` endpoint and verify it returns non-empty Markdown.

3. **Error Injection**

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

1. **SSE Backend**
   1.1. Create `/stream/{workspace}` SSE endpoint in FastAPI, hooking into `graph.astream()`.
   1.2. Serialise each event with fields `{type, payload, timestamp}`.
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
   4.1. Render footnote markers; on click, fetch full citation metadata via `GET /citations/{id}`.
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
   1.1. Create `main.py` initialising Config, DB, Graph, and mounting React build under `/`.
   1.2. Add CLI flag `--offline` to toggle search and fact-check behaviour.

2. **Dockerfile & Compose**
   2.1. Write `Dockerfile` installing system dependenciess for WeasyPrint, copying app, running `uvicorn main:app`.
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
   2.2. If breached, `POST` to a configurable webhook URL.

3. **RBAC Middleware**
   3.1. Implement FastAPI dependency checking JWT claims for `role` ∈ {viewer, editor, admin}.
   3.2. Protect routes accordingly (`export` open to viewer+, `run` to editor+, admin for governance endpoints).

4. **Audit Trail Verification**
   4.1. Create endpoint `/audit/{workspace}` that lists SHA-256 hashes of each saved state.
   4.2. Offer a “compare” utility in CLI to diff two states by hash.

---
