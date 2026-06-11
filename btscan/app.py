"""btscan: detect nearby Bluetooth Low Energy devices and report what
they are. One-shot by default; --watch for live view; --every N for a
scan every N minutes until Ctrl+C."""

import argparse
import asyncio
import sys
import time
from datetime import datetime

from bleak.exc import BleakError
from rich.console import Console
from rich.live import Live
from rich.table import Table

from identify import (
    estimate_distance_yards,
    guess_type,
    manufacturer_name,
    proximity_label,
    within_radius,
)
from scanner import scan

SCAN_SECONDS = 10.0
console = Console()

BLUETOOTH_HELP = (
    "Could not scan: {err}\n"
    "Check that Bluetooth is turned on and that your terminal has Bluetooth "
    "permission (System Settings > Privacy & Security > Bluetooth)."
)


def scan_once(duration: float = SCAN_SECONDS):
    try:
        return asyncio.run(scan(duration))
    except BleakError as err:
        console.print(BLUETOOTH_HELP.format(err=err))
        sys.exit(1)


def build_table(records, radius=None, title="Nearby Bluetooth devices"):
    """Return (table, row_count); rows outside `radius` yards are dropped."""
    table = Table(title=title)
    for column in ("Name", "Manufacturer", "Type", "Distance", "RSSI", "TX power", "Address"):
        table.add_column(column)
    rows = 0
    for record in records:
        if radius is not None and not within_radius(record, radius):
            continue
        yards = estimate_distance_yards(record.rssi, record.tx_power)
        table.add_row(
            record.name or "(hidden)",
            manufacturer_name(record),
            guess_type(record),
            f"~{yards:.0f} yd ({proximity_label(yards)})",
            f"{record.rssi} dBm",
            f"{record.tx_power} dBm" if record.tx_power is not None else "-",
            record.address,
        )
        rows += 1
    return table, rows


def run_once(radius):
    records = scan_once()
    table, rows = build_table(records, radius)
    if rows == 0:
        console.print("No devices detected. Is Bluetooth on? (--radius may also be filtering everything out.)")
    else:
        console.print(table)


def run_watch(radius):
    """Repeated short scans feeding a live-updating table. Ctrl+C stops."""
    try:
        with Live(console=console, refresh_per_second=4) as live:
            while True:
                records = scan_once(duration=3.0)
                title = f"Live scan {datetime.now():%H:%M:%S} - Ctrl+C to stop"
                table, _ = build_table(records, radius, title=title)
                live.update(table)
    except KeyboardInterrupt:
        console.print("Stopped.")


def main():
    parser = argparse.ArgumentParser(
        description="Scan for nearby Bluetooth (BLE) devices and report what they are."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--watch", action="store_true",
                      help="continuously refresh a live table until Ctrl+C")
    mode.add_argument("--every", type=float, metavar="MINUTES",
                      help="run one scan every MINUTES minutes until Ctrl+C")
    parser.add_argument("--radius", type=int, choices=[10, 15, 20, 25],
                        help="only show devices estimated within this many yards")
    args = parser.parse_args()
    if args.every is not None and args.every <= 0:
        parser.error("--every must be a positive number of minutes")

    if args.watch:
        run_watch(args.radius)
    elif args.every is not None:
        run_every(args.every, args.radius)
    else:
        run_once(args.radius)


if __name__ == "__main__":
    main()
