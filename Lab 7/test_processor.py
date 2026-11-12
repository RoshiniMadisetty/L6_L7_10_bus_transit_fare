import math
from hypothesis import given, strategies as st
from processor import parse_transit_corridor, lookup_concession_discount, compute_passenger_density


@given(st.text() | st.none())
def test_parse_transit_corridor_no_crash(s):
    try:
        result = parse_transit_corridor(s)
    except Exception as e:
        assert False, f"parse_transit_corridor crashed with: {e!r} on input {s!r}"
    assert isinstance(result, str)


@given(st.text() | st.none())
def test_lookup_concession_discount_safe(s):
    try:
        result = lookup_concession_discount(s)
    except Exception as e:
        assert False, f"lookup_concession_discount crashed with: {e!r} on input {s!r}"
    assert result is None or 0.0 <= result <= 1.0


@given(st.text() | st.none())
def test_compute_passenger_density_safe(s):
    try:
        result = compute_passenger_density(s)
    except Exception as e:
        assert False, f"compute_passenger_density crashed with: {e!r} on input {s!r}"
    assert result is None or (math.isfinite(result) and result >= 0)