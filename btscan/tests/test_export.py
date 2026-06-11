from export import export_payload
from test_identify import make_record


def test_payload_has_timestamp_and_count():
    records = [make_record(), make_record(rssi=-80)]
    payload = export_payload(records, "2026-06-11 16:00:00")
    assert payload["scanned_at"] == "2026-06-11 16:00:00"
    assert payload["device_count"] == 2
    assert len(payload["devices"]) == 2


def test_device_fields_present():
    record = make_record(manufacturer_data={0x004C: b"\x12\x00"}, rssi=-59, tx_power=None)
    device = export_payload([record], "x")["devices"][0]
    assert device["manufacturer"] == "Apple"
    assert device["type"] == "item tracker (Find My)"
    assert 1.0 < device["distance_yards"] < 1.2
    assert device["proximity"] == "near"
    assert device["rssi_dbm"] == -59
    assert device["tx_power_dbm"] is None
    assert device["address"] == "AA:BB:CC:DD:EE:FF"


def test_names_are_never_exported():
    record = make_record(name="Dorothy's iPhone")
    payload = export_payload([record], "x")
    assert "name" not in payload["devices"][0]
    assert "Dorothy" not in str(payload)
