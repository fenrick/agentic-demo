# Streaming OpenAI Responses

The API server exposes an endpoint that streams tokens from OpenAI to the browser using **Server-Sent Events (SSE)**.

1. The service requests a streaming completion from OpenAI. Each chunk arrives as soon as the model generates it.
2. A FastAPI route wraps the OpenAI iterator and yields each chunk as an SSE `data:` message using the `text/event-stream` media type.
3. The browser connects with `EventSource`, receiving token events incrementally. UI code appends each token to the page as it arrives.
4. When the stream ends, a final event delivers aggregate statistics such as total tokens and latency.

This flow provides near real-time feedback without requiring a WebSocket. Standard HTTP semantics make it easy to proxy and debug.
