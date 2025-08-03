from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ActionLog(BaseModel):
    agent: str
    input_hash: str
    output_hash: str
    tokens: int
    cost: float
    timestamp: datetime

class Citation(BaseModel):
    url: str
    title: str
    retrieved_at: datetime
    licence: str

class Outline(BaseModel):
    sections: List[str]
    # extend with slide bullets, notes, etc.
