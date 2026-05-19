import feedparser
import hashlib
from datetime import datetime, timezone
from typing import Optional

UW_ALERTS_RSS = "https://www.washington.edu/alert/feed/"

# Sample alerts used when the live RSS feed returns nothing or errors.
SEED_ALERTS = [
    {
        "id": "seed-001",
        "raw_text": "Police activity near UW1, avoid the area and seek shelter immediately.",
        "published": "2026-05-18T10:00:00Z",
    },
    {
        "id": "seed-002",
        "raw_text": "All-clear: The earlier police activity near UW1 has been resolved. Normal operations may resume.",
        "published": "2026-05-18T11:30:00Z",
    },
]


def fetch_alerts(use_seed_on_empty: bool = True) -> tuple[list[dict], bool]:
    """
    Returns (alerts, feed_ok).
    Each alert dict has: id, raw_text, published.
    feed_ok is False if the live feed was unreachable.
    """
    try:
        feed = feedparser.parse(UW_ALERTS_RSS)
        if feed.bozo and not feed.entries:
            raise ValueError("Feed parse error")

        alerts = []
        for entry in feed.entries:
            text = entry.get("summary") or entry.get("title") or ""
            if entry.get("title") and entry.get("summary"):
                text = f"{entry['title']}. {entry['summary']}"
            entry_id = hashlib.md5(text.encode()).hexdigest()[:12]
            published = entry.get("published", datetime.now(timezone.utc).isoformat())
            alerts.append({"id": entry_id, "raw_text": text, "published": published})

        if not alerts and use_seed_on_empty:
            return SEED_ALERTS, True
        return alerts, True

    except Exception:
        if use_seed_on_empty:
            return SEED_ALERTS, False
        return [], False
