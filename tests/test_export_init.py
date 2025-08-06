from export import EXPORTERS, MarkdownExporter


def test_exporters_registry_contains_markdown():
    assert EXPORTERS["markdown"] is MarkdownExporter
