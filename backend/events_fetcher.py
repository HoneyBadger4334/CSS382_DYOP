import hashlib
import logging
import re
from datetime import datetime, timezone

import feedparser
import httpx

logger = logging.getLogger(__name__)

RSS_FEEDS = [
    "https://www.trumba.com/calendars/bot_studentlife.rss",
    "https://www.trumba.com/calendars/bot_campus.rss",
]

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "technology": ["tech", "code", "coding", "hackathon", "software", "computer", "cyber",
                   "ai", "ml", "data", "web", "dev", "programming", "react", "python"],
    "science":    ["science", "biology", "chemistry", "physics", "research", "lab",
                   "astronomy", "environment", "ecology", "stem"],
    "business":   ["business", "entrepreneur", "startup", "finance", "career", "resume",
                   "interview", "networking", "job", "internship", "leadership", "accounting"],
    "arts":       ["art", "music", "film", "gallery", "performance", "theater", "creative",
                   "design", "photography", "exhibition", "open mic", "dance", "poetry"],
    "health":     ["health", "wellness", "mental", "meditation", "mindfulness", "fitness",
                   "nutrition", "therapy", "counseling", "stress", "de-stress", "yoga"],
    "sports":     ["sport", "soccer", "basketball", "volleyball", "intramural",
                   "recreation", "athletic", "hiking", "outdoor"],
}

BUILDING_ALIASES: dict[str, str] = {
    "library": "LIB",
    "lb1":     "LIB",
    "uw1":     "UW1",
    "uw2":     "UW2",
    "discovery hall": "DISC",
    "discovery": "DISC",
    "stem":    "STEM",
    "arc":     "ARC",
    "activities and recreation": "ARC",
    "husky hall": "HH",
    "north creek": "NCH",
    "summit":  "UW1",
}

_METADATA_MARKERS = (
    "event interval", "campus room", "location type", "online meeting link",
    "event sponsors", "accessibility contact", "event types", "uw bothell event types",
)


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;|&#8239;", " ", text)
    text = re.sub(r"&ndash;|&#8211;", "–", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&#\d+;", "", text)
    text = re.sub(r"&[a-z]+;", "", text)
    return re.sub(r" {2,}", " ", text).strip()


_DATE_HEADER = re.compile(
    r"(?:virtual|zoom[^.!?\n]*?)?\s*"
    r"(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday),\s+"
    r"[a-z]+\.?\s+\d{1,2},\s+\d{4}.*?(?:pdt|pst)\s*",
    re.IGNORECASE,
)


def _parse_description(html: str) -> tuple[str, str]:
    """
    Returns (description, url) extracted from the Trumba RSS description HTML.
    Strips leading location/datetime lines since those are shown separately on the card.
    """
    plain = _strip_html(html)

    # Extract registration/Handshake URL before stripping HTML
    url_match = re.search(r"https?://uw\.joinhandshake\.com\S+", html)
    url = url_match.group(0).rstrip("&gt;") if url_match else None

    # Also grab the UWB calendar event link as fallback
    if not url:
        uwb_match = re.search(r"https?://www\.uwb\.edu/calendar[^\s\"<]+", html)
        url = uwb_match.group(0) if uwb_match else None

    # Strip leading location/datetime header that Trumba prepends (already shown on card)
    plain = _DATE_HEADER.sub("", plain, count=1).strip()

    # Stop at metadata section
    for marker in _METADATA_MARKERS:
        idx = plain.lower().find(marker)
        if idx != -1:
            plain = plain[:idx].strip()

    # Stop at registration link line
    for stop in ("registration link", "register in handshake", "register here"):
        idx = plain.lower().find(stop)
        if idx != -1:
            plain = plain[:idx].strip()

    description = re.sub(r"\s{2,}", " ", plain)[:250].strip()
    return description, url


def _infer_category(title: str, description: str) -> str:
    text = (title + " " + description).lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return category
    return "social"


def _normalize_building(location: str) -> str:
    if not location:
        return "CAMPUS"
    loc_lower = location.lower()
    for alias, code in BUILDING_ALIASES.items():
        if alias in loc_lower:
            return code
    return "CAMPUS"


_DATE_PATTERN = re.compile(
    r"\b(January|February|March|April|May|June|July|August|September|October|November|December)"
    r"\s+(\d{1,2}),\s+(\d{4})\b"
)


def _parse_date(entry) -> datetime | None:
    # Trumba RSS entries have no published field — date is inside the description HTML
    raw = entry.get("summary", "") or entry.get("description", "")
    plain = _strip_html(raw)
    match = _DATE_PATTERN.search(plain)
    if match:
        try:
            return datetime.strptime(f"{match.group(1)} {match.group(2)} {match.group(3)}", "%B %d %Y").replace(tzinfo=timezone.utc)
        except Exception:
            pass
    return None


def _parse_feed(feed_text: str) -> list[dict]:
    events: list[dict] = []
    now = datetime.now(timezone.utc)

    parsed = feedparser.parse(feed_text)
    for entry in parsed.entries:
        try:
            dt = _parse_date(entry)
            if dt is None or dt < now:
                continue

            title = entry.get("title", "Untitled Event")
            raw_desc = entry.get("description", "") or entry.get("summary", "")
            description, reg_url = _parse_description(raw_desc)

            # Use registration link if available, else fall back to entry link
            url = reg_url or entry.get("link") or None

            # Extract location from first non-empty line of stripped description
            first_line_match = re.search(r"^(.+?)(?:<br|\\n|\n)", raw_desc)
            location = _strip_html(first_line_match.group(1)) if first_line_match else ""
            building = _normalize_building(location)

            uid = entry.get("id") or entry.get("link") or (title + dt.isoformat())
            event_id = "live-" + hashlib.md5(uid.encode()).hexdigest()[:10]

            events.append({
                "id":          event_id,
                "title":       title,
                "category":    _infer_category(title, description),
                "building":    building,
                "date":        dt.strftime("%b %d, %Y"),
                "description": description or "Click ↗ details to view on the UWB events calendar.",
                "url":         url,
            })
        except Exception as e:
            logger.debug("Skipping malformed entry: %s", e)

    return events


def fetch_live_events(limit: int = 200) -> tuple[list[dict], bool]:
    """
    Fetch both Trumba RSS feeds and return deduplicated future events.
    Returns (events, feed_ok).
    """
    seen: set[str] = set()
    all_events: list[dict] = []
    any_ok = False

    for url in RSS_FEEDS:
        try:
            resp = httpx.get(url, timeout=10, follow_redirects=True)
            resp.raise_for_status()
            parsed = _parse_feed(resp.text)
            for event in parsed:
                if event["id"] not in seen:
                    seen.add(event["id"])
                    all_events.append(event)
            any_ok = True
            logger.info("Fetched %d events from %s", len(parsed), url)
        except Exception as e:
            logger.error("Failed to fetch %s: %s", url, e)

    all_events.sort(key=lambda e: e["date"])
    return all_events[:limit], any_ok
