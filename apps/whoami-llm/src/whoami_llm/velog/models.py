from dataclasses import dataclass


@dataclass(frozen=True)
class VelogPost:
    title: str
    link: str
    pub_date: str | None = None
    description: str | None = None
