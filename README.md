# agentic-demo

A minimal Python project managed with [Poetry](https://python-poetry.org/) targeting Python 3.13.

## Layout

- `src/` – application source code
- `tests/` – unit tests
- `scripts/` – helper scripts
- `workspace/` – scratch space ignored by version control

## Development

Install dependencies and run quality checks:

```bash
pip install -e .[test]
black .
ruff .
mypy .
bandit -r src -ll
pip-audit
pytest --cov
```
