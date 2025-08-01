# Coding Requirements

This project enforces consistent, secure and maintainable Python code.

## Quality Checks

Run the following tools before committing changes:

- `black .` – auto-format the codebase.
- `ruff check .` – enforce style rules and catch common bugs.
- `mypy .` – perform static type checking.
- `bandit -r app -ll` – scan for security issues.
- `pip-audit` – check dependencies for known vulnerabilities.
- `pytest --cov` – execute the test suite with coverage enabled.

## Development Standards

- Follow **Test Driven Development**. Create TODO comments and failing tests before implementing features.
- Keep functions small with cyclomatic complexity below 8.
- Maintain line, branch and function coverage above 90%.
- Document every function with purpose, inputs, outputs, side effects and exceptions.

These requirements mirror the automation configured in the GitHub workflow and must be satisfied for every pull request.
