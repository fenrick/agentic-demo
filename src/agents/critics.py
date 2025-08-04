"""Critic nodes for pedagogy and factual accuracy."""

from __future__ import annotations

from models import CritiqueReport, FactCheckReport

from .fact_checker import run_fact_checker
from .pedagogy_critic import run_pedagogy_critic

__all__ = [
    "run_pedagogy_critic",
    "run_fact_checker",
    "CritiqueReport",
    "FactCheckReport",
]
