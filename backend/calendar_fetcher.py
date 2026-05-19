from __future__ import annotations

import hashlib
import html as html_module
import re
from datetime import date, datetime, time as time_cls, timedelta, timezone
from typing import Optional
from urllib.parse import unquote
from zoneinfo import ZoneInfo

import feedparser

from building_coords import resolve_coordinates

UW_BOTHELL_CALENDAR_RSS = "https://www.trumba.com/calendars/bot_campus.rss"
PACIFIC_TZ = ZoneInfo("America/Los_Angeles")
WINDOW_DAYS = 180

MONTHS = {
    month.lower(): index
    for index, month in enumerate(
        [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ],
        start=1,
    )
}

WEEKDAY_PATTERN = r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)"
DATE_PATTERN = r"(?:January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2}(?:, \d{4})?"
DATE_RE = re.compile(rf"(?P<month>{DATE_PATTERN})", re.I)
TIME_RE = re.compile(r"\d{1,2}(?::\d{2})?\s*(?:a\.?m\.?|p\.?m\.?)", re.I)
SCHEDULE_RE = re.compile(
    rf"<br\s*/>\s*(?P<schedule>{WEEKDAY_PATTERN}.*?)(?=<br\s*/><br\s*/>|<b>Event interval</b>|<b>Campus location</b>|<b>Location Type</b>|<b>Target Audience</b>|<b>Event Types</b>|</description>|$)",
    re.I | re.S,
)
FIELD_RE_TEMPLATE = r"<b>{label}</b>:\s*&nbsp;(?P<value>.*?)(?=(?:<br\s*/>\s*)?<b>|</description>|$)"
METADATA_SPLIT_RE = re.compile(
    r"<b>Event interval</b>|<b>Campus location</b>|<b>Campus room</b>|<b>Location Type</b>|<b>UW Bothell Event types</b>|<b>Event Types</b>|<b>Target Audience</b>|<b>Accessibility Contact</b>|<b>Event sponsors</b>|<b>More info</b>|</description>",
    re.I,
)
POSITIVE_AUDIENCE_HINTS = (
    "student",
    "students",
    "prospective",
    "campus community",
    "general public",
    "all are welcome",
    "open to all",
    "everyone",
    "undergraduate",
    "graduate",
)
STAFF_ONLY_HINTS = (
    "staff and faculty",
    "faculty and staff",
)
TITLE_HINTS: tuple[tuple[str, str], ...] = (
    ("campus tour", "Campus Tour"),
    ("study abroad", "Study Abroad"),
    ("springfest", "SpringFest"),
    ("grad fair", "Grad Fair"),
    ("free market", "Free Market"),
    ("block party", "Block Party"),
    ("career development", "Career Development"),
    ("transfer application", "Transfer Application"),
    ("information session", "Information Session"),
    ("office hours", "Office Hours"),
    ("crafternoon", "Crafternoon"),
    ("yoga", "Yoga"),
    ("pilates", "Pilates"),
    ("hackathon", "Hackathon"),
    ("research poster", "Research"),
    ("commencement", "Commencement"),
)


def _clean_html_fragment(value: str) -> str:
    if not value:
        return ""

    text = re.sub(r"(?i)<br\s*/?>", "\n", value)
    text = re.sub(r"(?i)</(p|div|li|tr|h[1-6])>", "\n", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html_module.unescape(text)
    text = re.sub(r"[\t\r ]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text)
    return text.strip()


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().lower()


def _split_values(value: str) -> list[str]:
    if not value:
        return []

    values = []
    for part in re.split(r",|;|\s\|\s|\s/\s", _clean_html_fragment(value)):
        cleaned = re.sub(r"\s+", " ", part).strip()
        if cleaned:
            values.append(cleaned)

    deduped: list[str] = []
    seen: set[str] = set()
    for item in values:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            deduped.append(item)
    return deduped


def _extract_field_value(raw_html: str, label: str) -> str:
    pattern = re.compile(FIELD_RE_TEMPLATE.format(label=re.escape(label)), re.I | re.S)
    match = pattern.search(raw_html)
    if not match:
        return ""
    return _clean_html_fragment(match.group("value"))


def _extract_schedule_html(raw_html: str) -> str:
    match = SCHEDULE_RE.search(raw_html)
    return match.group("schedule") if match else ""


def _parse_date_token(token: str, fallback_year: int) -> date:
    token = _clean_html_fragment(token)
    match = re.match(r"(?P<month>[A-Za-z]+) (?P<day>\d{1,2})(?:, (?P<year>\d{4}))?", token)
    if not match:
        return date(fallback_year, 1, 1)

    month = MONTHS.get(match.group("month").lower(), 1)
    day = int(match.group("day"))
    year = int(match.group("year")) if match.group("year") else fallback_year
    return date(year, month, day)


def _parse_time_token(token: str) -> time_cls:
    normalized = re.sub(r"\s+", "", token.lower().replace(".", ""))
    match = re.match(r"(?P<hour>\d{1,2})(?::(?P<minute>\d{2}))?(?P<period>am|pm)", normalized)
    if not match:
        return time_cls(9, 0)

    hour = int(match.group("hour"))
    minute = int(match.group("minute") or 0)
    period = match.group("period")

    if hour == 12:
        hour = 0
    if period == "pm":
        hour += 12

    return time_cls(hour, minute)


def _parse_published(raw_value: Optional[str]) -> datetime:
    if not raw_value:
        return datetime.now(PACIFIC_TZ)

    try:
        return datetime.fromisoformat(raw_value.replace("Z", "+00:00")).astimezone(PACIFIC_TZ)
    except Exception:
        return datetime.now(PACIFIC_TZ)


def _parse_schedule_window(schedule_text: str, published_value: Optional[str]) -> tuple[datetime, datetime, bool]:
    now = datetime.now(PACIFIC_TZ)
    fallback_year = _parse_published(published_value).year if published_value else now.year

    date_matches = list(DATE_RE.finditer(schedule_text))
    if date_matches:
        start_date = _parse_date_token(date_matches[0].group("month"), fallback_year)
        end_date = _parse_date_token(date_matches[-1].group("month"), fallback_year)
    else:
        start_date = now.date()
        end_date = now.date()

    time_matches = TIME_RE.findall(schedule_text)
    if time_matches:
        start_time = _parse_time_token(time_matches[0])
        if len(time_matches) > 1:
            end_time = _parse_time_token(time_matches[1])
        else:
            end_time = (datetime.combine(start_date, start_time) + timedelta(hours=1)).time()

        start = datetime.combine(start_date, start_time, tzinfo=PACIFIC_TZ).astimezone(timezone.utc)
        end = datetime.combine(end_date, end_time, tzinfo=PACIFIC_TZ).astimezone(timezone.utc)
        if end <= start:
            end = end + timedelta(days=1)
        return start, end, False

    start = datetime.combine(start_date, time_cls(0, 0), tzinfo=PACIFIC_TZ).astimezone(timezone.utc)
    end = datetime.combine(end_date + timedelta(days=1), time_cls(0, 0), tzinfo=PACIFIC_TZ).astimezone(timezone.utc)
    return start, end, True


def _extract_event_id(entry: dict) -> str:
    candidates = [entry.get("guid"), entry.get("id"), entry.get("link")]
    for candidate in candidates:
        if not candidate:
            continue
        decoded = unquote(str(candidate))
        match = re.search(r"(?:eventid=|event/)(\d+)", decoded)
        if match:
            return f"trumba-{match.group(1)}"

    title = _clean_html_fragment(str(entry.get("title") or "event"))
    return f"trumba-{hashlib.md5(title.encode('utf-8')).hexdigest()[:12]}"


def _extract_campus_location(raw_html: str) -> str:
    location = _extract_field_value(raw_html, "Campus location")
    if location:
        return location

    room = _extract_field_value(raw_html, "Campus room")
    if room:
        return room

    first_line = raw_html.split("<br/>", 1)[0]
    return _clean_html_fragment(first_line)


def _extract_location_type(raw_html: str) -> str:
    return _extract_field_value(raw_html, "Location Type")


def _extract_audience(raw_html: str) -> list[str]:
    audience = _split_values(_extract_field_value(raw_html, "Target Audience"))
    if audience:
        return audience
    return []


def _extract_event_types(raw_html: str) -> list[str]:
    event_types = _split_values(_extract_field_value(raw_html, "UW Bothell Event types"))
    if event_types:
        return event_types
    return _split_values(_extract_field_value(raw_html, "Event Types"))


def _infer_building_name(location_text: str, location_type: str) -> str:
    combined = _normalize_text(" ".join(part for part in [location_text, location_type] if part))
    if not combined or any(term in combined for term in ("zoom", "online", "virtual", "teams", "remote")):
        return "CAMPUS"

    aliases = (
        ("summit hall", "SUMMIT HALL"),
        ("north creek events center", "NCEC"),
        ("ncec", "NCEC"),
        ("founder", "UW1"),
        ("uw1", "UW1"),
        ("founders hall", "UW1"),
        ("discovery hall", "DISC"),
        ("disc", "DISC"),
        ("campus library", "LIB"),
        ("library - lb1", "LIB"),
        ("library", "LIB"),
        ("husky hall", "HH"),
        ("north creek hall", "NCH"),
        ("science and engineering", "STEM"),
        ("stem", "STEM"),
        ("campus activities building", "CAB"),
        ("campus center", "CC"),
    )

    for needle, building_name in aliases:
        if needle in combined:
            return building_name

    return "CAMPUS"


def _normalize_tag(value: str) -> str:
    return _clean_html_fragment(value)


def _infer_tags(title: str, event_types: list[str], audience: list[str], location_type: str, body_text: str) -> list[str]:
    tags: list[str] = []
    combined = _normalize_text(" ".join([title, location_type, body_text, *event_types, *audience]))

    for needle, label in TITLE_HINTS:
        if needle in combined:
            tags.append(label)

    for value in [location_type, *event_types, *audience]:
        normalized = _normalize_tag(value)
        if normalized:
            tags.append(normalized)

    if not tags:
        tags.append("Campus Event")

    deduped: list[str] = []
    seen: set[str] = set()
    for tag in tags:
        key = tag.lower()
        if key not in seen:
            seen.add(key)
            deduped.append(tag)

    return deduped[:8]


def _infer_audience(title: str, audience: list[str]) -> list[str]:
    if audience:
        return audience

    normalized_title = _normalize_text(title)
    student_hints = (
        "campus tour",
        "study abroad",
        "springfest",
        "grad fair",
        "free market",
        "block party",
        "career development",
        "transfer application",
        "information session",
        "crafternoon",
        "yoga",
        "pilates",
        "commencement",
        "hackathon",
        "research poster",
    )
    if any(hint in normalized_title for hint in student_hints):
        return ["All students"]

    if "faculty" in normalized_title or "staff" in normalized_title:
        return ["Campus community"]

    return ["Campus community"]


def _should_include_event(title: str, audience: list[str], event_types: list[str], location_type: str) -> bool:
    combined = _normalize_text(" ".join([title, location_type, " ".join(event_types), " ".join(audience)]))

    if any(hint in combined for hint in STAFF_ONLY_HINTS) and not any(hint in combined for hint in POSITIVE_AUDIENCE_HINTS):
        return False

    if any(hint in combined for hint in POSITIVE_AUDIENCE_HINTS):
        return True

    if any(
        hint in combined
        for hint in (
            "campus tour",
            "study abroad",
            "springfest",
            "grad fair",
            "free market",
            "block party",
            "career",
            "student activities",
            "community engagement",
            "special events",
            "information sessions",
            "workshops",
            "commencement",
            "crafternoon",
            "yoga",
            "pilates",
            "hackathon",
            "transfer application",
            "open studio",
        )
    ):
        return True

    if "office hours" in combined and not any(hint in combined for hint in ("student", "students", "campus community", "general public")):
        return False

    return False


def _truncate(value: str, limit: int = 240) -> str:
    text = _clean_html_fragment(value)
    if len(text) <= limit:
        return text
    shortened = text[: limit - 3].rsplit(" ", 1)[0]
    return f"{shortened}..."


def _build_event_dict(entry: dict) -> Optional[dict[str, object]]:
    raw_title = str(entry.get("title") or "").strip()
    raw_html = str(entry.get("description") or entry.get("summary") or "")
    schedule_html = _extract_schedule_html(raw_html)
    schedule_text = _clean_html_fragment(schedule_html)
    location_text = _extract_campus_location(raw_html)
    location_type = _extract_location_type(raw_html)
    event_types = _extract_event_types(raw_html)
    audience = _infer_audience(raw_title, _extract_audience(raw_html))

    if not _should_include_event(raw_title, audience, event_types, location_type):
        return None

    published_value = str(entry.get("published") or "") or None
    start_time, end_time, all_day = _parse_schedule_window(schedule_text or location_text or raw_title, published_value)

    body_html = raw_html
    if schedule_html:
        schedule_match = SCHEDULE_RE.search(raw_html)
        if schedule_match:
            body_html = raw_html[schedule_match.end():]
    body_html = METADATA_SPLIT_RE.split(body_html, maxsplit=1)[0]
    description = _truncate(body_html or raw_html)
    if not description:
        description = raw_title

    building_name = _infer_building_name(location_text, location_type)
    category = event_types[0] if event_types else (location_type or "Campus Event")
    tags = _infer_tags(raw_title, event_types, audience, location_type, description)

    return {
        "id": _extract_event_id(entry),
        "title": _clean_html_fragment(raw_title),
        "description": description,
        "building_name": building_name,
        "coordinates": list(resolve_coordinates(building_name)),
        "category": category,
        "tags": tags,
        "audience": audience,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "schedule_text": schedule_text or _clean_html_fragment(location_text) or _clean_html_fragment(raw_title),
        "all_day": all_day,
    }


def fetch_calendar_events(limit: int = 60) -> list[dict[str, object]]:
    feed = feedparser.parse(UW_BOTHELL_CALENDAR_RSS)
    events: list[dict[str, object]] = []
    seen_ids: set[str] = set()

    now = datetime.now(PACIFIC_TZ)
    lower_bound = now - timedelta(days=7)
    upper_bound = now + timedelta(days=WINDOW_DAYS)

    for entry in feed.entries:
        event_dict = _build_event_dict(entry)
        if not event_dict:
            continue

        event_id = str(event_dict["id"])
        if event_id in seen_ids:
            continue
        seen_ids.add(event_id)

        try:
            start_time = datetime.fromisoformat(str(event_dict["start_time"]))
        except Exception:
            start_time = now

        if start_time < lower_bound.astimezone(timezone.utc) or start_time > upper_bound.astimezone(timezone.utc):
            continue

        events.append(event_dict)

    events.sort(key=lambda item: (str(item["start_time"]), str(item["title"])))
    return events[:limit]