from __future__ import annotations

import hashlib
import math
import os
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from itertools import combinations
from threading import Lock
from typing import List, Literal, Optional, Tuple

from pydantic import BaseModel, ConfigDict

from building_coords import resolve_coordinates

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


def _build_event_catalog(anchor: Optional[datetime] = None) -> List[EventCard]:
    anchor = anchor or datetime.now(timezone.utc)
    catalog: List[EventCard] = []
    for definition in EVENT_DEFINITIONS:
        start_time = anchor + timedelta(days=definition["days_ahead"])
        end_time = start_time + timedelta(minutes=definition["duration_minutes"])
        catalog.append(
            EventCard(
                id=definition["id"],
                title=definition["title"],
                description=definition["description"],
                building_name=definition["building_name"],
                coordinates=list(resolve_coordinates(definition["building_name"])),
                category=definition["category"],
                tags=definition["tags"],
                audience=definition["audience"],
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat(),
            )
        )
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
        self.seed_demo_data()

    def _read_launch_started_at(self) -> datetime:
        raw_value = os.getenv("CAMPUS_PULSE_LAUNCH_STARTED_AT")
        if raw_value:
            try:
                return _parse_timestamp(raw_value)
            except Exception:
                pass
        return datetime.now(timezone.utc) - timedelta(days=GRACE_PERIOD_DAYS + 1)

    def reset(self, seed_demo: bool = True) -> None:
        with self._lock:
            self.launch_started_at = self._read_launch_started_at()
            self.events = _build_event_catalog()
            self.interactions = []
        if seed_demo:
            self.seed_demo_data()

    def seed_demo_data(self) -> None:
        if os.getenv("CAMPUS_PULSE_DISABLE_RECOMMENDER_SEED", "0") == "1":
            return

        demo_plans: dict[str, list[str]] = {
            "demo-student-1": [
                "evt-ai-careers",
                "evt-hackathon",
                "evt-resume-lab",
                "evt-library-office-hours",
                "evt-ai-careers",
                "evt-hackathon",
                "evt-resume-lab",
                "evt-leadership-workshop",
                "evt-poster-session",
                "evt-club-fair",
            ],
            "demo-student-2": [
                "evt-biology-lecture",
                "evt-poster-session",
                "evt-library-office-hours",
                "evt-mindful-movement",
                "evt-biology-lecture",
                "evt-nursing-circle",
                "evt-library-office-hours",
                "evt-club-fair",
                "evt-transfer-mixer",
                "evt-leadership-workshop",
            ],
            "demo-student-3": [
                "evt-entrepreneurship-lunch",
                "evt-resume-lab",
                "evt-leadership-workshop",
                "evt-transfer-mixer",
                "evt-club-fair",
                "evt-entrepreneurship-lunch",
                "evt-resume-lab",
                "evt-leadership-workshop",
                "evt-ai-careers",
                "evt-mindful-movement",
            ],
            "demo-student-4": [
                "evt-nursing-circle",
                "evt-mindful-movement",
                "evt-club-fair",
                "evt-library-office-hours",
                "evt-transfer-mixer",
                "evt-nursing-circle",
                "evt-mindful-movement",
                "evt-club-fair",
                "evt-leadership-workshop",
                "evt-library-office-hours",
            ],
            "demo-student-5": [
                "evt-leadership-workshop",
                "evt-transfer-mixer",
                "evt-club-fair",
                "evt-resume-lab",
                "evt-mindful-movement",
                "evt-leadership-workshop",
                "evt-transfer-mixer",
                "evt-club-fair",
                "evt-entrepreneurship-lunch",
                "evt-library-office-hours",
            ],
            "demo-student-6": [
                "evt-club-fair",
                "evt-mindful-movement",
                "evt-library-office-hours",
                "evt-transfer-mixer",
                "evt-resume-lab",
                "evt-club-fair",
                "evt-mindful-movement",
                "evt-library-office-hours",
                "evt-ai-careers",
                "evt-entrepreneurship-lunch",
            ],
        }

        interaction_cycle = ["view", "click", "save", "view", "click"]
        for user_token, event_ids in demo_plans.items():
            for index, event_id in enumerate(event_ids):
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

        interactions = self._snapshot()
        event_popularity, user_event_weights, cooccurrence, user_counts = self._aggregate_state(interactions)
        user_history = user_event_weights.get(user_token_hash, Counter())

        global_interaction_count = len(interactions)
        user_interaction_count = user_counts.get(user_token_hash, 0)
        grace_period_active = self._grace_period_active()
        model_ready = (
            global_interaction_count >= GLOBAL_ACTIVATION_THRESHOLD
            and user_interaction_count >= USER_ACTIVATION_THRESHOLD
            and not grace_period_active
        )
        mode = self._mode_for_context(model_ready, major_profile)

        max_popularity = max((float(value) for value in event_popularity.values()), default=1.0)
        cards: List[RecommendationCard] = []

        for event in self.events:
            popularity_score = math.log1p(float(event_popularity.get(event.id, 0.0))) / math.log1p(max_popularity)
            major_score = self._major_affinity_score(event, major_profile)
            recency_score = self._recency_score(event)
            collaborative_score = 0.0

            if model_ready:
                collaborative_score = self._collaborative_score(event.id, user_history, event_popularity, cooccurrence)

            already_seen = event.id in user_history
            seen_penalty = 1.2 if already_seen else 0.0

            score = (
                popularity_score * 1.4
                + major_score * 0.9
                + recency_score * 0.75
                + collaborative_score * 1.6
                - seen_penalty
            )

            why = self._format_reason(
                mode=mode,
                major_label=major_label,
                major_score=major_score,
                collaborative_score=collaborative_score,
                popularity_score=popularity_score,
                recency_score=recency_score,
                already_seen=already_seen,
            )

            cards.append(
                RecommendationCard(
                    **event.model_dump(),
                    rank=0,
                    score=round(score, 3),
                    why=why,
                )
            )

        cards.sort(key=lambda card: (-card.score, card.start_time, card.title))
        limited_cards: List[RecommendationCard] = []
        for rank, card in enumerate(cards[: max(1, limit)], start=1):
            limited_cards.append(card.model_copy(update={"rank": rank}))

        fallback_reason: Optional[str] = None
        if grace_period_active:
            fallback_reason = "Two-week deployment grace period is active."
        elif mode == "major-seeded" and major_profile:
            fallback_reason = "Using major-seeded ranking until both interaction thresholds are met."
        elif mode == "popularity" and not major_profile:
            fallback_reason = "Major profile unavailable; showing popularity-ranked events."

        return RecommendationResponse(
            user_token_hash=user_token_hash,
            major=major_label,
            major_source=major_source,
            mode=mode,
            model_ready=model_ready,
            grace_period_active=grace_period_active,
            global_interaction_count=global_interaction_count,
            user_interaction_count=user_interaction_count,
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
        event_ids = {event.id for event in self.events}
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
