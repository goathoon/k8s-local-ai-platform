from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Iterable

from whoami_llm.velog.models import VelogPost

ENV_HOME = "WHOAMI_LLM_HOME"
DEFAULT_DIRNAME = ".whoami_llm"


def get_data_dir() -> Path:
    """
    Data dir resolution priority:
    1) WHOAMI_LLM_HOME env var
    2) ~/.whoami_llm (default)

    Returns a Path (does not create it).
    """
    env = os.getenv(ENV_HOME)
    if env and env.strip():
        return Path(env).expanduser().resolve()
    return (Path.home() / DEFAULT_DIRNAME).resolve()


def ensure_data_dir() -> Path:
    """
    Ensures the data directory exists and returns it.
    """
    data_dir = get_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def posts_file(username: str) -> Path:
    """
    Returns the path to the posts jsonl file for a velog username.
    """
    data_dir = ensure_data_dir()
    safe = username.strip().lstrip("@")
    return data_dir / f"{safe}_posts.jsonl"


def save_posts(username: str, posts: Iterable[VelogPost]) -> Path:
    """
    Saves posts as JSON Lines (one JSON object per line).
    Uses atomic replace to avoid partial/corrupted files on crash.
    """
    target = posts_file(username)
    target.parent.mkdir(parents=True, exist_ok=True)

    # Write to temp file first, then atomic replace
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        delete=False,
        dir=str(target.parent),
        prefix=target.name + ".",
        suffix=".tmp",
    ) as tmp:
        tmp_path = Path(tmp.name)

        for p in posts:
            # dataclass -> dict; fallback for non-dataclass objects
            obj = getattr(p, "__dict__", None) or {
                "title": getattr(p, "title", None),
                "link": getattr(p, "link", None),
                "pub_date": getattr(p, "pub_date", None),
                "description": getattr(p, "description", None),
            }
            tmp.write(json.dumps(obj, ensure_ascii=False) + "\n")

    tmp_path.replace(target)
    return target
