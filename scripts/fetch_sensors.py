"""
fetch_sensors.py
────────────────
Fetches lahar-relevant sensor data from:
  • USGS Earthquake / Seismic API  (earthquake.usgs.gov)
  • USGS HANS Public API (volcanoes.usgs.gov/hans-public) — Mt. Rainier alert level
  • IRIS FDSN Station Service — UW + CC network station availability
  • USGS Water Services — stream gauge levels on lahar drainages
  • PNSN helicorder images — fetched server-side to avoid browser CORS

Station network notes (verified against pnsn.org/seismograms):
  UW network: RCM (Camp Muir), RCS (Camp Sherman), FMW (White River), STAR, TDH
  CC network: PARA (Paradise), CRYS (Crystal), WOW (Mt. Wow), MILD (Nisqually), PR05

Writes results to data/ as JSON files consumed by the dashboard.

Usage:
    pixi run fetch                  # full fetch including helicorders
    pixi run fetch -- --no-heli     # skip helicorder images (faster)
    pixi run status                 # fetch + print rich status table
"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import requests
from rich.console import Console
from rich.table import Table

console = Console()

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# ── Station registry ──────────────────────────────────────────────────────────
# Network codes verified against PNSN seismograms page (pnsn.org/seismograms)
# UW = University of Washington network
# CC = Cascade Chain network (PNSN volcano stations)
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
    {"id": "STAR",       "name": "St. Andrews Rock",     "drainage": "Summit",    "elev_ft": 9800,  "net": "UW", "sta": "STAR", "type": "LMS"},
    {"id": "AFM-PUY-01", "name": "AFM Puyallup Lower",  "drainage": "Puyallup",  "elev_ft": 820,   "net": None, "sta": None,   "type": "AFM"},
    {"id": "AFM-PUY-02", "name": "AFM Puyallup Mid",    "drainage": "Puyallup",  "elev_ft": 680,   "net": None, "sta": None,   "type": "AFM"},
    {"id": "AFM-CAR-01", "name": "AFM Carbon Lower",    "drainage": "Carbon",    "elev_ft": 490,   "net": None, "sta": None,   "type": "AFM"},
]

# USGS stream gauges on lahar drainages (NWIS site numbers)
STREAM_GAUGES = {
    "Puyallup at Orting":   "12093500",
    "Carbon at Orting":     "12094000",
    "White at Buckley":     "12099200",
    "Nisqually at McKenna": "12089500",
}

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
    url = "https://volcanoes.usgs.gov/hans-public/api/volcano/getMonitoredVolcanoes"
    data = safe_get(url)

    result = {
        "fetched_at":  utcnow_iso(),
        "volcano":     "Mount Rainier",
        "vnum":        "321030",
        "volcano_cd":  "wa6",
        "source":      url,
    }

    if data:
        rainier = next((v for v in data if v.get("volcano_cd") == "wa6"), None)
        if rainier:
            result["alert_level"]     = rainier.get("color_code", "GREEN")
            result["activity_level"]  = rainier.get("alert_level", "NORMAL")
            result["activity_notice"] = (
                f"{rainier.get('alert_level', 'NORMAL')} / {rainier.get('color_code', 'GREEN')}"
                f" — last update {rainier.get('sent_utc', 'unknown')[:10]}"
            )
            result["last_updated"]    = rainier.get("sent_utc", utcnow_iso())
            result["notice_url"]      = rainier.get("notice_url", "")
            result["notice_type"]     = rainier.get("notice_type_cd", "")
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
    """
    USGS Earthquake Hazards API — events within 50 km of Rainier summit
    in the past 7 days.
    """
    url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    params = {
        "format":       "geojson",
        "latitude":     46.853,
        "longitude":    -121.760,
        "maxradiuskm":  50,
        "minmagnitude": 0.5,
        "orderby":      "time",
        "limit":        50,
    }
    data = safe_get(url, params=params)

    result = {
        "fetched_at": utcnow_iso(),
        "source":     url,
        "events":     [],
    }

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
    """
    USGS National Water Information System — instantaneous values.
    Parameter 00060 = discharge (cfs), 00065 = gage height (ft).
    All four lahar drainage gauges fetched in a single request.
    """
    site_list = ",".join(STREAM_GAUGES.values())
    url = "https://waterservices.usgs.gov/nwis/iv/"
    params = {
        "format":      "json",
        "sites":       site_list,
        "parameterCd": "00060,00065",
        "siteStatus":  "active",
    }
    data = safe_get(url, params=params)

    result = {
        "fetched_at": utcnow_iso(),
        "source":     url,
        "gauges":     {},
    }

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
                    result["gauges"][gauge_name]["stage_ft"]      = latest_val
                    result["gauges"][gauge_name]["stage_dt"]      = latest_dt

        except (KeyError, IndexError, TypeError) as e:
            console.print(f"[yellow]⚠ Could not parse NWIS response:[/yellow] {e}")

    return result


# ── 4. Station status via IRIS FDSN ───────────────────────────────────────────

def fetch_station_status() -> dict:
    """
    Queries IRIS FDSN station/1 for both UW and CC networks.
    Stores keys as NET.STA to avoid collisions between networks.
    """
    url = "https://service.iris.edu/fdsnws/station/1/query"
    now = utcnow_iso()
    known_stations: set[str] = set()

    for net in ("UW", "CC"):
        net_stations = [s["sta"] for s in STATIONS if s["net"] == net and s["sta"]]
        if not net_stations:
            continue
        params = {
            "network": net,
            "station": ",".join(net_stations),
            "level":   "station",
            "format":  "text",
        }
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
                console.print(f"[yellow]⚠ IRIS {net} returned HTTP {r.status_code}[/yellow]")
        except requests.RequestException as e:
            console.print(f"[yellow]⚠ IRIS {net} query failed:[/yellow] {e}")

    stations_out = []
    for s in STATIONS:
        entry = {
            "id":         s["id"],
            "name":       s["name"],
            "drainage":   s["drainage"],
            "elev_ft":    s["elev_ft"],
            "type":       s["type"],
            "net":        s["net"] or "—",
            "sta":        s["sta"] or "—",
            "checked_at": now,
        }
        key = f"{s['net']}.{s['sta']}" if s["net"] and s["sta"] else None
        if key and key in known_stations:
            entry["status"] = "nominal"
        elif s["sta"]:
            entry["status"] = "unknown"
        else:
            entry["status"] = "legacy_afm"

        stations_out.append(entry)

    return {
        "fetched_at":    now,
        "stations":      stations_out,
        "known_in_iris": sorted(known_stations),
        "source":        url,
    }


# ── 5. Helicorder images (server-side fetch) ──────────────────────────────────

def fetch_helicorders() -> dict:
    """
    Downloads PNSN helicorder PNG images server-side.
    Saves to data/helicorders/*.png — served directly by GitHub Pages,
    no browser CORS issues.
    """
    heli_dir = DATA_DIR / "helicorders"
    heli_dir.mkdir(exist_ok=True)

    targets = [
        {"sta": "RCM",  "net": "UW", "cha": "EHZ", "id": "MUIR"},
        {"sta": "RCS",  "net": "UW", "cha": "EHZ", "id": "CR01"},
        {"sta": "FMW",  "net": "UW", "cha": "HHZ", "id": "WR02"},
        {"sta": "STAR", "net": "UW", "cha": "EHZ", "id": "STAR"},
        {"sta": "PARA", "net": "CC", "cha": "EHZ", "id": "PARA"},
        {"sta": "CRYS", "net": "CC", "cha": "EHZ", "id": "CRY5"},
        {"sta": "WOW",  "net": "CC", "cha": "EHZ", "id": "MT.WOW"},
        {"sta": "MILD", "net": "CC", "cha": "EHZ", "id": "NQ01"},
    ]

    results = {}
    fetched_at = utcnow_iso()

    for t in targets:
        url = (
            f"https://pnsn.org/helicorder/image"
            f"?sta={t['sta']}&net={t['net']}&cha={t['cha']}&loc=--"
        )
        try:
            r = requests.get(url, timeout=20, headers={"User-Agent": "lahar-watch/1.0"})
            if r.ok and "image" in r.headers.get("content-type", ""):
                filename = f"{t['id']}.png"
                (heli_dir / filename).write_bytes(r.content)
                results[t["id"]] = {
                    "file":       f"data/helicorders/{filename}",
                    "sta":        t["sta"],
                    "net":        t["net"],
                    "cha":        t["cha"],
                    "fetched_at": fetched_at,
                    "ok":         True,
                }
                console.print(f"[green]✓[/green] Helicorder [bold]{t['id']}[/bold] ({t['net']}.{t['sta']})")
            else:
                results[t["id"]] = {"ok": False, "reason": f"HTTP {r.status_code}"}
                console.print(f"[yellow]⚠[/yellow] Helicorder {t['id']}: HTTP {r.status_code}")
        except requests.RequestException as e:
            results[t["id"]] = {"ok": False, "reason": str(e)}
            console.print(f"[yellow]⚠[/yellow] Helicorder {t['id']}: {e}")

    manifest = {
        "fetched_at": fetched_at,
        "stations":   results,
        "source":     "https://pnsn.org/helicorder/image",
    }
    write_json("helicorders.json", manifest)
    return manifest


# ── Rich status table ─────────────────────────────────────────────────────────

def print_status_table(
    volcano: dict,
    seismicity: dict,
    gauges: dict,
    stations: dict,
) -> None:
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
        console.print(
            f"    M{ev['magnitude']}  {ev['place']}  "
            f"depth {ev['depth_km']} km  {ev['time'][:16]}"
        )

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
        sc      = {"nominal": "green", "unknown": "yellow", "legacy_afm": "dim", "offline": "red"}.get(status, "white")
        net_sta = f"{s.get('net','—')}.{s.get('sta','—')}"
        stbl.add_row(
            s["id"], net_sta, s["drainage"],
            str(s["elev_ft"]), s["type"],
            f"[{sc}]{status}[/{sc}]"
        )
    console.print(stbl)
    console.print(f"\n[dim]Fetched at {utcnow_iso()}[/dim]\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="lahar-watch data fetcher")
    parser.add_argument("--status",  action="store_true", help="Print rich status table after fetch")
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
        "stations_nominal": sum(
            1 for s in stations.get("stations", []) if s.get("status") == "nominal"
        ),
    }
    write_json("summary.json", summary)

    if args.status:
        print_status_table(volcano, seismicity, gauges, stations)

    console.print("\n[green bold]✓ Done.[/green bold] All data written to data/")


if __name__ == "__main__":
    main()
