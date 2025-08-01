# agentic-demo

This repository demonstrates two main workflows for generating course content using agentic techniques:

* **Lecture Builder** – assembles lecture notes from topic prompts and reference material.
* **AI-Curriculum Overlay** – applies generative methods to enrich or modify an existing curriculum.

## License

This project is released under the [Unlicense](LICENSE).

## Setup

1. **Python**: Use Python 3.11 or newer.
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
