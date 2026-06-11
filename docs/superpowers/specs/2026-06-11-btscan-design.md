# btscan — Minimal Bluetooth Device Scanner

**Date:** 2026-06-11
**Status:** Approved design, pending implementation

## Purpose

A minimal Python command-line app that scans for Bluetooth Low Energy (BLE)
devices near the user's Mac and reports what they are: name, manufacturer, a
best-effort device-type guess, estimated distance, and raw signal details.

## Scope and platform

- Runs on macOS using the Mac's built-in Bluetooth radio.
- Detects **BLE** devices only (covers nearly all modern devices: phones,
  earbuds, watches, trackers, beacons, TVs). Classic-Bluetooth-only devices
  are out of scope.
- Radio range is roughly 25–30 yards in open air; the app cannot extend or
  precisely bound that range, but it can filter results by estimated distance
  (see `--radius`).

## Modes of operation

| Mode | Command | Behavior |
|------|---------|----------|
| One-shot (default) | `python app.py` | Scan ~10 seconds, print a table, exit |
| Live | `python app.py --watch` | Continuously refreshing table until Ctrl+C |
| Periodic | `python app.py --every N` | One ~10-second scan every N minutes, each printed as a fresh timestamped table, until Ctrl+C |

- `--watch` and `--every` are mutually exclusive; passing both is an error.
- `--every` takes a positive number of minutes (e.g. `--every 15`).

## Options

- `--radius {10,15,20,25}` — only show devices whose **estimated** distance is
  within that many yards. Default: no filter (show everything in radio range).
  Works in all three modes. The cutoff is approximate: RSSI-based distance
  estimates can be off by several yards (walls, bodies, pockets weaken signal
  and make devices look farther away).

## Output: one row per detected device

| Column | Source | Notes |
|--------|--------|-------|
| Name | Advertised local name | `(hidden)` when not broadcast |
| Manufacturer | Bluetooth SIG company ID in manufacturer data | e.g. Apple, Samsung, Garmin; `unknown` if absent/unrecognized |
| Type | Heuristic from advertised services and appearance data | headphones, watch, phone, tracker, beacon, etc.; `unknown` fallback |
| Distance | Path-loss estimate from RSSI + TX power | Shown as `~N yd` plus near/medium/far label |
| RSSI | Scan result | Signal strength in dBm |
| TX power | Advertisement, when present | The device's broadcast transmit power |
| Address | Scan result | Most devices randomize this for privacy |

Honest limitation: a passive scanner cannot measure a device's data speed —
that is only negotiated during an active connection. TX power and RSSI are
the observable "power" figures, so those are reported.

## Architecture

New `btscan/` folder at the repo root:

- `app.py` — CLI argument parsing (argparse) and table rendering (`rich`);
  owns the three mode loops.
- `scanner.py` — async BLE scan via `bleak` (`BleakScanner`); returns a list
  of plain device-record dicts/dataclasses so the rest of the app never
  touches bleak types.
- `identify.py` — pure logic, no radio: manufacturer lookup table (company ID
  → name), device-type heuristics, and RSSI → distance estimation.
- `tests/` — unit tests for `identify.py` (manufacturer lookup, type
  heuristics, distance math, radius filtering). Scanning itself is not unit
  tested (requires hardware).

Dependencies: `bleak`, `rich` (in `btscan/requirements.txt`).

## Error handling

- Bluetooth off or unavailable → clear message telling the user to turn it on.
- macOS Bluetooth permission denied → message explaining how to grant it
  (System Settings → Privacy & Security → Bluetooth). First run will trigger
  the standard macOS permission prompt; this is expected.
- No devices found → friendly "no devices detected" message, not an empty table.
- Ctrl+C in live/periodic mode → clean exit, no traceback.

## Web export and GitHub Pages (added 2026-06-11)

- `--export` flag: after each scan (any mode), also write results to
  `btscan/scan.json`.
- **Privacy:** device names are never written to the export — exports are
  meant to be published. All other columns are included.
- `btscan/index.html`: self-contained static page (no frameworks) that
  describes the project and renders the latest `scan.json` as a table
  (manufacturer, type, distance, proximity, RSSI, TX power, address) with
  the scan timestamp. Includes the 3-command publish recipe.
- GitHub Pages serves the repo's `main` branch root; the page lives at
  `https://dorothyk98.github.io/dhsi/btscan/`. Results are a pushed
  snapshot, not live data.

## Success criteria

- Running `python app.py` on a Mac with Bluetooth on prints a table of nearby
  BLE devices with all seven columns populated where data is available.
- `--watch`, `--every 15`, and `--radius` behave as described above.
- Unit tests for the pure-logic module pass without Bluetooth hardware.
