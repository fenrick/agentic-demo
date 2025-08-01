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
4. **Open the web interface**:
   Navigate to `http://localhost:8000/ui` once the server is running.
   The page streams intermediate results as they arrive and provides
   **Download Markdown** and **Download DOCX** buttons for exporting
   the final output.
5. **Run the demo script**:
   ```bash
   python scripts/run_demo.py --topic "Quantum"
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

## Docker Usage

A Dockerfile is included for local development and deployment. See
[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for build and run instructions.

## API

The FastAPI app exposes several endpoints:

- `POST /chat?input=TEXT` – runs the conversation flow and returns
  `{"response": "..."}`.
- `GET /ui` – serves a simple browser UI for interactive use.

Start the server using the command shown in the setup section.
Open `http://localhost:8000/ui` for the web interface or send requests to
`http://localhost:8000/chat`.

## Running Tests

Install the development dependencies and run the test suite using `pytest`:

```bash
pip install -r requirements-dev.txt
pytest
```

## Agentic Workflow

The application orchestrates content creation through a sequence of prompts and agents. Each topic is processed section by section, allowing refinements at every stage.

1. **Research** – gather background notes for each subheading.
2. **Draft** – generate initial text from the notes.
3. **Edit** – review and adjust the draft for clarity and coherence.
4. **Rewrite** – produce an improved revision using feedback from the edit step.
5. **Final edit and polish** – complete a last pass to ensure consistent style and structure across all sections.

The conversation graph in ``app.graph`` repeats steps 2–4 until the review approves the content. Once all subsections are finalized, the final edit produces the polished document.

The :class:`~app.workflow.DocumentWorkflow` helper wraps this graph. It starts
by planning an outline, then iterates over each heading so that every section
flows through the Research → Draft → Edit → Rewrite cycle before the parts are
combined. Each section runs through a graph built with ``skip_plan=True`` so the
outline step isn't repeated. Once the sections are joined, a final review agent
polishes the document before returning it.

## Coding requirements

For detailed coding standards and quality checks see
[`docs/CODING_REQUIREMENTS.md`](docs/CODING_REQUIREMENTS.md).

