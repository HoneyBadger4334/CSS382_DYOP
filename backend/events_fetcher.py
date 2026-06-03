import hashlib
import logging
import re
from datetime import datetime, timezone

import httpx
from icalendar import Calendar

logger = logging.getLogger(__name__)

ICAL_FEEDS = [
    "https://www.trumba.com/calendars/bot_studentlife.ics",
    "https://www.trumba.com/calendars/bot_campus.ics",
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


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&[a-z]+;", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _parse_feed(ical_text: str) -> list[dict]:
    events: list[dict] = []
    now = datetime.now(timezone.utc)

    try:
        cal = Calendar.from_ical(ical_text)
    except Exception as e:
        logger.error("Failed to parse iCal content: %s", e)
        return events

    for component in cal.walk():
        if component.name != "VEVENT":
            continue
        try:
            dtstart = component.get("DTSTART")
            if dtstart is None:
                continue

            dt = dtstart.dt
            if not hasattr(dt, "hour"):
                dt = datetime(dt.year, dt.month, dt.day, tzinfo=timezone.utc)
            elif dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)

            if dt < now:
                continue

            uid = str(component.get("UID", ""))
            event_id = "live-" + hashlib.md5(uid.encode()).hexdigest()[:10]

            title = str(component.get("SUMMARY", "Untitled Event"))
            location = str(component.get("LOCATION", "") or "")
            raw_desc = str(component.get("DESCRIPTION", "") or "")
            description = _strip_html(raw_desc)[:200]

            events.append({
                "id":          event_id,
                "title":       title,
                "category":    _infer_category(title, description),
                "building":    _normalize_building(location),
                "date":        dt.strftime("%b %d, %Y"),
                "description": description or "See UWB events calendar for details.",
            })
        except Exception as e:
            logger.debug("Skipping malformed VEVENT: %s", e)

    return events


def fetch_live_events(limit: int = 60) -> tuple[list[dict], bool]:
    """
    Fetch both Trumba iCal feeds and return deduplicated future events.
    Returns (events, feed_ok).
    """
    seen: set[str] = set()
    all_events: list[dict] = []
    any_ok = False

    for url in ICAL_FEEDS:
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
