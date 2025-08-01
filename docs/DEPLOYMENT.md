# Deployment

This project provides a Dockerfile for running the application in a container.

## Build the image

```bash
docker build -t agentic-demo .
```

## Development mode

Mount the source tree and use `--reload` to automatically pick up changes:

```bash
docker run --rm -it -p 8000:8000 -v $(pwd):/app agentic-demo \
  uvicorn app.api:app --host 0.0.0.0 --reload
```

## Production mode

Run the prebuilt image without mounting local files. Pass environment variables
such as `OPENAI_API_KEY` or load them from a file:

```bash
docker run --rm -it -p 8000:8000 --env-file .env agentic-demo
```

## Testing inside the container

Install the development dependencies and execute the test suite:

```bash
docker run --rm -it -v $(pwd):/app -w /app agentic-demo \
  /bin/bash -c "pip install -e .[test,dev] && pytest --cov"
```
