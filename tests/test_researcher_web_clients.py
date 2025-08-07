import json

import httpx

from agents.researcher_web import PerplexityClient, TavilyClient


def test_perplexity_client_parses_response():
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:  # pragma: no cover - simple handler
        assert request.url.path == "/search"
        data = {
            "search_results": [
                {"url": "https://example.com", "snippet": "snippet", "title": "title"}
            ]
        }
        return httpx.Response(200, json=data)

    transport = httpx.MockTransport(handler)
    client = PerplexityClient("key", http=httpx.Client(transport=transport))
    results = client.search("query")
    assert results[0].url == "https://example.com"


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
