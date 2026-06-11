"""Export scan results to JSON for the static results page.

Device names are deliberately never written: exports are meant to be
published (e.g. on GitHub Pages)."""

import json
from datetime import datetime
from pathlib import Path

from identify import (
    DeviceRecord,
    estimate_distance_yards,
    guess_type,
    manufacturer_name,
    proximity_label,
)

EXPORT_PATH = Path(__file__).parent / "scan.json"


def export_payload(records: list[DeviceRecord], scanned_at: str) -> dict:
    devices = []
    for record in records:
        yards = estimate_distance_yards(record.rssi, record.tx_power)
        devices.append(
            {
                "manufacturer": manufacturer_name(record),
                "type": guess_type(record),
                "distance_yards": round(yards, 1),
                "proximity": proximity_label(yards),
                "rssi_dbm": record.rssi,
                "tx_power_dbm": record.tx_power,
                "address": record.address,
            }
        )
    return {
        "scanned_at": scanned_at,
        "device_count": len(devices),
        "devices": devices,
    }


def write_export(records: list[DeviceRecord], path: Path = EXPORT_PATH) -> None:
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    path.write_text(json.dumps(export_payload(records, stamp), indent=1))
