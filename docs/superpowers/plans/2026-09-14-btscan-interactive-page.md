# btscan Interactive Results Page — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn `btscan/index.html` from a static dump of the published scan into a page you can filter, search, sort, and read at a glance.

**Architecture:** One self-contained HTML file, inline CSS and JS, no frameworks and no build step. The script has three separated regions: a single `state` object, pure `(devices, state) -> devices` filter/sort functions, and renderers that repaint summary + radar + table. Every control mutates `state` and calls one `render()`.

**Tech Stack:** Vanilla ES2020 in one file. Served by GitHub Pages as a static asset. No dependencies. Python scanner is untouched.

**Testing note:** Node is not installed on this machine, so there is no JS unit-test runner and this plan is not TDD. Each task ends with a concrete browser check run against the real 41-device `btscan/scan.json` via a local server. The Python suite (`python -m pytest btscan/tests -v`, 13 tests) must keep passing but is not touched by any task.

**Local server for every verification step:**

```bash
python3 -m http.server 8009
```

Then open `http://localhost:8009/btscan/`. Leave it running across all tasks.

---

## File Structure

- Modify: `btscan/index.html` — the only file this plan changes. Its `<style>` grows a controls/radar/bar section; its `<script>` is replaced wholesale by the state/filter/render structure.

No other file is created or modified. `scan.json`'s format is an input contract and does not change.

---

### Task 1: Page shell, controls markup, and CSS

**Files:**
- Modify: `btscan/index.html` (`<style>` block, and the `<h2>Latest published scan</h2>` section)

- [ ] **Step 1: Add CSS for controls, chips, bars, radar, and empty state**

Append inside the existing `<style>`, keeping the current rules untouched:

```css
  .controls { background: #f9f9f9; border: 1px solid #e3e3e3; border-radius: 6px;
              padding: 14px 16px; margin-top: 12px; display: grid; gap: 12px; }
  .ctl-row { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; }
  .ctl-label { font-size: 0.8em; color: #666; text-transform: uppercase;
               letter-spacing: 0.04em; min-width: 92px; }
  #search { flex: 1; min-width: 180px; padding: 6px 10px; font-size: 0.9em;
            border: 1px solid #ccc; border-radius: 6px; font-family: inherit; }
  .chip { padding: 4px 10px; font-size: 0.85em; border: 1px solid #ccc;
          border-radius: 999px; background: #fff; cursor: pointer; font-family: inherit; }
  .chip:hover { border-color: #888; }
  .chip[aria-pressed="true"] { background: #222; color: #fff; border-color: #222; }
  .chip .n { opacity: 0.6; margin-left: 4px; }
  .seg { display: inline-flex; border: 1px solid #ccc; border-radius: 6px; overflow: hidden; }
  .seg button { padding: 4px 12px; font-size: 0.85em; border: none; background: #fff;
                cursor: pointer; border-right: 1px solid #ddd; font-family: inherit; }
  .seg button:last-child { border-right: none; }
  .seg button[aria-pressed="true"] { background: #222; color: #fff; }
  #reset { margin-left: auto; padding: 4px 12px; font-size: 0.85em; border: 1px solid #ccc;
           border-radius: 6px; background: #fff; cursor: pointer; font-family: inherit; }
  th.sortable { cursor: pointer; user-select: none; white-space: nowrap; }
  th.sortable:hover { background: #e6e6e6; }
  th .arrow { color: #888; font-size: 0.8em; }
  .bar { display: inline-block; height: 8px; border-radius: 2px; vertical-align: middle;
         min-width: 2px; }
  .bar.near { background: #1a7f37; } .bar.medium { background: #9a6700; }
  .bar.far { background: #bbb; }
  tr.hot td { background: #fff3cd !important; }
  #radar-wrap { margin-top: 16px; }
  #radar { display: block; margin: 0 auto; max-width: 100%; }
  #radar circle.dev { cursor: pointer; }
  .radar-caption { color: #666; font-size: 0.85em; text-align: center; margin-top: 4px; }
  .empty { background: #f4f4f4; border-radius: 6px; padding: 20px; text-align: center;
           color: #666; margin-top: 12px; }
```

- [ ] **Step 2: Replace the results section markup**

Replace this:

```html
<h2>Latest published scan</h2>
<p id="scan-meta">Loading scan results…</p>
<div id="results"></div>
```

with:

```html
<h2>Latest published scan</h2>
<div class="controls" id="controls" hidden>
  <div class="ctl-row">
    <span class="ctl-label">Search</span>
    <input id="search" type="search" placeholder="manufacturer, type, or address…"
           autocomplete="off" />
    <button id="reset" type="button">Reset</button>
  </div>
  <div class="ctl-row">
    <span class="ctl-label">Within</span>
    <span class="seg" id="radius"></span>
    <span class="ctl-label" style="min-width:auto">Proximity</span>
    <span id="proximity"></span>
  </div>
  <div class="ctl-row">
    <span class="ctl-label">Maker</span>
    <span id="makers"></span>
  </div>
  <div class="ctl-row">
    <span class="ctl-label">View</span>
    <button class="chip" id="group-toggle" type="button" aria-pressed="true">Group by type</button>
  </div>
</div>
<p id="scan-meta">Loading scan results…</p>
<div id="radar-wrap" hidden>
  <svg id="radar" viewBox="0 0 360 360" width="360" height="360" role="img"
       aria-label="Devices by estimated distance"></svg>
  <p class="radar-caption">Angle is arbitrary — signal strength gives distance
    only, not direction.</p>
</div>
<div id="results"></div>
```

- [ ] **Step 3: Verify the shell renders**

Load `http://localhost:8009/btscan/`. The controls panel is still `hidden` (no JS yet wires it), the prose sections are unchanged, and the page has no console errors.

- [ ] **Step 4: Commit**

```bash
git add btscan/index.html
git commit -m "feat(page): add controls shell and styles for interactive scan view"
```

---

### Task 2: Data load, facets, and the summary line

**Files:**
- Modify: `btscan/index.html` (`<script>`)

- [ ] **Step 1: Replace the whole `<script>` body with state, load, and facet derivation**

```js
const PROXIMITIES = ["near", "medium", "far"];
const RADII = [10, 15, 20, 25];
const RSSI_MIN = -105, RSSI_MAX = -50;

const state = {
  search: "", radius: null, proximity: new Set(PROXIMITIES),
  makers: new Set(), sort: null, groupByType: true,
};

let DEVICES = [], SCAN = null, MAKER_BUCKETS = new Map();

// Manufacturers with 2+ devices get their own chip; the rest collapse to "Other".
function deriveMakers(devices) {
  const counts = new Map();
  for (const d of devices) counts.set(d.manufacturer, (counts.get(d.manufacturer) || 0) + 1);
  const buckets = new Map();
  const other = [];
  for (const [name, n] of counts) (n >= 2 ? buckets.set(name, [name]) : other.push(name));
  const sorted = new Map([...buckets.entries()].sort(
    (a, b) => counts.get(b[0]) - counts.get(a[0])));
  if (other.length) sorted.set("Other", other);
  return sorted;
}

function relativeAge(stamp) {
  const then = new Date(stamp.replace(" ", "T"));
  if (isNaN(then)) return null;
  const days = Math.floor((Date.now() - then) / 86400000);
  if (days < 1) return "today";
  if (days === 1) return "yesterday";
  if (days < 30) return `${days} days ago`;
  const months = Math.round(days / 30);
  if (months < 12) return `${months} month${months === 1 ? "" : "s"} ago`;
  const years = Math.round(days / 365);
  return `${years} year${years === 1 ? "" : "s"} ago`;
}
```

- [ ] **Step 2: Add the fetch and the meta renderer**

```js
function renderMeta(shown) {
  const age = relativeAge(SCAN.scanned_at);
  const count = shown === DEVICES.length
    ? `${DEVICES.length} devices`
    : `${shown} of ${DEVICES.length} devices`;
  document.getElementById("scan-meta").textContent =
    `${count} · scanned ${SCAN.scanned_at}${age ? ` (${age})` : ""} (scanner's local time)`;
}

fetch("scan.json")
  .then((r) => { if (!r.ok) throw new Error("scan.json not found"); return r.json(); })
  .then((scan) => {
    SCAN = scan;
    DEVICES = scan.devices || [];
    if (!DEVICES.length) {
      document.getElementById("scan-meta").textContent =
        `No devices in this scan (scanned ${scan.scanned_at}).`;
      return;
    }
    MAKER_BUCKETS = deriveMakers(DEVICES);
    document.getElementById("controls").hidden = false;
    document.getElementById("radar-wrap").hidden = false;
    buildControls();
    render();
  })
  .catch((err) => {
    document.getElementById("scan-meta").textContent =
      "No scan published yet (" + err.message + ").";
  });
```

- [ ] **Step 3: Verify in the browser**

Reload the page. Expected: the meta line reads `41 devices · scanned 2026-06-12 23:44:08 (3 months ago) (scanner's local time)`. `buildControls`/`render` are not defined yet, so a `ReferenceError` in the console at this step is expected and is fixed by Task 3.

- [ ] **Step 4: Commit**

```bash
git add btscan/index.html
git commit -m "feat(page): load scan, derive maker facets, show snapshot age"
```

---

### Task 3: Filter pipeline, controls wiring, and table render

**Files:**
- Modify: `btscan/index.html` (`<script>`)

- [ ] **Step 1: Add the pure filter function**

```js
function applyFilters(devices, s) {
  const q = s.search.trim().toLowerCase();
  const names = new Set();
  for (const key of s.makers) for (const n of MAKER_BUCKETS.get(key) || []) names.add(n);
  return devices.filter((d) => {
    if (s.radius !== null && d.distance_yards > s.radius) return false;
    if (!s.proximity.has(d.proximity)) return false;
    if (names.size && !names.has(d.manufacturer)) return false;
    if (q && !`${d.manufacturer} ${d.type} ${d.address}`.toLowerCase().includes(q)) return false;
    return true;
  });
}
```

- [ ] **Step 2: Build the controls**

```js
function chip(label, count, pressed, onClick) {
  const b = document.createElement("button");
  b.type = "button";
  b.className = "chip";
  b.setAttribute("aria-pressed", String(pressed));
  b.innerHTML = count === null ? label : `${label}<span class="n">${count}</span>`;
  b.addEventListener("click", () => { onClick(); render(); });
  return b;
}

function buildControls() {
  const radius = document.getElementById("radius");
  radius.replaceChildren(...[...RADII, null].map((r) => {
    const b = document.createElement("button");
    b.type = "button";
    b.textContent = r === null ? "All" : `${r} yd`;
    b.setAttribute("aria-pressed", String(state.radius === r));
    b.addEventListener("click", () => { state.radius = r; render(); });
    return b;
  }));

  const prox = document.getElementById("proximity");
  prox.replaceChildren(...PROXIMITIES.map((p) => chip(
    p, DEVICES.filter((d) => d.proximity === p).length, state.proximity.has(p),
    () => state.proximity.has(p) ? state.proximity.delete(p) : state.proximity.add(p))));

  const makers = document.getElementById("makers");
  makers.replaceChildren(...[...MAKER_BUCKETS.entries()].map(([key, names]) => chip(
    key, DEVICES.filter((d) => names.includes(d.manufacturer)).length, state.makers.has(key),
    () => state.makers.has(key) ? state.makers.delete(key) : state.makers.add(key))));

  document.getElementById("search").addEventListener("input", (e) => {
    state.search = e.target.value; render();
  });
  document.getElementById("group-toggle").addEventListener("click", () => {
    state.groupByType = !state.groupByType;
    if (state.groupByType) state.sort = null;
    render();
  });
  document.getElementById("reset").addEventListener("click", () => {
    state.search = ""; state.radius = null; state.proximity = new Set(PROXIMITIES);
    state.makers = new Set(); state.sort = null; state.groupByType = true;
    document.getElementById("search").value = "";
    render();
  });
}

function syncControls() {
  [...document.getElementById("radius").children].forEach((b, i) => {
    const r = i < RADII.length ? RADII[i] : null;
    b.setAttribute("aria-pressed", String(state.radius === r));
  });
  [...document.getElementById("proximity").children].forEach((b, i) =>
    b.setAttribute("aria-pressed", String(state.proximity.has(PROXIMITIES[i]))));
  const keys = [...MAKER_BUCKETS.keys()];
  [...document.getElementById("makers").children].forEach((b, i) =>
    b.setAttribute("aria-pressed", String(state.makers.has(keys[i]))));
  document.getElementById("group-toggle")
    .setAttribute("aria-pressed", String(state.groupByType));
}
```

- [ ] **Step 3: Add the row/table renderers and `render()`**

```js
const COLUMNS = [
  { key: "manufacturer", label: "Manufacturer" },
  { key: "distance_yards", label: "Distance" },
  { key: "proximity", label: "Proximity" },
  { key: "rssi_dbm", label: "Signal (RSSI)" },
  { key: "tx_power_dbm", label: "TX power" },
  { key: "address", label: "Address" },
];

function rowHtml(d) {
  const pct = Math.max(0, Math.min(1, (d.rssi_dbm - RSSI_MIN) / (RSSI_MAX - RSSI_MIN)));
  return `<tr data-addr="${d.address}">
    <td>${d.manufacturer}</td>
    <td>~${d.distance_yards} yd</td>
    <td class="${d.proximity}">${d.proximity}</td>
    <td><span class="bar ${d.proximity}" style="width:${Math.round(pct * 60)}px"></span>
        ${d.rssi_dbm} dBm</td>
    <td>${d.tx_power_dbm ?? "—"}</td>
    <td><code>${d.address.slice(0, 8)}…</code></td>
  </tr>`;
}

function tableHtml(devices) {
  const heads = COLUMNS.map((c) => {
    const active = state.sort && state.sort.key === c.key;
    const arrow = active ? (state.sort.dir === "asc" ? " ▲" : " ▼") : "";
    return `<th class="sortable" data-key="${c.key}">${c.label}<span class="arrow">${arrow}</span></th>`;
  }).join("");
  return `<table><thead><tr>${heads}</tr></thead>
    <tbody>${devices.map(rowHtml).join("")}</tbody></table>`;
}

function render() {
  syncControls();
  const shown = applyFilters(DEVICES, state);
  renderMeta(shown.length);
  const results = document.getElementById("results");

  if (!shown.length) {
    results.innerHTML = `<div class="empty">No devices match these filters.</div>`;
    drawRadar([]);
    return;
  }

  if (state.groupByType) {
    const groups = new Map();
    for (const d of shown) {
      if (!groups.has(d.type)) groups.set(d.type, []);
      groups.get(d.type).push(d);
    }
    results.innerHTML = [...groups.entries()]
      .sort((a, b) => b[1].length - a[1].length)
      .map(([type, list]) => {
        list.sort((a, b) => a.distance_yards - b.distance_yards);
        return `<h3>${type} <span class="count">${list.length} device${
          list.length === 1 ? "" : "s"}</span></h3>${tableHtml(list)}`;
      }).join("");
  } else {
    results.innerHTML = tableHtml(sortDevices(shown, state.sort));
  }

  wireTable();
  drawRadar(shown);
}
```

- [ ] **Step 4: Verify filtering in the browser**

Reload. Check each in turn:
- `41 devices` shown, grouped by type as before, now with signal bars.
- Click `15 yd` → meta reads `N of 41 devices`, all rows ≤ 15 yd.
- Click the `far` chip off → no `far` rows remain.
- Type `sonos` in search → only the Sonos device.
- Click the `Apple` maker chip → 26 devices.
- Combine two filters → both apply.
- Filter to nothing → "No devices match these filters."
- `Reset` → back to 41.

- [ ] **Step 5: Commit**

```bash
git add btscan/index.html
git commit -m "feat(page): filter by search, radius, proximity, and manufacturer"
```

---

### Task 4: Column sorting and the grouped/flat switch

**Files:**
- Modify: `btscan/index.html` (`<script>`)

- [ ] **Step 1: Add `sortDevices` and `wireTable`**

```js
function sortDevices(devices, sort) {
  if (!sort) return devices.slice().sort((a, b) => a.distance_yards - b.distance_yards);
  const dir = sort.dir === "asc" ? 1 : -1;
  return devices.slice().sort((a, b) => {
    let x = a[sort.key], y = b[sort.key];
    // Nulls (tx_power_dbm) always sort last, whichever direction is active.
    if (x === null || x === undefined) return 1;
    if (y === null || y === undefined) return -1;
    if (typeof x === "string") return x.localeCompare(y) * dir;
    return (x - y) * dir;
  });
}

function wireTable() {
  document.querySelectorAll("th.sortable").forEach((th) => {
    th.addEventListener("click", () => {
      const key = th.dataset.key;
      state.sort = state.sort && state.sort.key === key
        ? { key, dir: state.sort.dir === "asc" ? "desc" : "asc" }
        : { key, dir: "asc" };
      state.groupByType = false;   // sorting flattens the grouped view
      render();
    });
  });
}
```

- [ ] **Step 2: Verify sorting in the browser**

Reload. Check:
- Click `Distance` → the grouped headings disappear, one flat table, nearest first, `▲` on Distance.
- Click `Distance` again → farthest first, `▼`.
- Click `Manufacturer` → alphabetical.
- Click `TX power` → rows with `—` sit at the bottom in both directions.
- Click `Group by type` → groups return and the arrow clears.

- [ ] **Step 3: Commit**

```bash
git add btscan/index.html
git commit -m "feat(page): sortable columns with grouped/flat switching"
```

---

### Task 5: Radar plot and row highlighting

**Files:**
- Modify: `btscan/index.html` (`<script>`)

- [ ] **Step 1: Add the radar renderer**

Distances run 0.8 to 629 yd against a ~25 yd usable radio range, so the scale
is linear to 25 yd and everything beyond is pinned to an outer "25+" band.

```js
const SVG_NS = "http://www.w3.org/2000/svg";
const CX = 180, CY = 180, R_MAX = 150, OUTER = 165;

function el(name, attrs) {
  const n = document.createElementNS(SVG_NS, name);
  for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v);
  return n;
}

// Stable pseudo-angle from the address — deterministic, but meaningless:
// BLE gives distance, never bearing. The caption says so on the page.
function angleFor(address) {
  let h = 0;
  for (let i = 0; i < address.length; i++) h = (h * 31 + address.charCodeAt(i)) % 3600;
  return (h / 3600) * Math.PI * 2;
}

function drawRadar(devices) {
  const svg = document.getElementById("radar");
  svg.replaceChildren();
  for (const ring of RADII) {
    svg.appendChild(el("circle", { cx: CX, cy: CY, r: (ring / 25) * R_MAX,
      fill: "none", stroke: "#e0e0e0" }));
    svg.appendChild(el("text", { x: CX + 3, y: CY - (ring / 25) * R_MAX + 11,
      fill: "#aaa", "font-size": "9" })).textContent = `${ring} yd`;
  }
  svg.appendChild(el("circle", { cx: CX, cy: CY, r: OUTER, fill: "none",
    stroke: "#e0e0e0", "stroke-dasharray": "3 3" }));
  svg.appendChild(el("text", { x: CX + 3, y: CY - OUTER + 11, fill: "#aaa",
    "font-size": "9" })).textContent = "25+ yd";
  svg.appendChild(el("circle", { cx: CX, cy: CY, r: 2, fill: "#999" }));

  const fill = { near: "#1a7f37", medium: "#9a6700", far: "#bbb" };
  for (const d of devices) {
    const a = angleFor(d.address);
    const r = d.distance_yards > 25 ? OUTER : (d.distance_yards / 25) * R_MAX;
    const dot = el("circle", { cx: CX + Math.cos(a) * r, cy: CY + Math.sin(a) * r,
      r: 5, fill: fill[d.proximity] || "#bbb", "fill-opacity": "0.75", class: "dev" });
    dot.dataset.addr = d.address;
    dot.addEventListener("mouseenter", () => highlight(d.address, true));
    dot.addEventListener("mouseleave", () => highlight(d.address, false));
    const title = el("title", {});
    title.textContent = `${d.manufacturer} · ${d.type} · ~${d.distance_yards} yd · ${d.rssi_dbm} dBm`;
    dot.appendChild(title);
    svg.appendChild(dot);
  }
}

function highlight(address, on) {
  const row = document.querySelector(`tr[data-addr="${address}"]`);
  if (!row) return;
  row.classList.toggle("hot", on);
  if (on) row.scrollIntoView({ block: "nearest", behavior: "smooth" });
}
```

- [ ] **Step 2: Verify the radar in the browser**

Reload. Check:
- Rings at 10/15/20/25 yd plus a dashed `25+` band; 41 dots, colored by proximity.
- Hovering a dot shows a tooltip and highlights its table row in yellow.
- Applying a filter (e.g. `15 yd`) removes the excluded dots.
- The caption about arbitrary angle is present under the plot.

- [ ] **Step 3: Commit**

```bash
git add btscan/index.html
git commit -m "feat(page): filter-aware radar plot with row highlighting"
```

---

### Task 6: Full verification pass

**Files:** none modified unless a defect is found.

- [ ] **Step 1: Confirm the Python suite is untouched and green**

Run: `python3 -m pytest btscan/tests -v`
Expected: 13 passed.

- [ ] **Step 2: Walk the spec's success criteria in the browser**

Starting from a fresh load, in one session without reloading:
narrow to devices within 15 yd → isolate one manufacturer → sort by RSSI →
confirm the radar and meta line both track every step → Reset returns to
41 devices, grouped, unsorted.

- [ ] **Step 3: Check the failure paths**

- Temporarily rename `scan.json`, reload: the page reads "No scan published
  yet (scan.json not found)." and the controls and radar stay hidden. Restore it.
- Filter to an empty set: the empty-state message and a working Reset.

- [ ] **Step 4: Commit any fixes**

```bash
git add btscan/index.html
git commit -m "fix: adjustments from the interactive page verification pass"
```

Skip this commit if nothing needed fixing.

- [ ] **Step 5: Publish**

```bash
git push
```

The page is live at https://dorothyk98.github.io/dhsi/btscan/ within a minute.
