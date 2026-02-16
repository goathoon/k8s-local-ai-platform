from urllib.parse import urlparse
import feedparser
import requests

from .models import VelogPost


def extract_username(blog: str) -> str:
    blog = blog.strip()

    if blog.startswith("@"):
        return blog[1:]

    if blog.startswith("http"):
        u = urlparse(blog)
        parts = [p for p in u.path.split("/") if p]
        head = parts[0]
        if head.startswith("@"):
            return head[1:]
        return head

    return blog


def find_rss(username: str) -> str:
    candidates = [
        f"https://v2.velog.io/rss/{username}",
        f"https://v2.velog.io/rss/@{username}",
    ]

    for url in candidates:
        r = requests.get(url, timeout=5)
        if r.status_code == 200 and "<rss" in r.text.lower():
            return url

    raise RuntimeError("Velog RSS not found")


def fetch_posts(blog: str) -> list[VelogPost]:
    username = extract_username(blog)
    rss_url = find_rss(username)

    feed = feedparser.parse(rss_url)

    posts = []
    for e in feed.entries:
        posts.append(
            VelogPost(
                title=e.title,
                link=e.link,
                pub_date=e.get("published") or e.get("pubDate"),
                description=getattr(e, "description", None),
            )
        )

    return posts
