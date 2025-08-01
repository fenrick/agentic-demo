# agentic-demo

This repository demonstrates two main workflows for generating course content using agentic techniques:

* **Lecture Builder** – assembles lecture notes from topic prompts and reference material.
* **AI-Curriculum Overlay** – applies generative methods to enrich or modify an existing curriculum.

## Setup

1. **Python**: Use Python 3.10 or newer.
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the CLI**:
   ```bash
   python -m agentic_demo.cli
   ```

## Configuration

This project uses environment variables for API keys. Start by copying the
provided example file and editing it with your credentials:

```bash
cp .env.example .env
```

The `OPENAI_API_KEY` variable is required to interact with OpenAI services.
If you have a Tavily account, you can also set `TAVILY_API_KEY` to enable
search features.

## Running Tests

Execute all tests with `pytest` from the repository root:

```bash
pytest
```