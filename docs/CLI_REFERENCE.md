# CLI Reference

Command-line shortcuts for running the application, executing tests, and handling maintenance tasks. All commands are run from the repository root.

---

## Running the Application

- **Start the FastAPI server**

  ```bash
  ./scripts/run.sh [--offline]
  ```

  Launches the backend with hot reload; use `--offline` to disable external network calls.

## Testing

- **Backend tests**

  ```bash
  poetry run pytest
  ```

- **Frontend tests**

  ```bash
  npm test
  ```

- **Resume workflow smoke test**

  ```bash
  ./scripts/test_resume.sh "<prompt>"
  ```

  Starts the server, generates an outline for the prompt, and verifies export resume functionality.

## Maintenance

- **Reset the workspace database**

  ```bash
  ./scripts/reset_db.sh
  ```

- **Build the production frontend**

  ```bash
  ./scripts/build_frontend.sh
  ```
