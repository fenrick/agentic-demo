# Module Overview

This document summarises the foundational modules that were recently
introduced.

## Core

- `core.Agent` – abstract base class that defines the agent interface.
- `core.AgentError` – base exception type for agent failures.
- `core.get_logger` – helper returning a configured `logging.Logger`.

## Agents

- `agents.EchoAgent` – echoes input text without modification.
- `agents.ReverseAgent` – reverses text input for demonstration purposes.

## Export

The `export` package exposes concrete export utilities through the
`EXPORTERS` registry mapping format names to implementations:

 - `markdown` and `pdf` map to exporter classes.
 - `metadata` maps to the `export_citations_json` function that serialises
   citation metadata to JSON.
