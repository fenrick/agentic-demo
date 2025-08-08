"""Data entry endpoints for storing and retrieving submissions."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class EntryCreate(BaseModel):
    """Payload for creating a new entry."""

    topic: str


class Entry(EntryCreate):
    """Entry representation returned by the API."""

    id: int


_entries: list[Entry] = []


@router.get("/entries", response_model=list[Entry])
async def list_entries() -> list[Entry]:
    """Return all submitted entries."""

    return _entries


@router.post("/entries", response_model=Entry)
async def create_entry(data: EntryCreate) -> Entry:
    """Store a new entry and return it."""

    entry = Entry(id=len(_entries) + 1, **data.model_dump())
    _entries.append(entry)
    return entry
