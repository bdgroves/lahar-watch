"""
fetch_sensors.py
────────────────
Fetches lahar-relevant sensor data from:
  • USGS Earthquake / Seismic API  (earthquake.usgs.gov)
  • USGS HANS Public API (volcanoes.usgs.gov/hans-public) — Mt. Rainier alert level
  • IRIS FDSN Station Service — UW + CC network station availability
  • USGS Water Services — stream gauge levels on lahar drainages
  • IRIS timeseriesplot — waveform PNG images fetched server-side (no browser CORS)

Helicorder channels verified against IRIS availability 2026-03-14:
  UW.RCM  → HHZ  (Camp Muir, 10,100 ft summit)
  UW.RCS  → EHZ  (Camp Sherman / Carbon River)
  UW.STOR → HHZ  (White River area)
  UW.TDH  → HHZ  (Tahoma Creek drainage)
  CC.PARA → BHZ  (Paradise / Nisqually, 5,400 ft)
  CC.CRYS → HHZ  (Crystal Mountain / White River NE)
  CC.MILD → BHZ  (Nisqually / Longmire)
  UW.PUPY → EHZ  (Puyallup River valley — replaces STAR which has restricted data)

Writes results to data/ as JSON files consumed by the dashboard.

Usage:
    pixi run fetch                               # full fetch including helicorders
    python scripts/fetch_sensors.py --no-heli   # skip images (faster dev loop)
    python scripts/fetch_sensors.py --status    # fetch + rich status table
"""

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from rich.console import Console
from rich.table import Table

console  = Console()
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# ── Station registry (used for IRIS status checks) ────────────────────────────
# UW = University of Washington  |  CC = Cascade Chain (PNSN volcano network)
STATIONS = [
    {"id": "PR05",       "name": "Puyallup River",      "drainage": "Puyallup",  "elev_ft": 2340,  "net": "CC", "sta": "PR05", "type": "LMS"},
    {"id": "CR01",       "name": "Carbon River",         "drainage": "Carbon",    "elev_ft": 1860,  "net": "UW", "sta": "RCS",  "type": "LMS"},
    {"id": "WR02",       "name": "White River East",     "drainage": "White",     "elev_ft": 3100,  "net": "UW", "sta": "FMW",  "type": "LMS"},
    {"id": "PARA",       "name": "Paradise / Nisqually", "drainage": "Nisqually", "elev_ft": 5400,  "net": "CC", "sta": "PARA", "type": "LMS"},
    {"id": "TC04",       "name": "Tahoma Creek",         "drainage": "Tahoma",    "elev_ft": 2900,  "net": "UW", "sta": "TDH",  "type": "LMS"},
    {"id": "CRY5",       "name": "Crystal Mountain",     "drainage": "White NE",  "elev_ft": 5800,  "net": "CC", "sta": "CRYS", "type": "LMS"},
    {"id": "MT.WOW",     "name": "Mt. Wow Westside",     "drainage": "Puyallup",  "elev_ft": 4150,  "net": "CC", "sta": "WOW",  "type": "LMS"},
    {"id": "NQ01",       "name": "Nisqually River",      "drainage": "Nisqually", "elev_ft": 2100,  "net": "CC", "sta": "MILD", "type": "LMS"},
    {"id": "MUIR",       "name": "Camp Muir Summit",     "drainage": "Summit",    "elev_ft": 10100, "net": "UW", "sta": "RCM",  "type": "LMS"},
    {"id": "PUPY",       "name": "Puyallup Valley",      "drainage": "Puyallup",  "elev_ft": 580,   "net": "UW", "sta": "PUPY", "type": "LMS"},
    {"id": "AFM-PUY-01", "name": "AFM Puyallup Lower",  "drainage": "Puyallup",  "elev_ft": 820,   "net": None, "sta": None,   "type": "AFM"},
    {"id": "AFM-PUY-02", "name": "AFM Puyallup Mid",    "drainage": "Puyallup",  "elev_ft": 680,   "net": None, "sta": None,   "type": "AFM"},
    {"id": "AFM-CAR-01", "name": "AFM Carbon Lower",    "drainage": "Carbon",    "elev_ft": 490,   "net": None, "sta": None,   "type": "AFM"},
]

# USGS stream gauges — site numbers verified 2026-03-14
STREAM_GAUGES = {
    "Puyallup at Orting":   "12093500",
    "Carbon at Orting":     "12094000",
    "White at Buckley":     "12099200",
    "Nisqually at McKenna": "12089500",
}

# Helicorder targets — all verified active in IRIS as of 2026-03-14
# PUPY replaces STAR (UW.STAR.EHZ has availability but timeseriesplot returns 404 — restricted feed)
HELI_TARGETS = [
    {"sta": "RCM",  "net": "UW", "cha": "HHZ", "loc": "--", "id": "MUIR", "label": "Camp Muir · Summit"},
    {"sta": "RCS",  "net": "UW", "cha": "EHZ", "loc": "--", "id": "CR01", "label": "Camp Sherman · Carbon"},
    {"sta": "STOR", "net": "UW", "cha": "HHZ", "loc": "--", "id": "WR02", "label": "White River"},
    {"sta": "TDH",  "net": "UW", "cha": "HHZ", "loc": "--", "id": "TC04", "label": "Tahoma Creek"},
    {"sta": "PARA", "net": "CC", "cha": "BHZ", "loc": "--", "id": "PARA", "label": "Paradise · Nisqually"},
    {"sta": "CRYS", "net": "CC", "cha": "HHZ", "loc": "--", "id": "CRY5", "label": "Crystal Mtn · White NE"},
    {"sta": "MILD", "net": "CC", "cha": "BHZ", "loc": "--", "id": "NQ01", "label": "Nisqually · Longmire"},
    {"sta": "PUPY", "net": "UW", "cha": "EHZ", "loc": "--", "id": "PUPY", "label": "Puyallup Valley"},
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def utcnow_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def safe_get(url: str, params: dict = None, timeout: int = 10) -> dict | None:
    try:
        r = requests.get(url, params=params, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        console.print(f"[yellow]⚠ Request failed:[/yellow] {url}\n  {e}")
        return None


def write_json(filename: str, data: dict) -> None:
    path = DATA_DIR / filename
    path.write_text(json.dumps(data, indent=2))
    console.print(f"[green]✓[/green] Wrote [bold]{path.name}[/bold]")


# ── 1. USGS Volcano Alert Level ───────────────────────────────────────────────

def fetch_volcano_alert() -> dict:
    """
    USGS HANS Public API — getMonitoredVolcanoes.
    Mount Rainier: volcano_cd = 'wa6', vnum = '321030'
    """
    url  = "https://volcanoes.usgs.gov/hans-public/api/volcano/getMonitoredVolcanoes"
    data = safe_get(url)

    result = {
        "fetched_at": utcnow_iso(),
        "volcano":    "Mount Rainier",
        "vnum":       "321030",
        "volcano_cd": "wa6",
        "source":     url,
    }

    if data:
        rainier = next((v for v in data if v.get("volcano_cd") == "wa6"), None)
        if rainier:
            result["alert_level"]     = rainier.get("color_code", "GREEN")
            result["activity_level"]  = rainier.get("alert_level", "NORMAL")
            result["activity_notice"] = (
                f"{rainier.get('alert_level','NORMAL')} / {rainier.get('color_code','GREEN')}"
                f" — last update {rainier.get('sent_utc','unknown')[:10]}"
            )
            result["last_updated"] = rainier.get("sent_utc", utcnow_iso())
            result["notice_url"]   = rainier.get("notice_url", "")
            result["notice_type"]  = rainier.get("notice_type_cd", "")
        else:
            result["alert_level"]     = "GREEN"
            result["activity_level"]  = "NORMAL"
            result["activity_notice"] = "Normal background activity — no notices issued"
            result["last_updated"]    = utcnow_iso()
    else:
        result["alert_level"]     = "UNKNOWN"
        result["activity_level"]  = "UNKNOWN"
        result["activity_notice"] = "Could not reach USGS HANS API"
        result["last_updated"]    = utcnow_iso()

    return result


# ── 2. Recent seismicity near Rainier ─────────────────────────────────────────

def fetch_seismicity() -> dict:
    """USGS Earthquake API — M0.5+ events within 50 km of Rainier, past 7 days."""
    url    = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    params = {
        "format": "geojson", "latitude": 46.853, "longitude": -121.760,
        "maxradiuskm": 50, "minmagnitude": 0.5, "orderby": "time", "limit": 50,
    }
    data   = safe_get(url, params=params)
    result = {"fetched_at": utcnow_iso(), "source": url, "events": []}

    if data and "features" in data:
        for feat in data["features"]:
            props  = feat["properties"]
            coords = feat["geometry"]["coordinates"]
            result["events"].append({
                "id":        feat["id"],
                "time":      datetime.fromtimestamp(props["time"] / 1000, tz=timezone.utc).isoformat(),
                "magnitude": props.get("mag"),
                "depth_km":  coords[2],
                "place":     props.get("place"),
                "status":    props.get("status"),
                "url":       props.get("url"),
            })
        result["count"] = len(result["events"])
    else:
        result["count"] = 0

    return result


# ── 3. USGS Stream Gauges (NWIS) ──────────────────────────────────────────────

def fetch_stream_gauges() -> dict:
    """USGS NWIS — instantaneous stage (ft) and discharge (cfs), all 4 drainages."""
    url    = "https://waterservices.usgs.gov/nwis/iv/"
    params = {
        "format": "json", "sites": ",".join(STREAM_GAUGES.values()),
        "parameterCd": "00060,00065", "siteStatus": "active",
    }
    data   = safe_get(url, params=params)
    result = {"fetched_at": utcnow_iso(), "source": url, "gauges": {}}
    name_by_site = {v: k for k, v in STREAM_GAUGES.items()}

    if data:
        try:
            for series in data["value"]["timeSeries"]:
                site_code  = series["sourceInfo"]["siteCode"][0]["value"]
                param_code = series["variable"]["variableCode"][0]["value"]
                values     = series["values"][0]["value"]
                latest_val = float(values[-1]["value"]) if values else None
                latest_dt  = values[-1]["dateTime"]     if values else None
                gauge_name = name_by_site.get(site_code, site_code)

                if gauge_name not in result["gauges"]:
                    result["gauges"][gauge_name] = {"site_no": site_code}

                if param_code == "00060":
                    result["gauges"][gauge_name]["discharge_cfs"] = latest_val
                    result["gauges"][gauge_name]["discharge_dt"]  = latest_dt
                elif param_code == "00065":
                    result["gauges"][gauge_name]["stage_ft"]  = latest_val
                    result["gauges"][gauge_name]["stage_dt"]  = latest_dt
        except (KeyError, IndexError, TypeError) as e:
            console.print(f"[yellow]⚠ NWIS parse error:[/yellow] {e}")

    return result


# ── 4. Station status via IRIS FDSN ───────────────────────────────────────────

def fetch_station_status() -> dict:
    """IRIS FDSN station/1 — queries UW and CC networks, keys as NET.STA."""
    url              = "https://service.iris.edu/fdsnws/station/1/query"
    now              = utcnow_iso()
    known_stations: set[str] = set()

    for net in ("UW", "CC"):
        net_stations = [s["sta"] for s in STATIONS if s["net"] == net and s["sta"]]
        if not net_stations:
            continue
        params = {"network": net, "station": ",".join(net_stations), "level": "station", "format": "text"}
        try:
            r = requests.get(url, params=params, timeout=15)
            if r.ok:
                for line in r.text.splitlines():
                    if line.startswith("#") or not line.strip():
                        continue
                    parts = line.split("|")
                    if len(parts) >= 2:
                        known_stations.add(f"{parts[0].strip()}.{parts[1].strip()}")
            else:
                console.print(f"[yellow]⚠ IRIS {net} HTTP {r.status_code}[/yellow]")
        except requests.RequestException as e:
            console.print(f"[yellow]⚠ IRIS {net} failed:[/yellow] {e}")

    stations_out = []
    for s in STATIONS:
        key    = f"{s['net']}.{s['sta']}" if s["net"] and s["sta"] else None
        status = ("nominal"    if key and key in known_stations else
                  "legacy_afm" if not s["sta"] else "unknown")
        stations_out.append({
            "id":         s["id"],
            "name":       s["name"],
            "drainage":   s["drainage"],
            "elev_ft":    s["elev_ft"],
            "type":       s["type"],
            "net":        s["net"] or "—",
            "sta":        s["sta"] or "—",
            "checked_at": now,
            "status":     status,
        })

    return {
        "fetched_at":    now,
        "stations":      stations_out,
        "known_in_iris": sorted(known_stations),
        "source":        url,
    }


# ── 5. Helicorder images via IRIS timeseriesplot ──────────────────────────────

def fetch_helicorders() -> dict:
    """
    Downloads 24h waveform PNG images from IRIS timeseriesplot service.
    Uses a rolling window ending now — more reliable than currentutcday.
    Falls back to the previous 24h window if today's data isn't ready yet.

    API: https://service.iris.edu/irisws/timeseriesplot/1/
    All targets in HELI_TARGETS are verified active in IRIS as of 2026-03-14.
    """
    heli_dir   = DATA_DIR / "helicorders"
    heli_dir.mkdir(exist_ok=True)

    base_url   = "https://service.iris.edu/irisws/timeseriesplot/1/query"
    now        = datetime.now(timezone.utc)
    fetched_at = utcnow_iso()
    fmt        = "%Y-%m-%dT%H:%M:%S"
    results    = {}

    windows = [
        (now - timedelta(hours=24), now),
        (now - timedelta(hours=48), now - timedelta(hours=24)),
    ]

    for t in HELI_TARGETS:
        success = False
        for start_dt, end_dt in windows:
            params = {
                "net":    t["net"],
                "sta":    t["sta"],
                "loc":    t["loc"],
                "cha":    t["cha"],
                "start":  start_dt.strftime(fmt),
                "end":    end_dt.strftime(fmt),
                "width":  "900",
                "height": "200",
            }
            try:
                r = requests.get(base_url, params=params, timeout=30,
                                 headers={"User-Agent": "lahar-watch/1.0"})
                if r.ok and "image" in r.headers.get("content-type", ""):
                    filename = f"{t['id']}.png"
                    (heli_dir / filename).write_bytes(r.content)
                    window_label = "24h" if start_dt == windows[0][0] else "prev 24h"
                    results[t["id"]] = {
                        "file":          f"data/helicorders/{filename}",
                        "label":         t.get("label", t["id"]),
                        "sta":           t["sta"],
                        "net":           t["net"],
                        "cha":           t["cha"],
                        "loc":           t["loc"],
                        "window_start":  start_dt.strftime(fmt),
                        "window_end":    end_dt.strftime(fmt),
                        "fetched_at":    fetched_at,
                        "ok":            True,
                    }
                    console.print(
                        f"[green]✓[/green] Helicorder [bold]{t['id']}[/bold] "
                        f"({t['net']}.{t['sta']}.{t['loc']}.{t['cha']}) [{window_label}]"
                    )
                    success = True
                    break
            except requests.RequestException as e:
                console.print(f"[yellow]⚠[/yellow] Helicorder {t['id']}: {e}")
                break

        if not success and t["id"] not in results:
            results[t["id"]] = {
                "ok":     False,
                "label":  t.get("label", t["id"]),
                "reason": f"no data in IRIS past 48h ({t['net']}.{t['sta']}.{t['loc']}.{t['cha']})",
            }
            console.print(
                f"[yellow]⚠[/yellow] Helicorder {t['id']}: "
                f"no data ({t['net']}.{t['sta']}.{t['loc']}.{t['cha']})"
            )

    manifest = {"fetched_at": fetched_at, "stations": results, "source": base_url}
    write_json("helicorders.json", manifest)
    return manifest


# ── Rich status table ─────────────────────────────────────────────────────────

def print_status_table(volcano: dict, seismicity: dict, gauges: dict, stations: dict) -> None:
    console.rule("[bold orange1]lahar-watch · Status Report[/bold orange1]")

    alert = volcano.get("alert_level", "UNKNOWN")
    color = {"GREEN": "green", "YELLOW": "yellow", "ORANGE": "orange1", "RED": "red"}.get(alert, "white")
    console.print(f"\n🌋  Mt. Rainier Alert Level: [{color} bold]{alert}[/{color} bold]")
    console.print(f"    {volcano.get('activity_notice', '')}")
    if volcano.get("notice_url"):
        console.print(f"    [dim]{volcano['notice_url']}[/dim]")
    console.print()

    count = seismicity.get("count", 0)
    console.print(f"🔴  Recent seismicity (50 km / 7 days): [bold]{count} events[/bold]")
    for ev in seismicity.get("events", [])[:5]:
        console.print(f"    M{ev['magnitude']}  {ev['place']}  depth {ev['depth_km']} km  {ev['time'][:16]}")

    console.print("\n💧  Stream Gauges:")
    tbl = Table(show_header=True, header_style="bold cyan", box=None)
    tbl.add_column("Gauge",           style="white", min_width=28)
    tbl.add_column("Stage (ft)",      justify="right")
    tbl.add_column("Discharge (cfs)", justify="right")
    for name, g in gauges.get("gauges", {}).items():
        tbl.add_row(name, str(g.get("stage_ft", "—")), str(g.get("discharge_cfs", "—")))
    console.print(tbl)

    console.print("\n📡  Station Status:")
    stbl = Table(show_header=True, header_style="bold cyan", box=None)
    stbl.add_column("ID",       min_width=10)
    stbl.add_column("Net.Sta",  min_width=10)
    stbl.add_column("Drainage", min_width=12)
    stbl.add_column("Elev ft",  justify="right")
    stbl.add_column("Type",     min_width=5)
    stbl.add_column("Status")
    for s in stations.get("stations", []):
        status  = s.get("status", "unknown")
        sc      = {"nominal":"green","unknown":"yellow","legacy_afm":"dim","offline":"red"}.get(status,"white")
        net_sta = f"{s.get('net','—')}.{s.get('sta','—')}"
        stbl.add_row(s["id"], net_sta, s["drainage"], str(s["elev_ft"]), s["type"], f"[{sc}]{status}[/{sc}]")
    console.print(stbl)
    console.print(f"\n[dim]Fetched at {utcnow_iso()}[/dim]\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="lahar-watch data fetcher")
    parser.add_argument("--status",  action="store_true", help="Print rich status table")
    parser.add_argument("--no-heli", action="store_true", help="Skip helicorder image fetch")
    parser.add_argument("--debug",   action="store_true", help="Verbose output")
    args = parser.parse_args()

    console.print("[bold orange1]lahar-watch[/bold orange1] · fetching data...\n")

    volcano    = fetch_volcano_alert()
    seismicity = fetch_seismicity()
    gauges     = fetch_stream_gauges()
    stations   = fetch_station_status()

    write_json("volcano_alert.json",  volcano)
    write_json("seismicity.json",     seismicity)
    write_json("stream_gauges.json",  gauges)
    write_json("station_status.json", stations)

    if not args.no_heli:
        console.print("\n[bold]Fetching helicorder images...[/bold]")
        fetch_helicorders()

    summary = {
        "fetched_at":       utcnow_iso(),
        "alert_level":      volcano.get("alert_level", "UNKNOWN"),
        "activity_level":   volcano.get("activity_level", "UNKNOWN"),
        "seismic_count":    seismicity.get("count", 0),
        "stations_total":   len(stations.get("stations", [])),
        "stations_nominal": sum(1 for s in stations.get("stations", []) if s.get("status") == "nominal"),
    }
    write_json("summary.json", summary)

    if args.status:
        print_status_table(volcano, seismicity, gauges, stations)

    console.print("\n[green bold]✓ Done.[/green bold] All data written to data/")


if __name__ == "__main__":
    main()
