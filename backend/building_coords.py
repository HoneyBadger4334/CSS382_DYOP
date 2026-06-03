from typing import Optional

# UW Bothell campus center — used as fallback pin location
CAMPUS_CENTER = (47.75927, -122.19120)

# Keyed by common abbreviations and full names that the NLP model may return.
# Coordinates are (lat, lng).
BUILDING_COORDS: dict[str, tuple[float, float]] = {
    "UW1": (47.75884, -122.19067),
    "UW2": (47.75872, -122.19133),
    "DISC": (47.75902, -122.19201),
    "DISCOVERY HALL": (47.75902, -122.19201),
    "LIB": (47.75979, -122.19136),
    "LIBRARY": (47.75979, -122.19136),
    "ARC": (47.76005, -122.19033),
    "ACTIVITIES AND RECREATION CENTER": (47.76005, -122.19033),
    "HH": (47.76170, -122.19456),
    "HUSKY HALL": (47.76170, -122.19456),
    "NCH": (47.76042, -122.19050),
    "NORTH CREEK HALL": (47.76042, -122.19050),
    "CC": (47.75927, -122.19120),
    "CAMPUS CENTER": (47.75927, -122.19120),
    "CAMPUS": (47.75927, -122.19120),
}


def resolve_coordinates(building_name: str) -> tuple[float, float]:
    key = building_name.strip().upper()
    if key in BUILDING_COORDS:
        return BUILDING_COORDS[key]
    # Partial match fallback
    for name, coords in BUILDING_COORDS.items():
        if key in name or name in key:
            return coords
    return CAMPUS_CENTER
