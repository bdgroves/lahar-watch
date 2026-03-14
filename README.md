# 🌋 lahar-watch

[![Fetch Sensor Data & Deploy](https://github.com/bdgroves/lahar-watch/actions/workflows/deploy.yml/badge.svg)](https://github.com/bdgroves/lahar-watch/actions/workflows/deploy.yml)
![Python](https://img.shields.io/badge/python-3.11+-3b82f6?logo=python&logoColor=white)
![pixi](https://img.shields.io/badge/env-pixi-f97316)
![GitHub Pages](https://img.shields.io/badge/pages-live-22c55e?logo=github)

---

> *"Most lahars from Mount Rainier have started with eruptions — but one of them didn't.  
> The Electron Mudflow came without warning, without fire, without any sign at all.  
> It just came."*

---

**Mount Rainier is the most dangerous volcano in the United States.** Not because it's the most active — but because of what surrounds it. More than 80,000 people live inside its lahar-hazard zones. The river valleys that drain the mountain — Puyallup, Carbon, White River, Nisqually, Tahoma Creek — are home to cities, highways, ports, and 2.5 million people in the broader corridor. When Rainier moves, it won't give much notice.

**lahar-watch** is a real-time monitoring dashboard that tracks the sensor network standing between those communities and the mountain.

🔗 **[Live Dashboard → bdgroves.github.io/lahar-watch](https://bdgroves.github.io/lahar-watch)**

---

## What Is a Lahar

A lahar is a volcanic mudflow — a fast-moving slurry of volcanic debris, rock, ash, and water that can travel over 100 mph on steep slopes and still move at 15–20 mph when it reaches the valley floor. They bury everything. Roads, bridges, neighborhoods, ports.

Rainier has buried the Puget Lowlands at least **11 times in the last 6,000 years.** The Osceola Mudflow — 5,600 years ago — sent 3.8 cubic kilometers of material all the way to Commencement Bay in Tacoma. The modern city of Enumclaw, Buckley, Bonney Lake, Sumner, and Auburn are built on top of it.

The most recent large lahar, the **Electron Mudflow (~1507 AD)**, came from a landslide on Rainier's weakened west flank. No eruption. No warning. The entire west side of the volcano is still potentially vulnerable to spontaneous collapse. The city of Orting sits directly in the Electron's path — built on top of the old mudflow deposits — with roughly **30 minutes** of warning time if a similar event happens today.

The USGS estimates a **1-in-7 chance** of a catastrophic lahar at Rainier in the next 75 years.

---

## The Sensor Network

The lahar detection system has been operating since **1998**, when Pierce County Emergency Management and the USGS Cascades Volcano Observatory installed the first Acoustic Flow Monitors (AFMs) in the Carbon and Puyallup River valleys. Since 2017, a major modernization effort has replaced aging hardware with a new generation of **Lahar Monitoring Stations (LMS)** featuring:

- **Broadband seismometers** — continuous real-time ground motion at 100+ samples/sec
- **Infrasound arrays** (3-sensor) — detect low-frequency pressure waves from debris flows, triangulate direction and speed
- **Tripwire arrays** — physical breakwire triggered by lahar front passage
- **Webcams** — visual confirmation of events
- **GPS receivers** — track ground deformation preceding volcanic unrest

Data from each station transmits to the **Washington State Emergency Operations Center** and **South Sound 911** within **10 seconds**. Automated algorithms analyze the signal and trigger alerts. When a lahar is confirmed, AHAB sirens activate across the Puyallup River Valley — over **40 sirens** strategically placed through the communities.

Most downstream communities receive **40 minutes to 3 hours** of warning. Orting gets about 30. Ashford, inside the park, gets roughly 5.

In October 2025, the National Park Service approved **9 new monitoring stations** on the southwest flank of the mountain — including two deliberately placed in the path of potential lahars. When those stations go dark, scientists calculate the lahar's speed from the time elapsed between failures.

---

## Pages

| Page | What It Shows |
|---|---|
| **[Dashboard](https://bdgroves.github.io/lahar-watch/)** | Live sensor map, station status, stream gauges, USGS alert level |
| **[Seismic](https://bdgroves.github.io/lahar-watch/seismic.html)** | Real 24h waveform images from 8 PNSN stations + seismicity table |
| **[Travel Time](https://bdgroves.github.io/lahar-watch/travel-time.html)** | Interactive lahar warning-time calculator by drainage, scenario, volume |
| **[Status](https://bdgroves.github.io/lahar-watch/status.html)** | Pipeline health, API status, data freshness, CI/CD badge |

---

## Data Sources

| Source | Data | Endpoint |
|---|---|---|
| USGS HANS API | Volcano alert level, CVO notices | `volcanoes.usgs.gov/hans-public/api` |
| USGS Earthquake Hazards | M0.5+ seismicity within 50 km | `earthquake.usgs.gov/fdsnws/event/1` |
| USGS NWIS Water Services | Live stream gauge levels | `waterservices.usgs.gov/nwis/iv` |
| IRIS FDSN Station Service | Station availability (UW + CC networks) | `service.iris.edu/fdsnws/station/1` |
| IRIS timeseriesplot | 24h waveform PNG images | `service.iris.edu/irisws/timeseriesplot/1` |

All APIs are public and require no authentication.

---

## Seismic Stations Monitored

| Station ID | IRIS Code | Location | Elevation | Drainage |
|---|---|---|---|---|
| MUIR | UW.RCM.HHZ | Camp Muir | 10,100 ft | Summit |
| CR01 | UW.RCS.EHZ | Camp Sherman | 1,860 ft | Carbon River |
| WR02 | UW.STOR.HHZ | White River | ~3,000 ft | White River |
| TC04 | UW.TDH.HHZ | Tahoma Creek | 2,900 ft | Tahoma Creek |
| PARA | CC.PARA.BHZ | Paradise | 5,400 ft | Nisqually |
| CRY5 | CC.CRYS.HHZ | Crystal Mountain | 5,800 ft | White River NE |
| NQ01 | CC.MILD.BHZ | Nisqually / Longmire | 2,100 ft | Nisqually |
| PUPY | UW.PUPY.EHZ | Puyallup Valley | 580 ft | Puyallup |

---

## Stream Gauges

| Gauge | USGS Site | Drainage | Communities at Risk |
|---|---|---|---|
| Puyallup at Orting | 12093500 | Puyallup | Orting, Puyallup, Sumner, Tacoma |
| Carbon at Orting | 12094000 | Carbon | Orting, Buckley |
| White at Buckley | 12099200 | White River | Enumclaw, Auburn, Kent |
| Nisqually at McKenna | 12089500 | Nisqually | Eatonville, Yelm, Olympia area |

---

## Getting Started

Install [pixi](https://pixi.sh) — the project's single environment and task runner:

```powershell
# Windows
winget install prefix-dev.pixi
```

```bash
# macOS / Linux
curl -fsSL https://pixi.sh/install.sh | bash
```

Clone and install:

```bash
git clone https://github.com/bdgroves/lahar-watch.git
cd lahar-watch
pixi install
```

Run the pipeline:

```bash
pixi run fetch          # fetch all data + helicorder images → data/
pixi run status         # fetch + print live status table in terminal
python scripts/fetch_sensors.py --no-heli   # fast fetch, skip images
python -m http.server 8080                  # serve dashboard at localhost:8080
```

---

## How the Pipeline Works

```
GitHub Actions (06:00 + 18:00 UTC daily)
        │
        ├── pixi run fetch
        │     ├── USGS HANS API      → data/volcano_alert.json
        │     ├── USGS Earthquake    → data/seismicity.json
        │     ├── USGS NWIS          → data/stream_gauges.json
        │     ├── IRIS FDSN          → data/station_status.json
        │     ├── IRIS timeseriesplot → data/helicorders/*.png
        │     └── summary            → data/summary.json
        │
        ├── pixi run validate
        │
        ├── git commit data/*.json data/helicorders/*.png
        │
        └── Deploy to GitHub Pages
                  │
                  └── index.html loads data/*.json on page load
                      auto-refreshes every 5 minutes
```

The dashboard is pure static HTML/JS — no server, no backend. It reads JSON files committed to the repo by the Actions pipeline and renders them client-side.

---

## Repo Structure

```
lahar-watch/
├── index.html              # Main dashboard
├── seismic.html            # Live helicorders + seismicity
├── travel-time.html        # Lahar warning-time calculator
├── status.html             # Pipeline health + API status
├── pixi.toml               # Environment + task runner
├── scripts/
│   ├── fetch_sensors.py    # Main data pipeline (5 APIs)
│   └── validate_data.py    # JSON validation for CI
├── data/
│   ├── summary.json
│   ├── volcano_alert.json
│   ├── seismicity.json
│   ├── stream_gauges.json
│   ├── station_status.json
│   ├── helicorders.json
│   └── helicorders/        # 8x PNG waveform images
│       ├── MUIR.png
│       ├── CR01.png
│       └── ...
├── docs/
│   └── sensor-network.md   # Detailed sensor network reference
└── .github/
    └── workflows/
        └── deploy.yml      # Fetch + deploy Actions workflow
```

---

## Warning Windows by Community

Based on USGS lahar inundation models for a 0.5 km³ eruption scenario:

| Community | Drainage | Distance | Warning Time | Population |
|---|---|---|---|---|
| Ashford (park) | Puyallup / Nisqually | 8 km | **~8 min** ⚠ | 1,200 |
| Orting | Puyallup / Carbon | 56 km | **~33 min** ⚡ | 8,000 |
| Buckley | Carbon / White | 72 km | **~44 min** ⚡ | 4,800 |
| Bonney Lake | Puyallup | 80 km | **~55 min** ⚡ | 21,000 |
| Enumclaw | White River | 48 km | **~38 min** ⚡ | 12,000 |
| Auburn | White River | 78 km | **~62 min** ✓ | 87,000 |
| Puyallup City | Puyallup | 98 km | **~82 min** ✓ | 43,000 |

The interactive calculator at [/travel-time.html](https://bdgroves.github.io/lahar-watch/travel-time.html) lets you adjust drainage, scenario type (eruption / west-flank collapse / rapid onset), and volume from 0.01 km³ to 4 km³ (Osceola scale).

---

## Background Reading

- [USGS: Monitoring Lahars at Mount Rainier](https://www.usgs.gov/volcanoes/mount-rainier/science/monitoring-lahars-mount-rainier)
- [Pierce County Outdoor Warning System](https://www.piercecountywa.gov/5888/Outdoor-Warning-System)
- [PNSN: Mount Rainier Volcano Page](https://pnsn.org/volcanoes/mount-rainier)
- [USGS: Lahars and Debris Flows from Mount Rainier](https://www.usgs.gov/volcanoes/mount-rainier/science/lahars-and-debris-flows-mount-rainier)
- [Seismological Society: Lahar Detection System Upgraded](https://www.seismosoc.org/news/lahar-detection-system-upgraded-for-mount-rainier/)

---

## License

MIT — all data is public domain (USGS / federal government sources).  
Built by [@bdgroves](https://github.com/bdgroves).
