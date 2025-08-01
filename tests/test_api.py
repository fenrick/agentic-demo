from fastapi.testclient import TestClient
from unittest.mock import patch

from app.api import app
from app.agents import ChatAgent


def test_chat_endpoint():
    client = TestClient(app)
    with patch.object(ChatAgent, "__call__", return_value="ok"):
        response = client.post('/chat', params={'input': 'topic'})
    assert response.status_code == 200
    data = response.json()
    assert data == {"response": "ok"}
