import typer
import json

from whoami_llm.extract.velog_rss_description import description_to_text
from whoami_llm.storage.document_store import write_documents
from whoami_llm.velog.rss import fetch_posts, extract_username
from whoami_llm.storage.jsonl_store import save_posts, posts_file

app = typer.Typer()


def _load_posts_from_file(pfile):
    posts = []
    with open(pfile, "r", encoding="utf-8") as f:
        for line in f:
            posts.append(json.loads(line))
    return posts


def _extract_docs_from_posts(posts, min_chars: int):
    docs: list[dict] = []
    warn_count = 0

    for i, p in enumerate(posts, start=1):
        title = p.get("title")
        url = p.get("link")
        published = p.get("pub_date")
        desc = p.get("description")

        text = description_to_text(desc)
        char_count = len(text)

        if char_count < min_chars:
            warn_count += 1
            typer.echo(f"[warn] [{i}/{len(posts)}] Short text ({char_count} chars): {url}")

        docs.append(
            {
                "source": "rss_description",
                "url": url,
                "title": title,
                "published": published,
                "text": text,
                "char_count": char_count,
            }
        )

        typer.echo(f"[{i}/{len(posts)}] Extracted {char_count:,} chars from RSS description.")

    return docs, warn_count


@app.command()
def ingest(blog: str = typer.Option(..., "--blog")):
    typer.echo("🔎 Fetching Velog posts...")
    posts = fetch_posts(blog)
    username = extract_username(blog)

    typer.echo(f"Found {len(posts)} posts.")
    path = save_posts(username, posts)
    typer.echo(f"Saved -> {path}")


@app.command()
def extract(
    blog: str = typer.Option(..., "--blog"),
    limit: int = typer.Option(0, "--limit", help="0이면 전부, 아니면 상위 N개만 처리"),
    min_chars: int = typer.Option(800, "--min-chars", help="description 텍스트 최소 길이 경고 기준"),
):
    username = extract_username(blog)
    pfile = posts_file(username)

    if not pfile.exists():
        raise typer.BadParameter(f"posts file not found: {pfile}. Run ingest first.")

    posts = _load_posts_from_file(pfile)
    if limit > 0:
        posts = posts[:limit]

    typer.echo(f"Building documents from RSS descriptions: {len(posts)} posts")
    docs, warn_count = _extract_docs_from_posts(posts, min_chars=min_chars)

    out = write_documents(username, docs)
    typer.echo(f"Saved -> {out}")
    if warn_count:
        typer.echo(f"Warnings: {warn_count} posts had text shorter than {min_chars} chars.")


@app.command()
def build(
    blog: str = typer.Option(..., "--blog"),
    limit: int = typer.Option(0, "--limit", help="0이면 전부, 아니면 상위 N개만 처리"),
    min_chars: int = typer.Option(800, "--min-chars", help="description 텍스트 최소 길이 경고 기준"),
):
    """
    One-shot: ingest + extract
    """
    # 1) ingest (RSS fetch -> posts.jsonl)
    typer.echo("🔎 Fetching Velog posts...")
    posts = fetch_posts(blog)
    username = extract_username(blog)

    typer.echo(f"Found {len(posts)} posts.")
    ppath = save_posts(username, posts)
    typer.echo(f"Saved -> {ppath}")

    # 2) extract (posts -> documents.jsonl)
    if limit > 0:
        posts_dicts = [p.__dict__ for p in posts[:limit]]
    else:
        posts_dicts = [p.__dict__ for p in posts]

    typer.echo(f"Building documents from RSS descriptions: {len(posts_dicts)} posts")
    docs, warn_count = _extract_docs_from_posts(posts_dicts, min_chars=min_chars)

    out = write_documents(username, docs)
    typer.echo(f"Saved -> {out}")
    if warn_count:
        typer.echo(f"Warnings: {warn_count} posts had text shorter than {min_chars} chars.")


if __name__ == "__main__":
    app()
