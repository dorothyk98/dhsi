from identify import (
    DeviceRecord,
    estimate_distance_yards,
    manufacturer_name,
    proximity_label,
    within_radius,
)


def make_record(**overrides):
    base = dict(
        address="AA:BB:CC:DD:EE:FF",
        name=None,
        rssi=-60,
        tx_power=None,
        manufacturer_data={},
        service_uuids=[],
    )
    base.update(overrides)
    return DeviceRecord(**base)


def test_known_manufacturer():
    record = make_record(manufacturer_data={0x004C: b"\x10\x05"})
    assert manufacturer_name(record) == "Apple"


def test_unknown_company_id_shows_hex():
    record = make_record(manufacturer_data={0x9999: b""})
    assert manufacturer_name(record) == "unknown (0x9999)"


def test_no_manufacturer_data():
    assert manufacturer_name(make_record()) == "unknown"


def test_distance_at_reference_rssi_is_about_one_meter():
    # -59 dBm is the assumed RSSI at 1 m; 1 m is ~1.09 yards.
    yards = estimate_distance_yards(rssi=-59, tx_power=None)
    assert 1.0 < yards < 1.2


def test_weaker_signal_means_farther():
    assert estimate_distance_yards(-80, None) > estimate_distance_yards(-60, None)


def test_tx_power_used_when_available():
    # tx_power 0 dBm implies ~-41 dBm at 1 m, so rssi -41 should read ~1 m.
    yards = estimate_distance_yards(rssi=-41, tx_power=0)
    assert 1.0 < yards < 1.2


def test_proximity_labels():
    assert proximity_label(2) == "near"
    assert proximity_label(7) == "medium"
    assert proximity_label(18) == "far"


def test_within_radius():
    near = make_record(rssi=-59)  # ~1 yd
    far = make_record(rssi=-95)   # ~30 yd
    assert within_radius(near, 10)
    assert not within_radius(far, 10)
