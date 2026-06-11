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
}


def manufacturer_name(record: DeviceRecord) -> str:
    if not record.manufacturer_data:
        return "unknown"
    company_id = next(iter(record.manufacturer_data))
    return COMPANY_IDS.get(company_id, f"unknown (0x{company_id:04X})")
