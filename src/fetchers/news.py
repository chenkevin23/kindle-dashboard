"""RSS news fetcher — parses feeds via feedparser."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import feedparser

from src.config import settings

logger = logging.getLogger(__name__)


@dataclass
class NewsItem:
    title: str
    source: str     # feed name, e.g. "TechCrunch"
    url: str = ""


def _truncate(text: str, max_len: int = 72) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def fetch_news() -> list[NewsItem]:
    """Fetch top headlines from configured RSS feeds."""
    feeds = settings.get_rss_feeds()
    items: list[NewsItem] = []

    per_feed = max(2, settings.max_news // len(feeds)) if feeds else 0

    for feed_config in feeds:
        name = feed_config.get("name", "Unknown")
        url = feed_config.get("url", "")
        if not url:
            continue

        try:
            parsed = feedparser.parse(url)
            if parsed.bozo and not parsed.entries:
                logger.warning(f"RSS parse error for {name}: {parsed.bozo_exception}")
                continue

            for entry in parsed.entries[:per_feed]:
                title = entry.get("title", "").strip()
                link = entry.get("link", "")
                if title:
                    items.append(NewsItem(
                        title=_truncate(title),
                        source=name.upper(),
                        url=link,
                    ))

        except Exception as e:
            logger.warning(f"Failed to fetch RSS {name}: {e}")
            continue

    logger.info(f"Fetched {len(items)} news items from {len(feeds)} feeds")
    return items[: settings.max_news]
