# 🌋 lahar-watch

**Washington State LAHAR Sensor Network — Command Dashboard & Data Pipeline**

[![Fetch Sensor Data & Deploy](https://github.com/bdgroves/lahar-watch/actions/workflows/deploy.yml/badge.svg)](https://github.com/bdgroves/lahar-watch/actions/workflows/deploy.yml)
![GitHub Pages](https://img.shields.io/badge/pages-live-22c55e?logo=github)
![Python](https://img.shields.io/badge/python-3.11+-3b82f6?logo=python&logoColor=white)
![pixi](https://img.shields.io/badge/env-pixi-f97316)

Live dashboard tracking the Mt. Rainier lahar detection network across all major drainages — Puyallup, Carbon, White River, Nisqually, and Tahoma Creek.

🔗 **[Live Dashboard → bdgroves.github.io/lahar-watch](https://bdgroves.github.io/lahar-watch)**

| Page | Description |
|---|---|
| [`index.html`](https://bdgroves.github.io/lahar-watch/) | Main sensor command dashboard |
| [`seismic.html`](https://bdgroves.github.io/lahar-watch/seismic.html) | Live PNSN helicorders + seismicity table |
| [`travel-time.html`](https://bdgroves.github.io/lahar-watch/travel-time.html) | Interactive lahar travel-time calculator |
| [`status.html`](https://bdgroves.github.io/lahar-watch/status.html) | Pipeline health, API status, data freshness |

---

## What this is

Mt. Rainier is considered the most dangerous volcano in the United States. ~80,000 people live in active lahar-hazard zones across 6 river drainages. The USGS and Pierce County Emergency Management operate a network of seismic, infrasound, and acoustic flow monitor (AFM) sensors that can detect a lahar and alert emergency operations within 10 seconds — giving downstream communities 40 minutes to 3 hours of warning.

This project:
- **Visualizes** the sensor network on a live stakeholder dashboard
- **Fetches** real-time data from USGS and PNSN APIs twice daily
- **Tracks** volcanic alert level, recent seismicity, stream gauge levels, and station status
- **Deploys** automatically to GitHub Pages via GitHub Actions

---

## Data Sources

| Source | Data | Endpoint |
|---|---|---|
| USGS Volcano Notifications | Alert level, activity notices | `volcanoes.usgs.gov/vns2/api` |
| USGS Earthquake Hazards | Seismicity within 50 km of Rainier | `earthquake.usgs.gov/fdsnws/event/1` |
| USGS NWIS Water Services | Stream gauge levels on lahar drainages | `waterservices.usgs.gov/nwis/iv` |
| IRIS / FDSN | UW network station availability | `service.iris.edu/irisws/availability` |

All APIs are public and require no authentication.

---

## Sensor Network Coverage

| Drainage | Key Stations | Coverage |
|---|---|---|
| Puyallup River (SW) | PR05, MT.WOW, AFM-PUY-01/02 | 80% |
| Carbon River (N) | CR01, AFM-CAR-01 | 65% |
| White River (NE) | WR02, CRY5 | 70% |
| Nisqually (S) | PARA, NQ01 | 55% |
| Tahoma Creek (W) | TC04 | 40% ⚠ |
| Mowich | TB01 (planned 2025) | 20% |

New stations TB01 (Tahoma Bridge) + 8 additional NPS-approved sites are scheduled for installation in late 2025, which will substantially increase coverage on the west flank — the most vulnerable to a non-eruptive landslide collapse.

---

## Getting Started

### Prerequisites

Install [pixi](https://prefix.dev/docs/pixi/overview) — the project uses it as the single environment + task runner:

**Windows (PowerShell):**
```powershell
winget install prefix-dev.pixi
```

**Or via curl:**
```powershell
iwr https://pixi.sh/install.ps1 -useb | iex
```

### Setup

```bash
git clone https://github.com/bdgroves/lahar-watch.git
cd lahar-watch
pixi install
```

That's it. No `conda activate`, no `pip install`, no `.venv`.

---

## Usage

```bash
# Fetch all sensor data → writes to data/*.json
pixi run fetch

# Fetch + print live status table in terminal
pixi run status

# Validate generated JSON files
pixi run validate

# Full pipeline (fetch → validate)
pixi run pipeline

# Open dashboard in browser
pixi run open

# Lint Python scripts
pixi run lint

# Run tests
pixi run test
```

### Example terminal output (`pixi run status`)

```
─────────── lahar-watch · Status Report ───────────

🌋  Mt. Rainier Alert Level: GREEN
    Normal background seismicity

🔴  Recent seismicity (50 km / 7 days): 4 events
    M1.2  4 km NE of Ashford, WA  depth 8.1 km
    M0.8  12 km SW of Enumclaw, WA  depth 5.4 km
    ...

💧  Stream Gauges:
    Puyallup at Orting       stage: 4.2 ft    discharge: 1,840 cfs
    Carbon at Orting         stage: 3.8 ft    discharge: 1,210 cfs
    White at Buckley         stage: 2.9 ft    discharge: 890 cfs
    Nisqually at McKenna     stage: 5.1 ft    discharge: 2,340 cfs

📡  Station Status:
    PR05     Puyallup    2340   LMS   nominal
    CR01     Carbon      1860   LMS   nominal
    ...
```

---

## Project Structure

```
lahar-watch/
├── index.html               # Dashboard (served by GitHub Pages)
├── pixi.toml                # Environment + tasks (replaces requirements.txt)
├── pixi.lock                # Locked dependencies (committed)
├── scripts/
│   ├── fetch_sensors.py     # Main data fetcher (USGS + PNSN APIs)
│   └── validate_data.py     # JSON validation for CI
├── data/                    # Auto-generated JSON (committed, updated by CI)
│   ├── summary.json
│   ├── volcano_alert.json
│   ├── seismicity.json
│   ├── stream_gauges.json
│   └── station_status.json
├── docs/
│   └── sensor-network.md    # Extended sensor network documentation
├── .github/
│   └── workflows/
│       └── deploy.yml       # Fetch data + deploy Pages (runs 2x daily)
└── README.md
```

---

## How the CI/CD Works

1. **Scheduled trigger** — GitHub Actions runs at 06:00 and 18:00 UTC daily
2. **`pixi run fetch`** — pulls fresh data from all APIs, writes to `data/*.json`
3. **`pixi run validate`** — ensures all files are well-formed JSON with required keys
4. **Commit** — updated `data/*.json` files are committed back to `main`
5. **Deploy** — the full repo is deployed to GitHub Pages

The dashboard JavaScript fetches `data/summary.json` etc. at page load and auto-refreshes every 5 minutes.

---

## Enabling GitHub Pages

In your repo settings:
1. **Settings → Pages**
2. Source: **GitHub Actions**

The `deploy.yml` workflow handles everything from there.

---

## Background: The Mt. Rainier Lahar Threat

Geologists estimate a **1-in-7 chance** of a catastrophic lahar at Mt. Rainier in the next 75 years. The Electron Mudflow (~1507 AD) buried the site of modern-day Orting without any associated eruption — triggered purely by a west-flank landslide. The city of Orting sits on that hardened mudflow today.

The current detection system, operational since 1998, was designed to provide communities with the maximum possible warning. USGS and Pierce County are actively expanding it with broadband seismometers, infrasound arrays, webcams, and GPS — all transmitting real-time data to the Washington State Emergency Operations Center and South Sound 911.

**Resources:**
- [USGS Mt. Rainier Lahar Monitoring](https://www.usgs.gov/volcanoes/mount-rainier/science/monitoring-lahars-mount-rainier)
- [Pierce County Outdoor Warning System](https://www.piercecountywa.gov/5888/Outdoor-Warning-System)
- [Pacific Northwest Seismic Network](https://pnsn.org)
- [USGS Cascades Volcano Observatory](https://www.usgs.gov/observatories/cvo)

---

## License

MIT — data is all public domain (USGS / federal government).
