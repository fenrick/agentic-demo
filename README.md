# agentic-demo

This repository demonstrates two main workflows for generating course content using agentic techniques:

* **Lecture Builder** – assembles lecture notes from topic prompts and reference material.
* **AI-Curriculum Overlay** – applies generative methods to enrich or modify an existing curriculum.

## License

This project is released under the [Unlicense](LICENSE).

## Setup

1. **Python**: Use the latest Python 3 release.
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   The optional `openai` dependency enables real API calls. Without it,
   the bundled `openai_stub` module provides placeholder responses.
   To hack on the code locally, install in editable mode:
   ```bash
   pip install -e .
   ```
3. **Start the API server**:
   ```bash
   uvicorn app.api:app --reload
   ```

4. **Send a run request**:
   ```bash
   curl -X POST http://localhost:8000/runs -H 'Content-Type: application/json' -d '{"topic":"Quantum"}'
   ```


## `openai_stub`

The minimal `openai_stub` package lets the demo run without the real
OpenAI client. It returns a placeholder response whenever the `openai`
library is missing. Install the official `openai` package and set an
`OPENAI_API_KEY` in your environment to receive genuine completions.

## Configuration

This project uses environment variables for API keys. The included
`.env.example` file provides a convenient starting point:

```bash
cp .env.example .env
```

The `OPENAI_API_KEY` variable enables real responses from OpenAI services. If it
is unset the demo prints placeholder text. If you have a Tavily account, you can also set `TAVILY_API_KEY` to enable
search features. Uvicorn can load this file automatically with `--env-file .env`,
and the demo script supports `python -m dotenv run -- python scripts/run_demo.py ...`.

### LangSmith tracing

Set `LANGCHAIN_API_KEY` and `LANGCHAIN_PROJECT` to send traces to
[LangSmith](https://smith.langchain.com). The application decorates agent
functions and graph nodes with `@langsmith.traceable`, so events are captured
automatically when these variables are configured.

## Docker Usage

A Dockerfile is included for local development and deployment. See
[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for build and run instructions.

## API

The FastAPI app exposes two endpoints:

- `POST /runs` – start a new run for a given topic and persist its outputs.
- `GET /runs/{run_id}/stream` – stream the generated tokens via Server-Sent Events.

Start the server using the command shown in the setup section.

The service streams OpenAI responses using **Server-Sent Events (SSE)**. Tokens
are forwarded directly from FastAPI to the browser so no WebSocket is required.
See [docs/streaming.md](docs/streaming.md) for a detailed overview of this
flow.

## Running Tests

Install the development dependencies and run the test suite using `pytest`:

```bash
pip install -r requirements-dev.txt
pytest
```

## Architecture

See [`docs/architecture.md`](docs/architecture.md) for a full overview of the
system diagram. The FastAPI service orchestrates five cooperating agents through
LangGraph and persists all runs to SQLite for deterministic versioning.

## Agentic Workflow

The application orchestrates content creation through five specialised agents. Each topic is processed section by section so every phase can refine the output.

1. **Planner** – break the request into an outline of subtopics.
2. **Researcher** – gather background notes for each subheading.
3. **Synthesiser** – draft a coherent section from the notes.
4. **Pedagogy-Critic** – review the draft for clarity and instructional value.
5. **QA-Reviewer** – perform a final pass to confirm style and structure.

The conversation graph in ``app.graph`` repeats steps 2–4 until the review approves the content. Once all subsections are finalized, the final edit produces the polished document.

## Coding requirements

For detailed coding standards and quality checks see
[`docs/CODING_REQUIREMENTS.md`](docs/CODING_REQUIREMENTS.md).

