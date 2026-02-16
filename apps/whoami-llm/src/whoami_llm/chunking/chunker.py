from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Iterator, Optional


_WORD_RE = re.compile(r"\w+|[^\w\s]", re.UNICODE)


def _try_get_tiktoken_encoder():
    try:
        import tiktoken  # type: ignore
        print("Using tiktoken for token counting.")
        return tiktoken.get_encoding("cl100k_base")
    except Exception:
        print("tiktoken not available, falling back to rough token counting.")
        return None


_ENCODER = _try_get_tiktoken_encoder()


def count_tokens(text: str) -> int:
    """
    Prefer tiktoken if available; otherwise fallback to a rough tokenizer.
    """
    if _ENCODER is not None:
        return len(_ENCODER.encode(text))
    # fallback: word+punct tokens (rough)
    return len(_WORD_RE.findall(text))


def split_to_token_units(text: str) -> list[str]:
    """
    Returns units that we can join back. If tiktoken exists, use token ids,
    but we still need reconstructable units; so we fallback to rough units.
    (In practice, chunk boundaries are what matter; exact detokenization isn't required.)
    """
    # We keep it simple & robust: use rough units always for splitting.
    # count_tokens() will be more accurate if tiktoken is available.
    return _WORD_RE.findall(text)


def join_units(units: list[str]) -> str:
    # Reconstruct with minimal spacing rules:
    out = []
    for u in units:
        if not out:
            out.append(u)
            continue
        # no space before punctuation
        if re.match(r"^[^\w\s]$", u):
            out.append(u)
        # no space after opening brackets
        elif out[-1] in ("(", "[", "{", "“", "‘"):
            out.append(u)
        else:
            out.append(" " + u)
    return "".join(out)


@dataclass(frozen=True)
class ChunkConfig:
    target_tokens: int = 700       # 500~800 사이 권장
    overlap_tokens: int = 100      # 권장
    min_tokens: int = 200          # 너무 작은 찌꺼기 chunk 방지


def chunk_text(text: str, cfg: ChunkConfig) -> list[str]:
    """
    Chunk by rough units but enforce token-like sizing using count_tokens().
    """
    units = split_to_token_units(text)
    chunks: list[str] = []

    start = 0
    n = len(units)

    # Helper: advance end until token count exceeds target
    while start < n:
        end = start
        # Greedy expand
        while end < n:
            candidate = join_units(units[start:end + 1])
            if count_tokens(candidate) > cfg.target_tokens:
                break
            end += 1

        # If we couldn't add even 1 unit without exceeding, force 1
        if end == start:
            end = min(start + 1, n)

        chunk = join_units(units[start:end])
        chunks.append(chunk)

        # next start with overlap
        if end >= n:
            break

        # Move start forward but keep overlap
        # We'll approximate overlap by moving back from end until overlap_tokens satisfied
        next_start = end
        if cfg.overlap_tokens > 0:
            back = end
            # move back until overlap reached (by tokens)
            while back > start:
                overlap_text = join_units(units[back:end])
                if count_tokens(overlap_text) >= cfg.overlap_tokens:
                    break
                back -= 1
            next_start = back

        # Prevent infinite loop
        if next_start <= start:
            next_start = end

        start = next_start

    # Merge last tiny chunk into previous if too small
    if len(chunks) >= 2 and count_tokens(chunks[-1]) < cfg.min_tokens:
        chunks[-2] = chunks[-2].rstrip() + "\n\n" + chunks[-1].lstrip()
        chunks.pop()

    return chunks
