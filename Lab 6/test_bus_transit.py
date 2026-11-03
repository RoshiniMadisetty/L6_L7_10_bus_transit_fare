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



# ---------- Extra tests for branch coverage ----------

def test_empty_manifest_list():
    # outer for-loop never entered
    assert process_commute_manifest([], 1.0) == {"total_fare": 0.0, "status": "ZERO_RIDERSHIP"}


def test_missing_route_active_defaults_to_inactive():
    result = process_commute_manifest([{"commuters": [c(1)]}], 1.0)
    assert result["status"] == "ZERO_RIDERSHIP"


def test_active_route_with_no_commuters_key():
    # route_type defaults to local, commuters defaults to [] (inner loop never entered)
    result = process_commute_manifest([{"route_active": True}], 1.0)
    assert result["status"] == "ZERO_RIDERSHIP"


def test_empty_commuter_dict_uses_defaults():
    # zones=1, type=regular, blacklisted=False -> 2.5 + 1 = 3.5
    result = process_commute_manifest([{"route_active": True, "commuters": [{}]}], 1.0)
    assert result["total_fare"] == pytest.approx(3.5)
    assert result["status"] == "COMPLETED"


def test_negative_zones_rejected():
    result = process_commute_manifest([m("local", [c(-2)])], 1.0)
    assert result["status"] == "ZERO_RIDERSHIP"


def test_exactly_four_rejections_is_not_audit():
    commuters = [c(0)] * 4 + [c(1)]
    result = process_commute_manifest([m("local", commuters)], 1.0)
    assert result["status"] == "COMPLETED"
    assert result["total_fare"] == pytest.approx(3.5)


def test_zero_booking_fee_is_valid():
    result = process_commute_manifest([m("local", [c(1)], priority=True)], 0)
    assert result["total_fare"] == pytest.approx(3.5)


def test_express_blacklisted_with_priority_pays_only_fee():
    # break resets fare to 0, then priority fee 1.5 is still added
    result = process_commute_manifest([m("express", [c(1, blacklisted=True)], priority=True)], 1.5)
    assert result["total_fare"] == pytest.approx(1.5)
    assert result["status"] == "COMPLETED"


def test_senior_on_express_and_student_on_local():
    # senior express: (6 + 0.5) * 0.7 = 4.55 ; student local: (2.5 + 0.5) * 0.5 = 1.5
    manifests = [m("express", [c(1, "senior")]), m("local", [c(1, "student")])]
    result = process_commute_manifest(manifests, 1.0)
    assert result["total_fare"] == pytest.approx(6.05)


def test_regular_shuttle_and_multiple_manifests():
    # shuttle regular zones 3: 4 + 3 = 7 ; inactive manifest ignored
    manifests = [m("shuttle", [c(3)]), m("express", [c(1)], active=False)]
    result = process_commute_manifest(manifests, 1.0)
    assert result["total_fare"] == pytest.approx(7.0)


# ---- turnstiles ----

def test_turnstile_streak_resets_after_good_reading():
    assert inspect_smartcard_turnstiles([[4, 1, 4]]) == "OPERATIONAL"


def test_turnstile_exactly_three_failures_is_not_a_failure():
    assert inspect_smartcard_turnstiles([[3, 3, 3]]) == "OPERATIONAL"


def test_turnstile_device_with_no_readings():
    assert inspect_smartcard_turnstiles([[]]) == "OPERATIONAL"


def test_turnstile_jam_on_second_device():
    assert inspect_smartcard_turnstiles([[1], [4, 4]]) == "TURNSTILE_JAM"


def test_turnstile_streak_does_not_carry_across_devices():
    assert inspect_smartcard_turnstiles([[4], [4]]) == "OPERATIONAL"


def test_turnstile_single_failure():
    assert inspect_smartcard_turnstiles([[5]]) == "OPERATIONAL"