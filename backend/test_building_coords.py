import pytest
from building_coords import resolve_coordinates, CAMPUS_CENTER


def test_exact_abbreviations():
    assert resolve_coordinates("UW1") == (47.75884, -122.19067)
    assert resolve_coordinates("UW2") == (47.75872, -122.19133)
    assert resolve_coordinates("DISC") == (47.75902, -122.19201)
    assert resolve_coordinates("LIB") == (47.75979, -122.19136)
    assert resolve_coordinates("HH") == (47.76170, -122.19456)
    assert resolve_coordinates("NCH") == (47.76042, -122.19050)


def test_full_name_aliases():
    assert resolve_coordinates("DISCOVERY HALL") == resolve_coordinates("DISC")
    assert resolve_coordinates("LIBRARY") == resolve_coordinates("LIB")
    assert resolve_coordinates("HUSKY HALL") == resolve_coordinates("HH")
    assert resolve_coordinates("NORTH CREEK HALL") == resolve_coordinates("NCH")


def test_campus_fallback():
    assert resolve_coordinates("CAMPUS") == CAMPUS_CENTER
    assert resolve_coordinates("CAMPUS CENTER") == CAMPUS_CENTER


def test_unknown_building_returns_campus_center():
    assert resolve_coordinates("UNKNOWN BUILDING") == CAMPUS_CENTER
    assert resolve_coordinates("PARKING LOT Z") == CAMPUS_CENTER


def test_case_insensitive():
    assert resolve_coordinates("uw1") == resolve_coordinates("UW1")
    assert resolve_coordinates("disc") == resolve_coordinates("DISC")
    assert resolve_coordinates("library") == resolve_coordinates("LIB")


def test_whitespace_trimmed():
    assert resolve_coordinates("  UW1  ") == resolve_coordinates("UW1")


def test_partial_match():
    # "UW1" is contained in a key — should resolve to UW1 coords, not fallback
    result = resolve_coordinates("UW1 BUILDING")
    assert result != CAMPUS_CENTER
