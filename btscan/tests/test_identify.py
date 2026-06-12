from identify import (
    DeviceRecord,
    estimate_distance_yards,
    guess_type,
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


def test_name_hint_wins():
    record = make_record(name="Dorothy's AirPods Pro")
    assert guess_type(record) == "headphones"


def test_service_hint():
    record = make_record(service_uuids=["0000180D-0000-1000-8000-00805F9B34FB"])
    assert guess_type(record) == "heart-rate sensor"


def test_apple_find_my_tracker():
    record = make_record(manufacturer_data={0x004C: b"\x12\x19\x00"})
    assert guess_type(record) == "item tracker (Find My)"


def test_apple_fallback():
    record = make_record(manufacturer_data={0x004C: b"\xff"})
    assert guess_type(record) == "Apple device"


def test_unknown_type():
    assert guess_type(make_record()) == "unknown"


def test_even_realities_manufacturer():
    record = make_record(manufacturer_data={0x5245: b"S211GCBB"})
    assert manufacturer_name(record) == "Even Realities"


def test_even_glasses_name_hint():
    record = make_record(name="Even G2_32_R_B87572")
    assert guess_type(record) == "smart glasses"


def test_generic_glasses_name_hint():
    record = make_record(name="Ray-Ban Meta Glasses")
    assert guess_type(record) == "smart glasses"
