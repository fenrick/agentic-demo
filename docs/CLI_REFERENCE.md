# CLI Reference

Command-line shortcuts for running the application, executing tests, and handling maintenance tasks. All commands are run from the repository root.

---

## Running the Application

- **Start the FastAPI server**

  ```bash
  ./scripts/run.sh [--offline]
  ```

  Launches the backend with hot reload; use `--offline` to disable external network calls.

- **Generate lecture material**

  ```bash
  ./scripts/cli.sh [--verbose] "<topic>"
  ```

  Produces a structured lecture in Markdown for the topic and saves it to `run_output.md`.
  `--verbose` shows progress logs. Use `--output` to specify a different
  Markdown file.

## Testing

- **Backend tests**

  ```bash
  poetry run pytest
  ```

- **Frontend tests**

  ```bash
  npm test
  ```

## Maintenance

- **Reset the workspace database**

  ```bash
  ./scripts/reset_db.sh
  ```

- **Build the production frontend**

  ```bash
  ./scripts/build_frontend.sh
  ```

