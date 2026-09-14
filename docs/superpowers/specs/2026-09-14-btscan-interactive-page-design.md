# btscan interactive results page — design

Date: 2026-09-14

## Problem

`btscan/index.html` renders the published `scan.json` as a static dump —
41 devices in seven tables grouped by type, with no way to narrow, search,
sort, or see signal strength at a glance. Reading it means scrolling and
comparing numbers by eye. The page also gives no sign of how old the
snapshot is; as of this writing it shows a 2026-06-12 scan without saying so.

## Goal

Make the published page interactive: filter, search, sort, and visualize the
latest scan entirely client-side.

## Non-goals

- Live scanning from the browser. The page renders a pushed snapshot; the
  Python CLI remains the only scanner.
- Any change to `app.py`, `scanner.py`, `identify.py`, `export.py`,
  `publish.sh`, or the `scan.json` format.
- Historical/trend data across scans.

## Approach

Keep `btscan/index.html` a single self-contained file with inline CSS and
JS, no frameworks and no build step — extending the pattern the page already
uses. The script is organized into three clearly separated regions: state,
a pure filter/sort pipeline, and renderers.

Considered and rejected: splitting into `index.html` + `btscan.css` +
`btscan.js`. Cleaner separation, but the original design called for a
self-contained page and that property was kept deliberately.

## Data characteristics driving the design

Measured against the published 41-device scan:

- `distance_yards` spans 0.8 to 629.3, while the radio's usable range is
  ~25-30 yd. The long tail is signal noise, so a linear distance slider
  would spend nearly all its travel on a handful of meaningless outliers.
- 11 distinct `manufacturer` strings, six of them one-off `unknown (0x….)`
  codes. One chip per string would crowd out the vendors that matter.
- `rssi_dbm` spans -103 to -54, a usable range for a fixed-scale bar.
- `tx_power_dbm` is frequently null and must keep rendering as an em dash.

## Controls

1. **Radius** — segmented buttons `10 / 15 / 20 / 25 / All yd`, mirroring the
   CLI's `--radius` choices rather than a free slider. Defaults to All.
2. **Proximity** — `near` / `medium` / `far` toggle chips, all enabled by
   default, reusing the existing `.near` / `.medium` / `.far` colors.
3. **Search** — free-text box, case-insensitive substring match against
   manufacturer, type, and address.
4. **Manufacturer chips** — derived from the loaded data with per-chip
   counts, ordered by count descending. Manufacturers with 2 or more devices
   get their own chip; every remaining one-off collapses into a single
   `Other` chip. Multi-select; no selection means no manufacturer filtering.
5. **Sortable columns** — clicking a column header cycles ascending →
   descending, with an arrow indicator on the active column.
6. **Reset** — clears all filters and sorting back to defaults.

All filters combine with AND.

## Grouping vs. sorting

The current view groups devices by type. A column sort contradicts that, so:

- No active sort → keep the existing group-by-type view, each group its own
  table, groups ordered by device count descending.
- Active sort → flatten into one table sorted by the chosen column.
- A `Group by type` toggle switches back, clearing the active sort.

## Visualizations

**Per-row signal bar.** An inline bar in each row sized from `rssi_dbm`
against a fixed -103…-54 dBm scale and colored by proximity class.

**Radar plot.** Concentric rings at 10/15/20/25 yd with an outer band for
everything beyond 25 yd, each visible device a dot placed at radius =
its distance. Dot angle is derived from a hash of the address so it stays
stable between renders. Hovering a dot highlights the matching table row.
The plot reflects the current filters.

BLE signal yields distance only, never bearing, so the angle carries no
information. In keeping with the page's "Honest caveats" section, the plot
is captioned: *"Angle is arbitrary — signal strength gives distance only,
not direction."*

## Summary line and staleness

The meta line reads `N of M devices · scanned <timestamp> (<relative>)`,
where `<relative>` is a humanized age ("3 months ago"), making a stale
snapshot visible without reading the date.

## State and rendering

A single `state` object holds `search`, `radius`, `proximity`,
`manufacturers`, `sort`, and `groupByType`. Every control mutates `state`
and calls one `render()`, which derives the filtered/sorted list and repaints
the summary, radar, and table. Filtering and sorting are pure functions of
`(devices, state)`.

## Error handling

- `scan.json` missing or unparseable → the existing failure message, with
  controls hidden rather than rendered dead.
- `scan.json` present but zero devices → an explicit "no devices in this
  scan" message.
- Filters match nothing → "No devices match these filters" plus a reset
  button, not an empty table.
- `tx_power_dbm: null` → em dash, as today.

## Cut (YAGNI)

- URL/hash state for shareable filtered views
- Filter persistence across reloads
- CSV export

## Verification

Node is not installed on the target machine, so there is no JS unit-test
runner; the Python test suite covers the scanner and is unaffected by this
change. Verification is a manual browser pass over the real 41-device
`scan.json`, exercising each control and confirming:

- each filter narrows the set correctly, and filters compose
- each column sorts both directions
- the grouped ↔ flat transition works in both directions
- the radar reflects filters, and hover highlights the right row
- the empty-filter state and the reset button behave
- `python -m pytest btscan/tests -v` still passes (13 tests, untouched)

## Success criteria

A reader can land on the page and, without reloading, narrow 41 devices to
the handful within 15 yards, isolate one manufacturer, sort them by signal
strength, and see at a glance how far away each one is and how old the
scan is.
