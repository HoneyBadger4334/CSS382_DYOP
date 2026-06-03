import asyncio
import os
from datetime import datetime, timezone
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from building_coords import resolve_coordinates, CAMPUS_CENTER
from rss_fetcher import fetch_alerts
from nlp_summarizer import summarize
from database import log_interaction, hash_netid
from recommender import get_recommendations

load_dotenv()

app = FastAPI(title="Campus Pulse API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
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

_demo_task: Optional[asyncio.Task] = None
_pre_demo_cache: Optional[AlertsResponse] = None

DEMO_SCENARIOS = {
    "high": (
        "Active Threat",
        "ACTIVE THREAT reported near {building}. Shelter in place immediately. Lock doors and avoid windows.",
        "Shelter in place immediately. Lock all doors, stay away from windows. Do not leave until all-clear is issued.",
    ),
    "medium": (
        "Suspicious Activity",
        "Suspicious activity reported near {building}. Campus safety and police are responding to the scene.",
        "Avoid the area around {building}. Follow instructions from campus safety officers.",
    ),
    "low": (
        "Minor Incident",
        "Minor incident reported near {building}. Campus safety is on scene and the situation is under control.",
        "Avoid the immediate area around {building}. Normal operations may continue elsewhere on campus.",
    ),
}

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


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}


class LoginRequest(BaseModel):
    netid: str


@app.post("/api/login")
async def login(body: LoginRequest) -> dict:
    if not body.netid or not body.netid.strip():
        return {"error": "NetID required"}
    hashed = hash_netid(body.netid)
    return {"hashed_netid": hashed}


@app.get("/api/recommendations")
async def recommendations(
    hashed_netid: str,
    major: Optional[str] = None,
    limit: int = 10,
) -> dict:
    events, mode = get_recommendations(hashed_netid, major=major, limit=limit)
    return {"events": events, "mode": mode}


@app.post("/api/demo")
async def trigger_demo(building: str = "UW1", severity: str = "high") -> dict:
    global _cache, _demo_task, _pre_demo_cache

    if _demo_task and not _demo_task.done():
        _demo_task.cancel()

    _pre_demo_cache = _cache

    incident_type, raw_tpl, action_tpl = DEMO_SCENARIOS.get(severity, DEMO_SCENARIOS["high"])
    raw_text = raw_tpl.format(building=building.upper())
    action = action_tpl.format(building=building.upper())

    demo_pin = AlertPin(
        id="demo-alert",
        raw_text=raw_text,
        building_name=building.upper(),
        incident_type=incident_type,
        severity=severity,
        recommended_action=action,
        coordinates=list(resolve_coordinates(building.upper())),
        published=datetime.now(timezone.utc).isoformat(),
    )

    _cache = AlertsResponse(
        alerts=[demo_pin],
        last_updated=datetime.now(timezone.utc).isoformat(),
        ai_available=True,
        feed_available=True,
    )

    async def revert():
        global _cache, _pre_demo_cache
        await asyncio.sleep(60)
        if _pre_demo_cache is not None:
            _cache = _pre_demo_cache
            _pre_demo_cache = None

    _demo_task = asyncio.create_task(revert())
    return {"status": "ok", "building": building.upper(), "severity": severity, "expires_in": 60}


@app.post("/api/demo/clear")
async def clear_demo() -> dict:
    global _cache, _demo_task, _pre_demo_cache

    if _demo_task and not _demo_task.done():
        _demo_task.cancel()

    if _pre_demo_cache is not None:
        _cache = _pre_demo_cache
        _pre_demo_cache = None

    return {"status": "cleared"}


class InteractionRequest(BaseModel):
    hashed_netid: str
    event_id: str


@app.post("/api/interactions")
async def record_interaction(body: InteractionRequest) -> dict:
    ok = log_interaction(body.hashed_netid, body.event_id)
    return {"recorded": ok}
