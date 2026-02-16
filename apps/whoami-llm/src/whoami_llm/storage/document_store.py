from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from whoami_llm.storage.jsonl_store import ensure_data_dir


def documents_file(username: str) -> Path:
    data_dir = ensure_data_dir()
    safe = username.strip().lstrip("@")
    return data_dir / f"{safe}_documents.jsonl"


def write_documents(username: str, docs: Iterable[dict]) -> Path:
    """
    documents.jsonl을 '덮어쓰기'로 생성한다 (Phase 2 결과물).
    """
    path = documents_file(username)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        for d in docs:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")

    return path
