# agentic-demo

This repository demonstrates two main workflows for generating course content using agentic techniques:

* **Lecture Builder** – assembles lecture notes from topic prompts and reference material.
* **AI-Curriculum Overlay** – applies generative methods to enrich or modify an existing curriculum.

## License

This project is released under the [Unlicense](LICENSE).

## Setup

1. **Python**: Use Python 3.13 or newer.
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Start the API server**:
   ```bash
   uvicorn app.api:app --reload
   ```
4. **Run the demo script**:
   ```bash
   python scripts/run_demo.py --topic "Quantum" 
   ```

## Configuration

This project uses environment variables for API keys. Start by copying the
provided example file and editing it with your credentials:

```bash
cp .env.example .env
```

The `OPENAI_API_KEY` variable enables real responses from OpenAI services. If it
is unset the demo prints placeholder text. If you have a Tavily account, you can also set `TAVILY_API_KEY` to enable
search features. Uvicorn can load this file automatically with `--env-file .env`,
and the demo script supports `python -m dotenv run -- python scripts/run_demo.py ...`.

## API

The FastAPI app exposes a single endpoint:

- `POST /chat?input=TEXT` – runs the conversation flow and returns
  `{"response": "..."}`.

Start the server using the command shown in the setup section and send requests
to `http://localhost:8000/chat`.

## Running Tests

Execute all tests with `pytest` from the repository root:

```bash
pytest
```
