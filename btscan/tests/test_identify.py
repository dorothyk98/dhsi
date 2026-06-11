from identify import DeviceRecord, manufacturer_name


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
