"""Pure device-identification logic: manufacturer lookup, type heuristics,
and distance estimation. No Bluetooth/radio dependencies."""

from dataclasses import dataclass


@dataclass
class DeviceRecord:
    """One detected device, decoupled from bleak's types."""

    address: str
    name: str | None
    rssi: int
    tx_power: int | None
    manufacturer_data: dict[int, bytes]  # Bluetooth SIG company ID -> payload
    service_uuids: list[str]


# Subset of Bluetooth SIG company identifiers covering common consumer
# vendors. Extend as unfamiliar IDs show up in scans.
COMPANY_IDS = {
    0x0001: "Nokia",
    0x0002: "Intel",
    0x0006: "Microsoft",
    0x000A: "Qualcomm (CSR)",
    0x000D: "Texas Instruments",
    0x0030: "ST Microelectronics",
    0x004C: "Apple",
    0x0059: "Nordic Semiconductor",
    0x0075: "Samsung",
    0x0087: "Garmin",
    0x009E: "Bose",
    0x00E0: "Google",
    0x012D: "Sony",
    0x0157: "Huami (Amazfit)",
    0x0171: "Amazon",
    0x02E5: "Espressif",
    0x038F: "Xiaomi",
    0x05A7: "Sonos",
    0x5245: "Even Realities",  # unregistered ID, ASCII "RE"
}


def manufacturer_name(record: DeviceRecord) -> str:
    if not record.manufacturer_data:
        return "unknown"
    company_id = next(iter(record.manufacturer_data))
    return COMPANY_IDS.get(company_id, f"unknown (0x{company_id:04X})")


# Log-distance path-loss model. Constants are conventional BLE values:
# -59 dBm is a typical RSSI at 1 m when the device doesn't advertise TX
# power; 41 dB is the approximate free-space loss over 1 m at 2.4 GHz.
DEFAULT_MEASURED_POWER = -59
ONE_METER_LOSS_DB = 41
PATH_LOSS_EXPONENT = 2.5  # between free space (2.0) and cluttered indoor (~3.0)
METERS_PER_YARD = 0.9144


def estimate_distance_yards(rssi: int, tx_power: int | None) -> float:
    if tx_power is not None:
        measured_power = tx_power - ONE_METER_LOSS_DB
    else:
        measured_power = DEFAULT_MEASURED_POWER
    meters = 10 ** ((measured_power - rssi) / (10 * PATH_LOSS_EXPONENT))
    return meters / METERS_PER_YARD


def proximity_label(yards: float) -> str:
    if yards <= 3:
        return "near"
    if yards <= 10:
        return "medium"
    return "far"


def within_radius(record: DeviceRecord, radius_yards: float) -> bool:
    return estimate_distance_yards(record.rssi, record.tx_power) <= radius_yards


# Heuristics checked in order: device name keywords, advertised service
# UUIDs, then Apple manufacturer-data message type (first payload byte).
NAME_HINTS = [
    ("even g", "smart glasses"),  # Even Realities G1/G2; one device per temple
    ("glasses", "smart glasses"),
    ("spectacles", "smart glasses"),
    ("airpods", "headphones"),
    ("headphone", "headphones"),
    ("buds", "earbuds"),
    ("watch", "watch"),
    ("iphone", "phone"),
    ("pixel", "phone"),
    ("galaxy", "phone"),
    ("ipad", "tablet"),
    ("macbook", "computer"),
    ("tv", "TV"),
    ("tile", "tracker"),
    ("keyboard", "keyboard"),
    ("mouse", "mouse"),
    ("speaker", "speaker"),
]

SERVICE_HINTS = {
    "0000180d-0000-1000-8000-00805f9b34fb": "heart-rate sensor",
    "00001812-0000-1000-8000-00805f9b34fb": "keyboard/mouse",
    "0000feed-0000-1000-8000-00805f9b34fb": "tracker (Tile)",
    "0000fe2c-0000-1000-8000-00805f9b34fb": "accessory (Google Fast Pair)",
}

APPLE_COMPANY_ID = 0x004C
APPLE_TYPE_HINTS = {
    0x02: "beacon (iBeacon)",
    0x06: "smart-home accessory (HomeKit)",
    0x07: "headphones/earbuds (AirPods family)",
    0x09: "speaker or TV (AirPlay)",
    0x10: "Apple device (phone/Mac)",
    0x12: "item tracker (Find My)",
}


def guess_type(record: DeviceRecord) -> str:
    name = (record.name or "").lower()
    for keyword, label in NAME_HINTS:
        if keyword in name:
            return label
    for uuid in record.service_uuids:
        label = SERVICE_HINTS.get(uuid.lower())
        if label:
            return label
    apple_payload = record.manufacturer_data.get(APPLE_COMPANY_ID)
    if apple_payload:
        return APPLE_TYPE_HINTS.get(apple_payload[0], "Apple device")
    return "unknown"
