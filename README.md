# 🌋 lahar-watch

[![Fetch Sensor Data & Deploy](https://github.com/bdgroves/lahar-watch/actions/workflows/deploy.yml/badge.svg)](https://github.com/bdgroves/lahar-watch/actions/workflows/deploy.yml)

**[🔴 Live dashboard → brooksgroves.com/lahar-watch](https://brooksgroves.com/lahar-watch/)**

---

**Mount Rainier is rated a "Very High Threat" volcano by the USGS,** and not mainly because of eruptions. It's the lahars: fast-moving slurries of rock, mud and water that follow the river valleys. More than 90,000 people live in its lahar hazard zones, with over 50,000 people working at about 3,800 businesses ([USGS, 2022](https://www.usgs.gov/news/featured-story/usgs-offers-emergency-managers-a-new-tool-assess-lahar-hazards-mount-rainier)). Rainier has sent at least nine large lahars into the lowlands in the last 5,600 years. The most recent, the Electron Mudflow about 500 years ago, began as a landslide, with no eruption ([USGS](https://www.usgs.gov/volcanoes/mount-rainier/science/significant-lahars-mount-rainier)).

**lahar-watch** shows, live, the network that watches for them: every seismometer and infrasound sensor on and around the mountain and whether it is actually reporting, the volcano alert level and the newest notice, earthquakes against 25 years of normal, the lahar rivers against flood stage, and the official USGS hazard zones. Everything on it is real data. Nothing is simulated.

## Pages

| Page | What it shows |
|---|---|
| **[Dashboard](https://brooksgroves.com/lahar-watch/)** | Alert level and the newest Cascades Volcano Observatory notice · stations reporting in the last 20 minutes · earthquakes this week vs normal · rivers vs flood stage · map of stations, earthquakes, gauges and hazard zones · station table with each station's ground-motion level vs its own normal · weekly and yearly earthquake counts · 7-day hydrographs with NOAA's forecast and flood lines |
| **[Seismic](https://brooksgroves.com/lahar-watch/seismic.html)** | 24-hour seismograms from one station per drainage and the summit · 7 days of ground-motion level (RSAM) for any station · earthquakes by depth |
| **[Warning time](https://brooksgroves.com/lahar-watch/travel-time.html)** | The published figures: ~5 min inside the park, 15–60 min outside, 40 min – 3 h once detected; the USGS 2022 D-Claw worst-case simulations; detection to sirens; the lahars Rainier has already sent |
| **[Status](https://brooksgroves.com/lahar-watch/status.html)** | Each live source checked from your browser, with what it returned; the age of each hourly file |

## The network

About 50 stations within 55 km of the summit, from two networks, read from the [EarthScope](https://www.earthscope.org/) (IRIS) FDSN services:

- **CC** — USGS Cascades Volcano Observatory. Includes the lahar detection stations: Puyallup River 01–05, Rushingwater and Swift creeks, Voight Creek, STYX and Electron (TRON) on the Puyallup; Carbon River; Tahoma Bridge (TABR) and Mount Wow (WOW), placed in lahar paths in 2022; Kautz Creek, the Nisqually entrance, Ashford and Elbe; and, new in autumn 2025, Greenwater, Palisades, Sun Top and Lonesome Lake on the White River. Many have three-sensor infrasound arrays that hear a debris flow through the air.
- **UW** — University of Washington, Pacific Northwest Seismic Network: summit-area stations such as Camp Muir (RCM), Camp Schurman (RCS) and St. Andrews Rock (STAR), and regional stations.

Accelerometer-only sites in schools and fire stations (earthquake early warning) are left out.

"Reporting" means the station actually delivered data in the last 20 minutes, from the FDSN dataselect service. "Ground-motion level" is RSAM: the mean absolute amplitude every 10 minutes, filtered 1–10 Hz, compared with the station's own median over the past week (shown once there are 12 hours of history). It rises with wind, rivers, storms and people as well as with the volcano.

## How it works

```
GitHub Actions, hourly at :17                          Your browser
  scripts/fetch_sensors.py                               ├─ USGS volcano alert (HANS), live
    ├─ station catalogue + last hour of data             ├─ USGS earthquakes, live
    │   → stations.json, rsam.json (7 days)              ├─ NOAA river gauges (NWPS), live
    ├─ 24 h seismograms → helicorders/*.png              └─ data/*.json for everything else
    ├─ HANS alert + newest notice → alert.json
    ├─ earthquakes, weekly & yearly → quakes.json
    └─ NOAA gauges, 7 days + forecast → rivers.json
  scripts/validate_data.py
  data/ → the `data` branch (overwritten each run)
  deploy to GitHub Pages
```

The data files don't go into `main`'s history: the latest copy lives on the `data` branch, which is replaced each run (it also carries the 7-day RSAM history between runs). `data/hazard_zones.geojson` is fixed and lives on `main`; `tools/build_hazard.py` rebuilds it.

Run locally:

```powershell
pip install -r requirements.txt
python scripts/fetch_sensors.py            # writes data/
python scripts/validate_data.py
python -m http.server 8080                 # http://localhost:8080
```

## Data sources

| Source | Data |
|---|---|
| [EarthScope](https://www.earthscope.org/) (IRIS) FDSN station, dataselect, timeseriesplot | Station catalogue, last hour of data, seismogram images |
| [USGS Hazard Notification System](https://volcanoes.usgs.gov/hans-public/volcano/wa6) | Alert level, aviation colour code, notices |
| [USGS Earthquake Hazards](https://earthquake.usgs.gov/fdsnws/event/1/) | Earthquakes located by PNSN |
| [NOAA National Water Prediction Service](https://water.noaa.gov/) | River gauges, forecasts, flood categories, historic crests |
| USGS [OFR 98-428](https://pubs.usgs.gov/of/1998/0428/) (Hoblitt and others, 1998), digital data [OFR 2007-1220](https://pubs.usgs.gov/of/2007/1220/) | Lahar hazard zones |

All public, no keys.

## Background

- [USGS: Monitoring lahars at Mount Rainier](https://www.usgs.gov/volcanoes/mount-rainier/science/monitoring-lahars-mount-rainier)
- [USGS: Significant lahars at Mount Rainier](https://www.usgs.gov/volcanoes/mount-rainier/science/significant-lahars-mount-rainier)
- [George, Iverson and Cannon, 2022: Modeling the dynamics of lahars that originate as landslides on the west side of Mount Rainier](https://pubs.usgs.gov/publication/ofr20211118) (USGS OFR 2021-1118)
- [USGS: The July–August 2025 earthquake swarm](https://www.usgs.gov/observatories/cvo/news/monitoring-stations-detect-small-magnitude-earthquakes-mount-rainier-during), the largest recorded at Rainier
- [Pierce County Outdoor Warning System](https://www.piercecountywa.gov/5888/Outdoor-Warning-System)

This is an independent view of public data, not an official warning. In an emergency, follow Pierce County and local officials.

*Until October 2026 the dashboard showed a simulated waveform, hardcoded station statuses and alerts, and a travel-time calculator with invented numbers. See the [write-up](https://brooksgroves.com/blog/lahar-watch-revisited-post.html) for what changed.*

MIT licence. Built by [@bdgroves](https://github.com/bdgroves).
