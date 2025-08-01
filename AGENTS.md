# Agent Workflow Guidance

This repository uses automated code quality tooling for all Python sources.

## Formatting
- Run `black .` to auto-format the code base.

## Linting
- Execute `ruff .` to check style and catch common bugs.

## Security
- Run `bandit -q -r app openai_stub scripts web` to scan for vulnerabilities.

## Static Analysis
- Run `mypy .` to perform type checking.

## Testing
- Install dependencies with `pip install -e '.[dev,test]'`.
- Run the full suite with `pytest --cov`.

The CI workflow mirrors these commands and also verifies formatting, linting,
type checking and security scanning. Run them locally before committing to avoid failures.

### Development Process
- Follow Test Driven Development.
  1. Write TODO comments describing needed behavior.
  2. Add failing tests covering the TODOs.
  3. Implement the minimal code to make tests pass.
  4. Refactor for readability and performance.
- Keep functions small (cyclomatic complexity < 8).
- Maintain test coverage above 90%.

