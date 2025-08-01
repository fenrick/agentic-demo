# System Architecture

This project orchestrates several agents via a langgraph flow exposed through a
FastAPI application. The web UI streams node outputs back to the browser so
users can observe each step in real time.

```mermaid
graph TD
    A[Web UI / API] -->|input| B(build_graph)
    B --> C[plan node]
    C --> D[research node]
    D --> E[draft node]
    E --> F[review node]
    F -->|approved| G[overlay node]
    F -->|retry| E
    G --> H[(output)]
```

Each node wraps a small agent function decorated with `@langsmith.traceable` so
token metrics and events are recorded when LangSmith environment variables are
configured.

