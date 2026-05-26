import asyncio
import os
from datetime import datetime, timezone
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from building_coords import resolve_coordinates, CAMPUS_CENTER
from recommender import (
    EventCard,
    InteractionRequest,
    InteractionResponse,
    RecommendationResponse,
    store as recommendation_store,
)
from calendar_fetcher import fetch_calendar_events
from rss_fetcher import fetch_alerts
from nlp_summarizer import summarize

load_dotenv()

app = FastAPI(title="Campus Pulse API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# ── In-memory cache ──────────────────────────────────────────────────────────

class AlertPin(BaseModel):
    id: str
    raw_text: str
    building_name: str
    incident_type: str
    severity: str          # low | medium | high
    recommended_action: str
    coordinates: list[float]  # [lat, lng]
    published: str

class AlertsResponse(BaseModel):
    alerts: list[AlertPin]
    last_updated: str
    ai_available: bool
    feed_available: bool

_cache: AlertsResponse = AlertsResponse(
    alerts=[],
    last_updated=datetime.now(timezone.utc).isoformat(),
    ai_available=True,
    feed_available=True,
)

# Hardcoded Week 7 test pin — always present until live alerts load.
TEST_PIN = AlertPin(
    id="test-week7",
    raw_text="[Test] UW Bothell Campus Pulse is live.",
    building_name="UW1",
    incident_type="Test Pin",
    severity="low",
    recommended_action="No action needed. This is a test pin.",
    coordinates=list(resolve_coordinates("UW1")),
    published=datetime.now(timezone.utc).isoformat(),
)

# ── Background refresh ────────────────────────────────────────────────────────

POLL_INTERVAL_SECONDS = 300  # 5 minutes


async def refresh_alerts() -> None:
    global _cache

    raw_alerts, feed_ok = fetch_alerts()
    ai_ok = True
    pins: list[AlertPin] = []

    for raw in raw_alerts:
        summary, ai_available = summarize(raw["raw_text"])
        if not ai_available:
            ai_ok = False

        if summary:
            coords = resolve_coordinates(summary.building_name)
            pins.append(
                AlertPin(
                    id=raw["id"],
                    raw_text=raw["raw_text"],
                    building_name=summary.building_name,
                    incident_type=summary.incident_type,
                    severity=summary.severity,
                    recommended_action=summary.recommended_action,
                    coordinates=list(coords),
                    published=raw["published"],
                )
            )
        else:
            # AI fallback: raw text on campus center
            pins.append(
                AlertPin(
                    id=raw["id"],
                    raw_text=raw["raw_text"],
                    building_name="CAMPUS",
                    incident_type="Alert",
                    severity="medium",
                    recommended_action="See raw alert text for details.",
                    coordinates=list(CAMPUS_CENTER),
                    published=raw["published"],
                )
            )

    # Always keep the Week 7 test pin if there are no live alerts.
    if not pins:
        pins = [TEST_PIN]

    _cache = AlertsResponse(
        alerts=pins,
        last_updated=datetime.now(timezone.utc).isoformat(),
        ai_available=ai_ok,
        feed_available=feed_ok,
    )


async def poll_loop() -> None:
    while True:
        try:
            await refresh_alerts()
        except Exception as e:
            print(f"[poll_loop] error: {e}")
        await asyncio.sleep(POLL_INTERVAL_SECONDS)


@app.on_event("startup")
async def startup_event() -> None:
    asyncio.create_task(poll_loop())


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/api/alerts", response_model=AlertsResponse)
async def get_alerts() -> AlertsResponse:
    return _cache


@app.get("/api/recommendations", response_model=RecommendationResponse)
async def get_recommendations(
    user_token: str = "demo-student-1",
    major: Optional[str] = None,
    limit: int = 6,
) -> RecommendationResponse:
    return recommendation_store.get_recommendations(user_token=user_token, major=major, limit=limit)


@app.get("/api/events", response_model=list[EventCard])
async def get_events(limit: int = 60) -> list[EventCard]:
    return [EventCard.model_validate(event) for event in fetch_calendar_events(limit=limit)]


@app.post("/api/recommendations/interactions", response_model=InteractionResponse)
async def log_recommendation_interaction(payload: InteractionRequest) -> InteractionResponse:
    try:
        return recommendation_store.record_interaction(
            user_token=payload.user_token,
            event_id=payload.event_id,
            interaction_type=payload.interaction_type,
            major=payload.major,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}
