from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from whoami_llm.storage.jsonl_store import ensure_data_dir


def chunks_file(username: str) -> Path:
    data_dir = ensure_data_dir()
    safe = username.strip().lstrip("@")
    return data_dir / f"{safe}_chunks.jsonl"


def write_chunks(username: str, rows: Iterable[dict]) -> Path:
    path = chunks_file(username)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    return path
