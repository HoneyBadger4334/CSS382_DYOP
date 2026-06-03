import logging
import os
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)

OBA_BASE = "https://api.pugetsound.onebusaway.org/api/where"

# Key UW Bothell bus stops — hardcoded since these are fixed infrastructure
UW_BOTHELL_STOPS = [
    {"id": "29_2229",  "name": "UW Bothell & Cascadia College", "lat": 47.761773, "lon": -122.192425},
    {"id": "1_76224",  "name": "Beardslee Blvd & 108th Ave NE", "lat": 47.762245, "lon": -122.195900},
    {"id": "1_76301",  "name": "Beardslee Blvd & 110th Ave NE", "lat": 47.763996, "lon": -122.193596},
]


def _get_api_key() -> str:
    return os.environ.get("OBA_API_KEY", "TEST")


def _fmt_time(ms: int) -> str:
    dt = datetime.fromtimestamp(ms / 1000, tz=timezone.utc).astimezone()
    return dt.strftime("%-I:%M %p")


def _minutes_away(ms: int) -> int:
    now_ms = datetime.now(timezone.utc).timestamp() * 1000
    return max(0, int((ms - now_ms) / 60000))


def fetch_arrivals_for_stop(stop_id: str, minutes_ahead: int = 60) -> list[dict]:
    """Fetch upcoming arrivals for a single stop. Returns list of arrival dicts."""
    try:
        resp = httpx.get(
            f"{OBA_BASE}/arrivals-and-departures-for-stop/{stop_id}.json",
            params={
                "key": _get_api_key(),
                "minutesBefore": 0,
                "minutesAfter": minutes_ahead,
            },
            timeout=8,
        )
        resp.raise_for_status()
        data = resp.json()
        arrivals = data["data"]["entry"]["arrivalsAndDepartures"]

        result = []
        for a in arrivals[:8]:  # cap at 8 per stop
            arrival_ms = a["predictedArrivalTime"] if a["predicted"] and a["predictedArrivalTime"] else a["scheduledArrivalTime"]
            if not arrival_ms:
                continue
            mins = _minutes_away(arrival_ms)
            result.append({
                "route":     a["routeShortName"],
                "headsign":  a["tripHeadsign"],
                "time":      _fmt_time(arrival_ms),
                "minutes":   mins,
                "predicted": a["predicted"],
            })

        return sorted(result, key=lambda x: x["minutes"])

    except Exception as e:
        logger.error("Failed to fetch arrivals for stop %s: %s", stop_id, e)
        return []


def fetch_all_stops() -> list[dict]:
    """Fetch arrivals for all UW Bothell stops. Returns list of stop dicts with arrivals."""
    stops = []
    for stop in UW_BOTHELL_STOPS:
        arrivals = fetch_arrivals_for_stop(stop["id"])
        stops.append({
            "id":       stop["id"],
            "name":     stop["name"],
            "lat":      stop["lat"],
            "lon":      stop["lon"],
            "arrivals": arrivals,
        })
    return stops
