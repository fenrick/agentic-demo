import json

import httpx

from agents.researcher_web import TavilyClient


def test_tavily_client_parses_response():
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:  # pragma: no cover - simple handler
        payload = json.loads(request.content.decode())
        assert payload["query"] == "query"
        data = {
            "results": [
                {"url": "https://tavily.com", "content": "info", "title": "Tavily"}
            ]
        }
        return httpx.Response(200, json=data)

    transport = httpx.MockTransport(handler)
    client = TavilyClient("key", http=httpx.Client(transport=transport))
    results = client.search("query")
    assert results[0].title == "Tavily"
