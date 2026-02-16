import typer

from whoami_llm.velog.rss import fetch_posts, extract_username
from whoami_llm.storage.jsonl_store import save_posts

app = typer.Typer()


@app.command()
def ingest(blog: str = typer.Option(..., "--blog")):
    """
    Velog -> RSS -> posts.jsonl 저장
    """

    typer.echo("🔎 Fetching Velog posts...")
    posts = fetch_posts(blog)
    username = extract_username(blog)

    typer.echo(f"Found {len(posts)} posts.")

    path = save_posts(username, posts)
    typer.echo(f"Saved -> {path}")


if __name__ == "__main__":
    app()
