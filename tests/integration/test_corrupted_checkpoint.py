from pathlib import Path

import aiosqlite
import pyarrow as pa
import pytest

from core.state import Outline, State
from persistence.manager import PersistenceManager


@pytest.mark.asyncio
async def test_corrupted_checkpoint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Restoring a corrupted document blob should raise an error."""
    for key in ("OPENAI_API_KEY", "PERPLEXITY_API_KEY", "MODEL_NAME"):
        monkeypatch.setenv(key, "x")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))

    pm = PersistenceManager()
    state = State(prompt="p", outline=Outline(steps=["a"]))
    await pm.checkpoint(state, state.outline)

    async with aiosqlite.connect(tmp_path / "checkpoint.db") as conn:
        await conn.execute(
            "UPDATE documents SET parquet_blob = X'00' WHERE state_id = ?",
            (state.version,),
        )
        await conn.commit()

    with pytest.raises(pa.lib.ArrowInvalid):
        await pm.restore(state.version)
