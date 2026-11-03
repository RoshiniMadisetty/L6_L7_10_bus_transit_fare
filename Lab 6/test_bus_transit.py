import pytest
from bus_transit_fare import process_commute_manifest, inspect_smartcard_turnstiles


def m(route_type, commuters, active=True, priority=False):
    return {"route_active": active, "route_type": route_type,
            "priority_boarding": priority, "commuters": commuters}


def c(zones=1, ptype="regular", blacklisted=False):
    return {"zones": zones, "type": ptype, "blacklisted": blacklisted}


# ---------- process_commute_manifest ----------

def test_single_regular_local_ride():
    manifests = [m("local", [c(2)])]
    result = process_commute_manifest(manifests, 2.0)
    assert result["total_fare"] == 4.5
    assert result["status"] == "COMPLETED"


def test_manifests_not_a_list():
    with pytest.raises(ValueError):
        process_commute_manifest("not a list", 1.0)


def test_negative_booking_fee():
    with pytest.raises(ValueError):
        process_commute_manifest([], -1.0)


def test_inactive_route_skipped():
    result = process_commute_manifest([m("local", [c()], active=False)], 1.0)
    assert result == {"total_fare": 0.0, "status": "ZERO_RIDERSHIP"}


def test_express_student():
    # (6 + 2*0.5) * 0.5 = 3.5
    result = process_commute_manifest([m("express", [c(2, "student")])], 1.0)
    assert result["total_fare"] == pytest.approx(3.5)
    assert result["status"] == "COMPLETED"


def test_shuttle_senior():
    # (4 + 2*0.5) * 0.7 = 3.5
    result = process_commute_manifest([m("shuttle", [c(2, "senior")])], 1.0)
    assert result["total_fare"] == pytest.approx(3.5)
    assert result["status"] == "COMPLETED"


def test_unknown_route_type_rejected():
    result = process_commute_manifest([m("metro", [c()])], 1.0)
    assert result["status"] == "ZERO_RIDERSHIP"


def test_zero_zones_rejected():
    result = process_commute_manifest([m("local", [c(0), c(1)])], 1.0)
    assert result["total_fare"] == pytest.approx(3.5)
    assert result["status"] == "COMPLETED"


def test_blacklisted_on_local_route_continues():
    result = process_commute_manifest([m("local", [c(1, blacklisted=True), c(1)])], 1.0)
    assert result["total_fare"] == pytest.approx(3.5)
    assert result["status"] == "COMPLETED"


def test_blacklisted_on_express_voids_manifest():
    commuters = [c(1), c(1, blacklisted=True), c(1)]
    result = process_commute_manifest([m("express", commuters)], 1.0)
    assert result == {"total_fare": 0.0, "status": "ZERO_RIDERSHIP"}


def test_priority_boarding_fee_added():
    # 2.5 + 1 = 3.5, + 2.0 fee = 5.5
    result = process_commute_manifest([m("local", [c(1)], priority=True)], 2.0)
    assert result["total_fare"] == pytest.approx(5.5)
    assert result["status"] == "COMPLETED"


def test_audit_rejected_when_more_than_four_rejections():
    commuters = [c(0)] * 5 + [c(1)]
    result = process_commute_manifest([m("local", commuters)], 1.0)
    assert result["status"] == "AUDIT_REJECTED"
    assert result["total_fare"] == pytest.approx(3.5)


# ---------- inspect_smartcard_turnstiles ----------

def test_turnstiles_no_data():
    assert inspect_smartcard_turnstiles([]) == "NO_DATA"


def test_turnstiles_jam():
    assert inspect_smartcard_turnstiles([[4, 5]]) == "TURNSTILE_JAM"


def test_turnstiles_operational():
    assert inspect_smartcard_turnstiles([[1, 2, 3]]) == "OPERATIONAL"