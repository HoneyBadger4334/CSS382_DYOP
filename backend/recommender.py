from __future__ import annotations

import hashlib
import json
import math
import os
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from itertools import combinations
from threading import Lock
from typing import List, Literal, Optional, Tuple

from openai import OpenAI
from pydantic import BaseModel, ConfigDict

from calendar_fetcher import fetch_calendar_events

AI_RECOMMENDER_MODEL = os.getenv("CAMPUS_PULSE_RECOMMENDER_MODEL", "gpt-4o-mini")
AI_RECOMMENDER_TARGET_MAJOR = os.getenv("CAMPUS_PULSE_RECOMMENDER_MAJOR", "computer science")
AI_RECOMMENDER_ENABLED = os.getenv("CAMPUS_PULSE_DISABLE_AI_RECOMMENDER", "0") != "1"

GLOBAL_ACTIVATION_THRESHOLD = 50
USER_ACTIVATION_THRESHOLD = 10
DEFAULT_LIMIT = 6
GRACE_PERIOD_DAYS = 14

INTERACTION_WEIGHTS: dict[str, float] = {
    "view": 1.0,
    "click": 2.25,
    "save": 4.0,
}

InteractionType = Literal["view", "click", "save"]


class EventCard(BaseModel):
    id: str
    title: str
    description: str
    building_name: str
    coordinates: List[float]
    category: str
    tags: List[str]
    audience: List[str]
    start_time: str
    end_time: str


class RecommendationCard(EventCard):
    rank: int
    score: float
    why: str
    ai_score: float
    matched_keywords: List[str]


class RecommendationResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    user_token_hash: str
    major: Optional[str]
    major_source: str
    mode: str
    model_ready: bool
    grace_period_active: bool
    global_interaction_count: int
    user_interaction_count: int
    ai_available: bool
    ai_target_major: str
    fallback_reason: Optional[str] = None
    generated_at: str
    recommendations: List[RecommendationCard]


class InteractionRequest(BaseModel):
    user_token: str
    event_id: str
    interaction_type: InteractionType
    major: Optional[str] = None


class InteractionResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    accepted: bool
    user_token_hash: str
    event_id: str
    interaction_type: InteractionType
    global_interaction_count: int
    user_interaction_count: int
    model_ready: bool
    mode: str
    grace_period_active: bool


class InteractionRecord(BaseModel):
    user_token_hash: str
    event_id: str
    interaction_type: InteractionType
    created_at: str


class RecommendationInsight(BaseModel):
    event_id: str
    match_score: float
    matched_keywords: List[str]
    reason: str


EVENT_DEFINITIONS = [
    {
        "id": "evt-ai-careers",
        "title": "AI Careers Panel",
        "description": "UW Bothell alumni and recruiters talk through internships, portfolios, and entry-level AI roles.",
        "building_name": "STEM",
        "category": "technology",
        "tags": ["ai", "coding", "career", "internship"],
        "audience": ["computer science", "informatics"],
        "days_ahead": 1,
        "duration_minutes": 90,
    },
    {
        "id": "evt-hackathon",
        "title": "Hackathon Kickoff Night",
        "description": "Student teams form around campus challenges, design prototypes, and plan weekend builds.",
        "building_name": "DISC",
        "category": "technology",
        "tags": ["hackathon", "programming", "teamwork", "design"],
        "audience": ["students"],
        "days_ahead": 2,
        "duration_minutes": 120,
    },
    {
        "id": "evt-resume-lab",
        "title": "Resume Sprint for STEM Students",
        "description": "Drop in for quick resume reviews, internship search tips, and LinkedIn polish.",
        "building_name": "CAB",
        "category": "career",
        "tags": ["resume", "career", "internship", "portfolio"],
        "audience": ["students"],
        "days_ahead": 3,
        "duration_minutes": 75,
    },
    {
        "id": "evt-biology-lecture",
        "title": "Biology Guest Lecture: Urban Ecology",
        "description": "A guest lecture on local ecosystems, field research methods, and environmental stewardship.",
        "building_name": "STEM",
        "category": "science",
        "tags": ["biology", "science", "research", "environment"],
        "audience": ["biology", "environmental science"],
        "days_ahead": 4,
        "duration_minutes": 90,
    },
    {
        "id": "evt-nursing-circle",
        "title": "Nursing Peer Study Circle",
        "description": "Small-group study session with nursing tutors, exam prep, and wellness check-ins.",
        "building_name": "HH",
        "category": "wellness",
        "tags": ["health", "wellness", "study", "care"],
        "audience": ["nursing"],
        "days_ahead": 5,
        "duration_minutes": 60,
    },
    {
        "id": "evt-transfer-mixer",
        "title": "Transfer Student Mixer",
        "description": "Meet classmates, learn campus resources, and get connected with transfer mentors.",
        "building_name": "CAB",
        "category": "community",
        "tags": ["transfer", "networking", "community", "welcome"],
        "audience": ["transfer students"],
        "days_ahead": 6,
        "duration_minutes": 90,
    },
    {
        "id": "evt-entrepreneurship-lunch",
        "title": "Entrepreneurship Lunch & Learn",
        "description": "Hear from student founders about pitching, startup validation, and campus support programs.",
        "building_name": "UW2",
        "category": "entrepreneurship",
        "tags": ["startup", "pitch", "innovation", "leadership"],
        "audience": ["business", "engineering"],
        "days_ahead": 7,
        "duration_minutes": 75,
    },
    {
        "id": "evt-library-office-hours",
        "title": "Library Research Office Hours",
        "description": "One-on-one help with sources, citations, literature reviews, and research strategy.",
        "building_name": "LIB",
        "category": "research",
        "tags": ["research", "writing", "citations", "library"],
        "audience": ["students"],
        "days_ahead": 8,
        "duration_minutes": 60,
    },
    {
        "id": "evt-club-fair",
        "title": "Club Fair & Student Org Showcase",
        "description": "Browse campus clubs, ask current members questions, and sign up on the spot.",
        "building_name": "CAMPUS CENTER",
        "category": "community",
        "tags": ["clubs", "involvement", "community", "networking"],
        "audience": ["students"],
        "days_ahead": 9,
        "duration_minutes": 120,
    },
    {
        "id": "evt-mindful-movement",
        "title": "Mindful Movement Walk",
        "description": "A low-pressure outdoor walk focused on stress relief, wellness, and connection.",
        "building_name": "CAMPUS CENTER",
        "category": "wellness",
        "tags": ["wellness", "fitness", "community", "mindfulness"],
        "audience": ["students"],
        "days_ahead": 10,
        "duration_minutes": 45,
    },
    {
        "id": "evt-leadership-workshop",
        "title": "Inclusive Leadership Workshop",
        "description": "Build leadership skills around communication, equity, and collaborative decision-making.",
        "building_name": "UW1",
        "category": "leadership",
        "tags": ["leadership", "equity", "teamwork", "community"],
        "audience": ["students"],
        "days_ahead": 11,
        "duration_minutes": 90,
    },
    {
        "id": "evt-poster-session",
        "title": "Graduate Research Poster Session",
        "description": "See student posters, ask research questions, and compare projects across disciplines.",
        "building_name": "DISC",
        "category": "research",
        "tags": ["research", "presentation", "science", "poster"],
        "audience": ["graduate students", "undergraduates"],
        "days_ahead": 12,
        "duration_minutes": 120,
    },
]

MAJOR_PROFILES: dict[str, dict[str, dict[str, float]]] = {
    "computer science": {
        "keywords": {
            "ai": 3,
            "coding": 3,
            "programming": 3,
            "hackathon": 3,
            "software": 3,
            "cybersecurity": 3,
            "security": 2,
            "data": 2,
            "cloud": 2,
            "systems": 2,
            "web": 2,
            "machine learning": 3,
            "ml": 3,
            "tableau": 2,
            "analytics": 2,
            "technology": 1,
            "career": 2,
            "internship": 2,
            "resume": 1,
            "research": 1,
        },
        "categories": {
            "technology": 3,
            "career": 2,
            "research": 1,
        },
    },
    "informatics": {
        "keywords": {
            "data": 3,
            "ux": 3,
            "design": 2,
            "ai": 2,
            "coding": 2,
            "research": 2,
            "career": 1,
        },
        "categories": {
            "technology": 2,
            "research": 3,
            "career": 1,
        },
    },
    "biology": {
        "keywords": {
            "biology": 3,
            "science": 3,
            "research": 3,
            "environment": 2,
            "health": 1,
        },
        "categories": {
            "science": 3,
            "research": 2,
            "wellness": 1,
        },
    },
    "business": {
        "keywords": {
            "entrepreneurship": 3,
            "startup": 3,
            "pitch": 2,
            "networking": 2,
            "leadership": 2,
            "career": 2,
            "resume": 1,
        },
        "categories": {
            "entrepreneurship": 3,
            "career": 2,
            "leadership": 2,
        },
    },
    "nursing": {
        "keywords": {
            "health": 3,
            "care": 3,
            "wellness": 2,
            "study": 1,
            "community": 1,
        },
        "categories": {
            "wellness": 3,
            "science": 1,
            "community": 1,
        },
    },
    "education": {
        "keywords": {
            "leadership": 3,
            "community": 2,
            "teaching": 3,
            "equity": 2,
            "student": 1,
        },
        "categories": {
            "leadership": 3,
            "community": 2,
        },
    },
    "undeclared": {
        "keywords": {
            "community": 1,
            "career": 1,
            "leadership": 1,
            "wellness": 1,
        },
        "categories": {
            "community": 1,
            "career": 1,
            "wellness": 1,
        },
    },
}


def _normalize_text(value: Optional[str]) -> str:
    if not value:
        return ""
    return " ".join(value.strip().lower().split())


def _format_title(value: str) -> str:
    return " ".join(part.capitalize() for part in value.split())


def _hash_user_token(user_token: str) -> str:
    normalized = user_token.strip()
    if len(normalized) == 64:
        try:
            int(normalized, 16)
            return normalized.lower()
        except ValueError:
            pass
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _parse_timestamp(raw_value: str) -> datetime:
    try:
        return datetime.fromisoformat(raw_value.replace("Z", "+00:00"))
    except Exception:
        return datetime.now(timezone.utc)


_ai_client: Optional[OpenAI] = None
_ai_insight_cache: dict[str, dict[str, RecommendationInsight]] = {}
_ai_insight_cache_lock = Lock()


def _get_ai_client() -> OpenAI:
    global _ai_client
    if _ai_client is None:
        _ai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _ai_client


def _strip_code_fences(content: str) -> str:
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```", 2)[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    return cleaned.strip()


def _clean_text(value: str) -> str:
    return " ".join(value.strip().split())


def _event_signature(events: List[EventCard], target_major: str) -> str:
    digest = hashlib.sha256()
    digest.update(_normalize_text(target_major).encode("utf-8"))
    for event in events:
        digest.update(event.id.encode("utf-8"))
        digest.update(event.title.encode("utf-8"))
        digest.update(event.description.encode("utf-8"))
        digest.update(event.category.encode("utf-8"))
        digest.update(event.start_time.encode("utf-8"))
        digest.update(event.end_time.encode("utf-8"))
    return digest.hexdigest()


def _normalize_keywords(keywords: List[str]) -> List[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for keyword in keywords:
        cleaned = _clean_text(str(keyword))
        if not cleaned:
            continue
        lowered = cleaned.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        deduped.append(cleaned)
    return deduped[:6]


def _cs_keyword_profile(major: str) -> dict[str, dict[str, float]]:
    normalized = _normalize_text(major)
    profile = MAJOR_PROFILES.get(normalized)
    if profile:
        return profile
    return MAJOR_PROFILES["computer science"]


def _keyword_in_text(text: str, keyword: str) -> bool:
    cleaned_keyword = _normalize_text(keyword)
    if not cleaned_keyword:
        return False
    pattern = rf"\b{re.escape(cleaned_keyword)}\b"
    return re.search(pattern, text) is not None


def _heuristic_insight(event: EventCard, target_major: str) -> RecommendationInsight:
    profile = _cs_keyword_profile(target_major)
    combined = _normalize_text(" ".join([event.title, event.description, event.category, *event.tags, *event.audience]))

    matched_keywords = [keyword for keyword in profile["keywords"] if _keyword_in_text(combined, keyword)]
    matched_keywords = _normalize_keywords(matched_keywords)

    score = 0.0
    for keyword in matched_keywords:
        score += profile["keywords"].get(_normalize_text(keyword), 1.0)
    score += profile["categories"].get(event.category, 0.0)
    for audience_term in event.audience:
        score += profile["keywords"].get(_normalize_text(audience_term), 0.0) * 0.5

    if matched_keywords:
        reason = f"Matches {target_major} keywords: {', '.join(matched_keywords[:3])}."
    else:
        reason = f"General campus event for {target_major} students."

    return RecommendationInsight(
        event_id=event.id,
        match_score=min(100.0, round(score * 12.5, 2)),
        matched_keywords=matched_keywords,
        reason=reason,
    )


def _heuristic_insights(events: List[EventCard], target_major: str) -> tuple[dict[str, RecommendationInsight], bool]:
    return ({event.id: _heuristic_insight(event, target_major) for event in events}, False)


def _parse_ai_insights(raw_content: str, events: List[EventCard], target_major: str) -> dict[str, RecommendationInsight]:
    event_lookup = {event.id: event for event in events}
    fallback_insights, _ = _heuristic_insights(events, target_major)
    insights = dict(fallback_insights)

    try:
        parsed = json.loads(_strip_code_fences(raw_content))
    except Exception:
        return insights

    if isinstance(parsed, dict):
        rows = parsed.get("analyses") or parsed.get("events") or []
    elif isinstance(parsed, list):
        rows = parsed
    else:
        rows = []

    for row in rows:
        try:
            event_id = str(row.get("event_id") or "").strip()
            if event_id not in event_lookup:
                continue
            match_score = float(row.get("match_score") or 0.0)
            matched_keywords = _normalize_keywords(list(row.get("matched_keywords") or []))
            reason = _clean_text(str(row.get("reason") or ""))
            if not reason:
                reason = insights[event_id].reason
            insights[event_id] = RecommendationInsight(
                event_id=event_id,
                match_score=max(0.0, min(100.0, round(match_score, 2))),
                matched_keywords=matched_keywords,
                reason=reason,
            )
        except Exception:
            continue

    return insights


def _ai_insights_for_events(events: List[EventCard], target_major: str) -> tuple[dict[str, RecommendationInsight], bool]:
    if not AI_RECOMMENDER_ENABLED:
        return _heuristic_insights(events, target_major)

    signature = _event_signature(events, target_major)
    with _ai_insight_cache_lock:
        cached = _ai_insight_cache.get(signature)
        if cached is not None:
            return cached, True

    prompt_events = [
        {
            "event_id": event.id,
            "title": event.title,
            "description": event.description,
            "category": event.category,
            "tags": event.tags,
            "audience": event.audience,
        }
        for event in events
    ]

    system_prompt = (
        "You rank UW Bothell events for a target major student. "
        "Return only valid JSON with an 'analyses' array. "
        "For each event, provide event_id, match_score from 0 to 100, matched_keywords, and a short reason. "
        "Matched keywords should be short phrases from the title or description whenever possible. "
        "Score high for directly relevant events and low for unrelated ones. "
        "Prioritize computing, programming, software, AI, cybersecurity, data, systems, cloud, web, hackathons, internships, resume help, and research for computer science. "
        "If a different target major is provided, adapt the relevance to that major."
    )

    user_prompt = json.dumps(
        {
            "target_major": target_major,
            "events": prompt_events,
            "output_schema": {
                "analyses": [
                    {
                        "event_id": "string",
                        "match_score": 0,
                        "matched_keywords": ["keyword"],
                        "reason": "short sentence",
                    }
                ]
            },
        },
        ensure_ascii=True,
    )

    try:
        client = _get_ai_client()
        response = client.chat.completions.create(
            model=AI_RECOMMENDER_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
            max_tokens=1200,
        )
        content = response.choices[0].message.content or ""
        insights = _parse_ai_insights(content, events, target_major)
        with _ai_insight_cache_lock:
            _ai_insight_cache[signature] = insights
        return insights, True
    except Exception:
        return _heuristic_insights(events, target_major)


def _build_event_catalog(limit: int = 60) -> List[EventCard]:
    catalog: List[EventCard] = []
    for event_data in fetch_calendar_events(limit=limit):
        try:
            catalog.append(
                EventCard(
                    id=str(event_data["id"]),
                    title=str(event_data["title"]),
                    description=str(event_data["description"]),
                    building_name=str(event_data["building_name"]),
                    coordinates=list(event_data["coordinates"]),
                    category=str(event_data["category"]),
                    tags=list(event_data["tags"]),
                    audience=list(event_data["audience"]),
                    start_time=str(event_data["start_time"]),
                    end_time=str(event_data["end_time"]),
                )
            )
        except (KeyError, TypeError, ValueError):
            continue
    return catalog


def _combine_reasons(reasons: List[str]) -> str:
    cleaned = [reason.rstrip(".") for reason in reasons if reason]
    if not cleaned:
        return "A solid campus option."
    if len(cleaned) == 1:
        return f"{cleaned[0]}."
    if len(cleaned) == 2:
        return f"{cleaned[0]} and {cleaned[1].lower()}."
    return f"{cleaned[0]}, {cleaned[1].lower()}, and {cleaned[2].lower()}."


def _resolve_major_profile(major: Optional[str]) -> Tuple[Optional[str], Optional[dict[str, dict[str, float]]], str]:
    normalized = _normalize_text(major)
    if not normalized:
        return None, None, "fallback-popularity"

    for profile_name, profile in MAJOR_PROFILES.items():
        if profile_name in normalized or normalized in profile_name:
            return _format_title(profile_name), profile, "request"

    if normalized in MAJOR_PROFILES:
        return _format_title(normalized), MAJOR_PROFILES[normalized], "request"

    return _format_title(normalized), None, "fallback-popularity"


class RecommendationStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self.launch_started_at = self._read_launch_started_at()
        self.events = _build_event_catalog()
        self.interactions: List[InteractionRecord] = []
        

    def _current_events(self) -> List[EventCard]:
        events = _build_event_catalog()
        if events:
            with self._lock:
                self.events = events
            return events

        with self._lock:
            return list(self.events)

    def _read_launch_started_at(self) -> datetime:
        raw_value = os.getenv("CAMPUS_PULSE_LAUNCH_STARTED_AT")
        if raw_value:
            try:
                return _parse_timestamp(raw_value)
            except Exception:
                pass
        return datetime.now(timezone.utc) - timedelta(days=GRACE_PERIOD_DAYS + 1)

    def reset(self, seed_demo: bool = False) -> None:
        with self._lock:
            self.launch_started_at = self._read_launch_started_at()
            self.events = _build_event_catalog()
            self.interactions = []
        if seed_demo:
            self.seed_demo_data()

    def seed_demo_data(self) -> None:
        if os.getenv("CAMPUS_PULSE_DISABLE_RECOMMENDER_SEED", "0") == "1":
            return
        event_ids = [event.id for event in self._current_events()]
        if not event_ids:
            return

        interaction_cycle = ["view", "click", "save", "view", "click"]
        demo_users = [f"demo-student-{index}" for index in range(1, 7)]

        for user_index, user_token in enumerate(demo_users):
            rotated_event_ids = event_ids[user_index:] + event_ids[:user_index]
            for index in range(10):
                event_id = rotated_event_ids[index % len(rotated_event_ids)]
                interaction_type = interaction_cycle[index % len(interaction_cycle)]
                self.record_interaction(user_token, event_id, interaction_type, seed_only=True)

    def _snapshot(self) -> List[InteractionRecord]:
        with self._lock:
            return list(self.interactions)

    def _aggregate_state(
        self, interactions: List[InteractionRecord]
    ) -> Tuple[Counter, dict[str, Counter], dict[Tuple[str, str], float], Counter]:
        event_popularity: Counter = Counter()
        user_event_weights: dict[str, Counter] = defaultdict(Counter)
        user_event_sets: dict[str, set[str]] = defaultdict(set)
        user_counts: Counter = Counter()

        for record in interactions:
            weight = INTERACTION_WEIGHTS.get(record.interaction_type, 1.0)
            event_popularity[record.event_id] += weight
            user_event_weights[record.user_token_hash][record.event_id] += weight
            user_event_sets[record.user_token_hash].add(record.event_id)
            user_counts[record.user_token_hash] += 1

        cooccurrence: dict[Tuple[str, str], float] = defaultdict(float)
        for event_set in user_event_sets.values():
            ordered = sorted(event_set)
            for left_event, right_event in combinations(ordered, 2):
                cooccurrence[(left_event, right_event)] += 1.0

        return event_popularity, user_event_weights, cooccurrence, user_counts

    def _grace_period_active(self) -> bool:
        return datetime.now(timezone.utc) - self.launch_started_at < timedelta(days=GRACE_PERIOD_DAYS)

    def _mode_for_context(
        self,
        model_ready: bool,
        major_profile: Optional[dict[str, dict[str, float]]],
    ) -> str:
        if self._grace_period_active():
            return "popularity"
        if model_ready:
            return "collaborative"
        if major_profile:
            return "major-seeded"
        return "popularity"

    def _major_affinity_score(
        self,
        event: EventCard,
        major_profile: Optional[dict[str, dict[str, float]]],
    ) -> float:
        if not major_profile:
            return 0.0

        keyword_scores = major_profile["keywords"]
        category_scores = major_profile["categories"]

        score = 0.0
        for tag in event.tags:
            score += keyword_scores.get(tag, 0.0)
        score += category_scores.get(event.category, 0.0)

        for audience_term in event.audience:
            score += keyword_scores.get(_normalize_text(audience_term), 0.0) * 0.5

        return score

    def _recency_score(self, event: EventCard) -> float:
        try:
            start_time = _parse_timestamp(event.start_time)
            hours_until = max((start_time - datetime.now(timezone.utc)).total_seconds() / 3600.0, 0.0)
            return max(0.0, 1.0 - hours_until / (24.0 * 12.0))
        except Exception:
            return 0.0

    def _collaborative_score(
        self,
        event_id: str,
        user_event_weights: Counter,
        event_popularity: Counter,
        cooccurrence: dict[Tuple[str, str], float],
    ) -> float:
        score = 0.0
        for seed_event_id, seed_weight in user_event_weights.items():
            if seed_event_id == event_id:
                continue
            pair = tuple(sorted((seed_event_id, event_id)))
            pair_strength = cooccurrence.get(pair, 0.0)
            if not pair_strength:
                continue

            seed_popularity = max(float(event_popularity.get(seed_event_id, 0.0)), 1.0)
            candidate_popularity = max(float(event_popularity.get(event_id, 0.0)), 1.0)
            score += (pair_strength / math.sqrt(seed_popularity * candidate_popularity)) * float(seed_weight)

        return score

    def _format_reason(
        self,
        mode: str,
        major_label: Optional[str],
        major_score: float,
        collaborative_score: float,
        popularity_score: float,
        recency_score: float,
        already_seen: bool,
    ) -> str:
        reasons: List[str] = []
        if mode == "collaborative" and collaborative_score > 0:
            reasons.append("Students with similar activity engaged with this event")
        if major_label and major_score > 0:
            reasons.append(f"Matches your {major_label} interests")
        if popularity_score > 0.45:
            reasons.append("Popular with UW Bothell students")
        if recency_score > 0.45:
            reasons.append("Happening soon")
        if already_seen:
            reasons.append("You already interacted with this")

        return _combine_reasons(reasons)

    def _recommendations_for_user(
        self,
        user_token: str,
        major: Optional[str],
        limit: int,
    ) -> RecommendationResponse:
        user_token_hash = _hash_user_token(user_token)
        major_label, major_profile, major_source = _resolve_major_profile(major)
        target_major = major_label or _format_title(AI_RECOMMENDER_TARGET_MAJOR)
        if major_label:
            major_source = "request"
        else:
            major_source = "default-ai-profile"

        interactions = self._snapshot()
        event_popularity, user_event_weights, cooccurrence, user_counts = self._aggregate_state(interactions)
        user_history = user_event_weights.get(user_token_hash, Counter())
        current_events = self._current_events()

        global_interaction_count = len(interactions)
        user_interaction_count = user_counts.get(user_token_hash, 0)
        grace_period_active = self._grace_period_active()
        insights, ai_available = _ai_insights_for_events(current_events, target_major)
        model_ready = ai_available
        mode = "ai-match" if ai_available else "keyword-fallback"

        if not current_events:
            return RecommendationResponse(
                user_token_hash=user_token_hash,
                major=major_label,
                major_source=major_source,
                mode=mode,
                model_ready=model_ready,
                grace_period_active=grace_period_active,
                global_interaction_count=global_interaction_count,
                user_interaction_count=user_interaction_count,
                ai_available=ai_available,
                ai_target_major=target_major,
                fallback_reason="UW Bothell calendar returned no current events.",
                generated_at=datetime.now(timezone.utc).isoformat(),
                recommendations=[],
            )

        max_popularity = max((float(value) for value in event_popularity.values()), default=1.0)
        cards: List[RecommendationCard] = []

        for event in current_events:
            insight = insights.get(event.id) or RecommendationInsight(
                event_id=event.id,
                match_score=0.0,
                matched_keywords=[],
                reason="No recommendation insight available.",
            )
            popularity_score = math.log1p(float(event_popularity.get(event.id, 0.0))) / math.log1p(max_popularity)
            major_score = self._major_affinity_score(event, major_profile or _cs_keyword_profile(target_major))
            recency_score = self._recency_score(event)

            already_seen = event.id in user_history
            seen_penalty = 1.2 if already_seen else 0.0

            if ai_available:
                score = (
                    (insight.match_score / 10.0)
                    + recency_score * 1.25
                    + popularity_score * 1.0
                    - seen_penalty
                )
                why = insight.reason
            else:
                score = (
                    major_score * 1.5
                    + recency_score * 1.25
                    + popularity_score * 1.0
                    - seen_penalty
                )
                why = insight.reason

            cards.append(
                RecommendationCard(
                    **event.model_dump(),
                    rank=0,
                    score=round(score, 3),
                    why=why,
                    ai_score=round(insight.match_score, 2),
                    matched_keywords=insight.matched_keywords,
                )
            )

        cards.sort(key=lambda card: (-card.score, card.start_time, card.title))
        limited_cards: List[RecommendationCard] = []
        for rank, card in enumerate(cards[: max(1, limit)], start=1):
            limited_cards.append(card.model_copy(update={"rank": rank}))

        fallback_reason: Optional[str] = None
        if grace_period_active:
            fallback_reason = "Two-week deployment grace period is active."
        elif not ai_available:
            fallback_reason = f"AI scoring unavailable; using keyword fallback for {target_major} students."

        return RecommendationResponse(
            user_token_hash=user_token_hash,
            major=major_label,
            major_source=major_source,
            mode=mode,
            model_ready=model_ready,
            grace_period_active=grace_period_active,
            global_interaction_count=global_interaction_count,
            user_interaction_count=user_interaction_count,
            ai_available=ai_available,
            ai_target_major=target_major,
            fallback_reason=fallback_reason,
            generated_at=datetime.now(timezone.utc).isoformat(),
            recommendations=limited_cards,
        )

    def get_recommendations(
        self,
        user_token: str,
        major: Optional[str] = None,
        limit: int = DEFAULT_LIMIT,
    ) -> RecommendationResponse:
        return self._recommendations_for_user(user_token=user_token, major=major, limit=limit)

    def record_interaction(
        self,
        user_token: str,
        event_id: str,
        interaction_type: InteractionType,
        major: Optional[str] = None,
        seed_only: bool = False,
    ) -> InteractionResponse:
        event_ids = {event.id for event in self._current_events()}
        if event_id not in event_ids:
            raise ValueError(f"Unknown event_id: {event_id}")

        record = InteractionRecord(
            user_token_hash=_hash_user_token(user_token),
            event_id=event_id,
            interaction_type=interaction_type,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        with self._lock:
            self.interactions.append(record)

        snapshot = self.get_recommendations(user_token=user_token, major=major)
        return InteractionResponse(
            accepted=True,
            user_token_hash=record.user_token_hash,
            event_id=event_id,
            interaction_type=interaction_type,
            global_interaction_count=snapshot.global_interaction_count,
            user_interaction_count=snapshot.user_interaction_count,
            model_ready=snapshot.model_ready,
            mode=snapshot.mode,
            grace_period_active=snapshot.grace_period_active,
        )


store = RecommendationStore()
