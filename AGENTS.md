# Agent Workflow Guidance

This repository uses automated code quality tooling for all Python sources.

## Formatting
- Run `black .` to auto-format the code base.

## Linting
- Execute `ruff .` to check style and catch common bugs.

## Static Analysis
- Run `mypy .` to perform type checking.
- Execute `bandit -r app -ll` to scan for security issues.
- Run `pip-audit` to check dependencies for vulnerabilities.

## Testing
- Install dependencies with `pip install -e .[test]`.
- Run the full suite with `pytest --cov`.

### Development Process
- Follow Test Driven Development.
  1. Write TODO comments describing needed behavior.
  2. Add failing tests covering the TODOs.
  3. Implement the minimal code to make tests pass.
  4. Refactor for readability and performance.
- Keep functions small (cyclomatic complexity < 8).
- Maintain test coverage above 90%.
- See [docs/CODING_REQUIREMENTS.md](docs/CODING_REQUIREMENTS.md) for full guidelines.

