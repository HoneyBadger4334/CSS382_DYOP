from typing import Optional

# UW Bothell campus center — used as fallback pin location
CAMPUS_CENTER = (47.75940, -122.19030)

# Keyed by common abbreviations and full names that the NLP model may return.
# Coordinates are (lat, lng).
BUILDING_COORDS: dict[str, tuple[float, float]] = {
    "UW1": (47.76014, -122.19019),
    "UW2": (47.75983, -122.18962),
    "DISC": (47.75824, -122.18872),
    "DISCOVERY HALL": (47.75824, -122.18872),
    "STEM": (47.75901, -122.18820),
    "SCIENCE AND ENGINEERING": (47.75901, -122.18820),
    "LIB": (47.76072, -122.19153),
    "LIBRARY": (47.76072, -122.19153),
    "CAB": (47.75968, -122.19163),
    "CAMPUS ACTIVITIES BUILDING": (47.75968, -122.19163),
    "HH": (47.75733, -122.18931),
    "HUSKY HALL": (47.75733, -122.18931),
    "NCH": (47.76183, -122.19001),
    "NORTH CREEK HALL": (47.76183, -122.19001),
    "CC": (47.75940, -122.19030),
    "CAMPUS CENTER": (47.75940, -122.19030),
    "CAMPUS": (47.75940, -122.19030),
    "SUMMIT HALL": (47.76221, -122.19447),
    "NORTH CREEK EVENTS CENTER": (47.76015, -122.19122),
    "NCEC": (47.76015, -122.19122),
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
