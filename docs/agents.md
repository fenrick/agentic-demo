# Agents

This project favors large language model (LLM) processing for all language
interpretation tasks. Agents rely on LLMs to classify, critique and generate
content rather than simple keyword heuristics.

The pedagogy critic, for example, prompts an LLM to map learning objectives to
Bloom's taxonomy levels. If an LLM is unavailable the agent falls back to a
lightweight keyword lookup, but high-quality runs should prefer the LLM path.
