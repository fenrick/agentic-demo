import pathlib


def test_dockerfile_configuration():
    path = pathlib.Path('Dockerfile')
    assert path.exists(), 'Dockerfile should exist'
    contents = path.read_text()
    lines = [line.strip() for line in contents.splitlines() if line.strip()]
    assert lines[0] == 'FROM python:3-slim'
    assert any(line.startswith('CMD ') and 'uvicorn' in line and 'app.api:app' in line for line in lines)
