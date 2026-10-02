"""
fetch_sensors.py
────────────────
Everything on lahar-watch that can't be read live by the browser, refreshed every hour.

  • Stations  — every seismic and infrasound station within ~55 km of Mount Rainier from the
                EarthScope (IRIS) FDSN station service: the USGS Cascades Volcano Observatory's
                CC network (which includes the lahar detection stations) and the University of
                Washington's UW network (Pacific Northwest Seismic Network).
  • Status    — whether each station has actually delivered data in the last 20 minutes, from
                the FDSN dataselect service (a station that exists in the catalogue but has
                gone quiet shows as such).
  • RSAM      — real-time seismic amplitude: the average ground-motion level in 10-minute
                windows, 1–10 Hz, from each station's vertical seismometer. Kept for 7 days.
                It is relative (raw counts), so each station is compared with its own normal.
  • Alert     — USGS Hazard Notification System: Mount Rainier's alert level and newest notice.
  • Quakes    — USGS ComCat (located by PNSN): the last 30 days within 20 km of the summit,
                weekly counts for two years and yearly counts since 2000, for "is this normal?".
  • Rivers    — NOAA's National Water Prediction Service gauges on the lahar rivers: the last
                7 days, the official forecast, flood categories and historic crests.
  • Waveforms — 24-hour helicorder images from the EarthScope timeseriesplot service.

Writes data/*.json (and data/helicorders/*.png). State that has to persist between runs (the
RSAM history) is kept on the `data` branch, which the workflow restores before running.

Usage:
    python scripts/fetch_sensors.py            # everything
    python scripts/fetch_sensors.py --no-heli  # skip the waveform images
"""

import argparse
import io
import json
import math
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

DATA = Path(__file__).parent.parent / "data"
DATA.mkdir(exist_ok=True)
UA = {"User-Agent": "lahar-watch/2.0 (github.com/bdgroves/lahar-watch)"}
SUMMIT = (46.853, -121.760)
FDSN = "https://service.earthscope.org"
NOW = datetime.now(timezone.utc)

# Waveform images: one station per drainage, plus the summit. Channel is picked from the catalogue.
HELI = [
    ("UW", "RCM", "Camp Muir · on the volcano, 10,100 ft"),
    ("CC", "TABR", "Tahoma Bridge · in the Tahoma Creek lahar path"),
    ("CC", "WOW", "Mount Wow · above the Nisqually"),
    ("CC", "PR05", "Puyallup River 05 · upper Puyallup"),
    ("CC", "TRON", "Electron · lower Puyallup"),
    ("CC", "CRBN", "Carbon River ranger station"),
    ("CC", "GRWR", "Greenwater · White River"),
    ("CC", "PARA", "Paradise"),
]

# NOAA NWPS river gauges on the lahar rivers, upstream to downstream
GAUGES = [
    ("ELEW1", "Puyallup"), ("ORTW1", "Puyallup"), ("PUYW1", "Puyallup"),
    ("FFXW1", "Carbon"), ("SPEW1", "Carbon"),
    ("WRRW1", "White"), ("WBCW1", "White"), ("WRAW1", "White"),
    ("NISW1", "Nisqually"), ("ALRW1", "Nisqually"),
]


def log(*a):
    print(*a, flush=True)


def get(url, params=None, timeout=40, tries=3, raw=False):
    for i in range(tries):
        try:
            r = requests.get(url, params=params, headers=UA, timeout=timeout)
            if r.status_code in (204, 404):
                return None
            r.raise_for_status()
            return r if raw else r.json()
        except requests.RequestException as e:
            if i == tries - 1:
                log(f"  ! {url.split('?')[0]}: {e}")
                return None
            time.sleep(2 * (i + 1))


def write(name, obj):
    (DATA / name).write_text(json.dumps(obj, separators=(",", ":")))
    log(f"  wrote {name}")


def iso(t):
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def km(lat1, lon1, lat2, lon2):
    p = math.pi / 180
    a = math.sin((lat2 - lat1) * p / 2) ** 2 + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lon2 - lon1) * p / 2) ** 2
    return 12742 * math.asin(math.sqrt(a))


# ── stations ─────────────────────────────────────────────────────────────────
def stations():
    """Current stations within ~55 km, with a vertical seismometer channel and infrasound if present."""
    r = get(f"{FDSN}/fdsnws/station/1/query", {"network": "CC,UW", "latitude": SUMMIT[0], "longitude": SUMMIT[1],
                                               "maxradius": 0.5, "level": "channel", "format": "text",
                                               "endafter": iso(NOW)}, raw=True, timeout=90)
    if r is None:
        raise SystemExit("station catalogue unavailable")
    st = {}
    for line in r.text.splitlines():
        if line.startswith("#") or not line.strip():
            continue
        p = [x.strip() for x in line.split("|")]
        net, sta, loc, cha, lat, lon, elev = p[0], p[1], p[2], p[3], float(p[4]), float(p[5]), float(p[6])
        s = st.setdefault(f"{net}.{sta}", {"net": net, "sta": sta, "lat": lat, "lon": lon, "elev_m": elev,
                                            "chans": set(), "start": p[15][:10]})
        s["chans"].add((loc, cha))
        s["start"] = min(s["start"], p[15][:10])
    # names and installation dates from the station level
    r2 = get(f"{FDSN}/fdsnws/station/1/query", {"network": "CC,UW", "latitude": SUMMIT[0], "longitude": SUMMIT[1],
                                                "maxradius": 0.5, "level": "station", "format": "text"}, raw=True)
    names, first = {}, {}
    for line in (r2.text.splitlines() if r2 is not None else []):
        if line.startswith("#") or not line.strip():
            continue
        p = [x.strip() for x in line.split("|")]
        k = f"{p[0]}.{p[1]}"
        names[k] = p[5]
        first[k] = min(first.get(k, "9999"), p[6][:10])
    out = []
    for k, s in st.items():
        chans = s["chans"]
        z = None
        for pref in ("HHZ", "BHZ", "EHZ", "SHZ", "HNZ", "ENZ"):
            c = sorted(l for l, ch in chans if ch == pref)
            if c:
                z = (c[0], pref)
                break
        infra = sorted({l for l, ch in chans if ch.endswith("DF")})
        if not z and not infra:
            continue
        out.append({"id": k, "net": s["net"], "sta": s["sta"], "name": names.get(k, s["sta"]),
                    "lat": s["lat"], "lon": s["lon"], "elev_ft": round(s["elev_m"] * 3.281),
                    "km_from_summit": round(km(SUMMIT[0], SUMMIT[1], s["lat"], s["lon"]), 1),
                    "since": first.get(k, s["start"]), "z": z, "infrasound": len(infra)})
    out.sort(key=lambda x: x["km_from_summit"])
    log(f"  {len(out)} stations")
    return out


def recent(st, minutes=60):
    """Last `minutes` of the vertical channel: (latest sample time, RSAM per 10 min) or (None, [])."""
    if not st["z"]:
        return None, []
    loc, cha = st["z"]
    end = NOW
    start = end - timedelta(minutes=minutes)
    r = get(f"{FDSN}/fdsnws/dataselect/1/query", {"net": st["net"], "sta": st["sta"], "loc": loc or "--", "cha": cha,
                                                  "start": iso(start)[:-1], "end": iso(end)[:-1], "nodata": 404},
            raw=True, timeout=60, tries=2)
    if r is None or not r.content:
        return None, []
    try:
        from obspy import read
        stream = read(io.BytesIO(r.content))
    except Exception as e:
        log(f"  ! {st['id']}: unreadable data ({e})")
        return None, []
    last = max(tr.stats.endtime for tr in stream).datetime.replace(tzinfo=timezone.utc)
    try:
        stream.merge(method=1, fill_value="interpolate")   # short telemetry gaps
        tr = stream[0]
        tr.data = tr.data.astype("float64")
        tr.detrend("demean")
        tr.filter("bandpass", freqmin=1.0, freqmax=10.0, corners=2, zerophase=False)
    except Exception as e:
        log(f"  ! {st['id']}: filter failed ({e})")
        return last, []
    out = []
    t0 = start.replace(second=0, microsecond=0)
    t0 = t0 - timedelta(minutes=t0.minute % 10)
    import numpy as np
    from obspy import UTCDateTime
    for k in range(minutes // 10 + 1):
        a = t0 + timedelta(minutes=10 * k)
        b = a + timedelta(minutes=10)
        if b > end:
            break
        seg = tr.slice(UTCDateTime(a), UTCDateTime(b))
        if seg.stats.npts < 0.8 * 600 * seg.stats.sampling_rate:
            continue
        out.append((int(a.timestamp()), round(float(np.mean(np.abs(seg.data))), 2)))
    return last, out


def station_status(sts):
    """Live check and RSAM for every station, keeping 7 days of RSAM history between runs."""
    path = DATA / "rsam.json"
    hist = json.loads(path.read_text()) if path.exists() else {}
    cutoff = int((NOW - timedelta(days=7)).timestamp())
    with ThreadPoolExecutor(max_workers=6) as ex:
        res = list(ex.map(recent, sts))
    for st, (last, rs) in zip(sts, res):
        age = (NOW - last).total_seconds() / 60 if last else None
        st["last_data"] = iso(last) if last else None
        st["status"] = "live" if age is not None and age <= 20 else ("late" if age is not None else "silent")
        if st["infrasound"] and not st["z"]:
            st["status"] = "infrasound only"
        h = dict(hist.get(st["id"], []))
        for t, v in rs:
            h[t] = v
        hist[st["id"]] = sorted([t, v] for t, v in h.items() if t >= cutoff)
        vals = [v for t, v in hist[st["id"]]]
        if vals:
            med = sorted(vals)[len(vals) // 2]
            cur = rs[-1][1] if rs else None
            st["rsam_now"] = cur
            st["rsam_median_7d"] = med
            st["rsam_ratio"] = round(cur / med, 2) if cur and med else None
    path.write_text(json.dumps(hist, separators=(",", ":")))
    live = sum(1 for s in sts if s["status"] == "live")
    log(f"  {live} of {len(sts)} stations sent data in the last 20 minutes")
    return sts


# ── volcano alert ────────────────────────────────────────────────────────────
def alert():
    base = "https://volcanoes.usgs.gov/hans-public/api"
    v = get(f"{base}/volcano/getVolcano/wa6") or {}
    mon = get(f"{base}/volcano/getMonitoredVolcanoes") or []
    w = next((x for x in mon if x.get("volcano_cd") == "wa6"), {})
    out = {"fetched_at": iso(NOW), "volcano": "Mount Rainier", "threat": v.get("nvews_threat"),
           "alert_level": w.get("alert_level"), "color_code": w.get("color_code"),
           "notice_sent_utc": w.get("sent_utc"), "notice_url": w.get("notice_url"), "notice_type": w.get("notice_type_cd")}
    if w.get("notice_data"):
        n = get(w["notice_data"]) or {}
        # keep the readable parts of the notice
        txt = {}
        for k in ("synopsis", "volcanic_activity_summary", "other_hazards", "remarks", "notice_type_desc", "title", "subject"):
            val = n.get(k) if isinstance(n, dict) else None
            if isinstance(val, str) and val.strip():
                txt[k] = val.strip()
        if isinstance(n, dict) and not txt:          # field names vary: keep any longer text fields
            for k, val in n.items():
                if isinstance(val, str) and len(val) > 60 and not val.startswith("http"):
                    txt[k] = val.strip()[:2000]
        out["notice"] = txt
    log(f"  alert {out['color_code']} / {out['alert_level']}")
    return out


# ── earthquakes ──────────────────────────────────────────────────────────────
def quakes():
    q = "https://earthquake.usgs.gov/fdsnws/event/1"
    near = {"latitude": SUMMIT[0], "longitude": SUMMIT[1], "maxradiuskm": 20}
    ev = get(f"{q}/query", {"format": "geojson", **near, "starttime": iso(NOW - timedelta(days=30)), "orderby": "time"}) or {}
    events = [{"t": f["properties"]["time"] // 1000, "m": f["properties"].get("mag"), "mt": f["properties"].get("magType"),
               "d": round(f["geometry"]["coordinates"][2], 1), "lat": round(f["geometry"]["coordinates"][1], 4),
               "lon": round(f["geometry"]["coordinates"][0], 4), "place": f["properties"].get("place"),
               "url": f["properties"].get("url")} for f in ev.get("features", [])]
    # weekly counts over two years (one query) and yearly counts since 2000 (cached for a day)
    two = get(f"{q}/query", {"format": "geojson", **near, "starttime": iso(NOW - timedelta(days=735)), "orderby": "time-asc"}, timeout=120) or {}
    wk = {}
    for f in two.get("features", []):
        d = datetime.fromtimestamp(f["properties"]["time"] / 1000, timezone.utc).date()
        w = (d - timedelta(days=d.weekday())).isoformat()          # the Monday of its week (UTC)
        wk[w] = wk.get(w, 0) + 1
    this_monday = NOW.date() - timedelta(days=NOW.weekday())
    weeks = [[(this_monday - timedelta(weeks=i)).isoformat(), wk.get((this_monday - timedelta(weeks=i)).isoformat(), 0)]
             for i in range(104, -1, -1)]
    path = DATA / "quakes.json"
    old = json.loads(path.read_text()) if path.exists() else {}
    years = old.get("years") if old.get("years_built") == NOW.date().isoformat() else None
    if not years:
        years = []
        for y in range(2000, NOW.year + 1):
            c = get(f"{q}/count", {**near, "starttime": f"{y}-01-01", "endtime": f"{y + 1}-01-01"}, raw=True)
            years.append([y, int(c.text) if c is not None else None])
    out = {"fetched_at": iso(NOW), "radius_km": 20, "events": events, "weeks": weeks, "years": years,
           "years_built": NOW.date().isoformat()}
    log(f"  {len(events)} earthquakes within 20 km in 30 days")
    return out


# ── rivers ───────────────────────────────────────────────────────────────────
def rivers():
    out = {"fetched_at": iso(NOW), "gauges": []}
    for lid, drainage in GAUGES:
        g = get(f"https://api.water.noaa.gov/nwps/v1/gauges/{lid}")
        if not g:
            continue
        sf = get(f"https://api.water.noaa.gov/nwps/v1/gauges/{lid}/stageflow") or {}
        def series(kind):
            d = (sf.get(kind) or {}).get("data") or []
            pts = []
            for x in d:
                t = x.get("validTime")
                if not t:
                    continue
                pts.append([t[:16], x.get("primary") if x.get("primary", -999) > -999 else None,
                            x.get("secondary") if x.get("secondary", -999) > -999 else None])
            return pts
        obs, fc = series("observed"), series("forecast")
        cutoff = (NOW - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M")
        obs = [p for p in obs if p[0] >= cutoff]
        if len(obs) > 400:                              # thin 15-minute data to hourly
            obs = [p for i, p in enumerate(obs) if i % 4 == 0 or i == len(obs) - 1]
        units = ((sf.get("observed") or {}).get("primaryUnits"), (sf.get("observed") or {}).get("secondaryUnits"))
        cats = ((g.get("flood") or {}).get("categories")) or {}
        crests = ((g.get("flood") or {}).get("crests") or {}).get("historic") or []
        out["gauges"].append({
            "lid": lid, "drainage": drainage, "name": g.get("name"), "usgs": g.get("usgsId"),
            "lat": g.get("latitude"), "lon": g.get("longitude"),
            "status": (g.get("status") or {}).get("observed"), "units": units,
            "flood": {k: {kk: (vv if vv not in (-9999, -999) else None) for kk, vv in v.items()} for k, v in cats.items()},
            "crests": [{"t": c.get("occurredTime", "")[:10], "stage": c.get("stage"), "flow": c.get("flow")} for c in crests[:5]],
            "observed": obs, "forecast": fc[:60],
        })
    log(f"  {len(out['gauges'])} river gauges")
    return out


# ── waveform images ──────────────────────────────────────────────────────────
def helicorders(sts):
    d = DATA / "helicorders"
    d.mkdir(exist_ok=True)
    by = {s["id"]: s for s in sts}
    res = {}
    for net, sta, label in HELI:
        s = by.get(f"{net}.{sta}")
        if not s or not s["z"]:
            continue
        loc, cha = s["z"]
        r = get(f"{FDSN}/irisws/timeseriesplot/1/query", {"net": net, "sta": sta, "loc": loc or "--", "cha": cha,
                                                         "start": iso(NOW - timedelta(hours=24))[:-1], "end": iso(NOW)[:-1],
                                                         "width": 1000, "height": 220}, raw=True, timeout=90, tries=2)
        if r is not None and "image" in r.headers.get("content-type", ""):
            (d / f"{sta}.png").write_bytes(r.content)
            res[f"{net}.{sta}"] = {"file": f"data/helicorders/{sta}.png", "label": label, "channel": f"{net}.{sta}.{loc or '--'}.{cha}",
                                   "start": iso(NOW - timedelta(hours=24)), "end": iso(NOW)}
        else:
            res[f"{net}.{sta}"] = {"file": None, "label": label, "channel": f"{net}.{sta}.{loc or '--'}.{cha}"}
    log(f"  {sum(1 for v in res.values() if v['file'])} waveform images")
    return {"fetched_at": iso(NOW), "stations": res}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-heli", action="store_true")
    a = ap.parse_args()
    failures = []
    log("stations")
    sts = stations()
    station_status(sts)
    write("stations.json", {"fetched_at": iso(NOW), "stations": sts})
    for name, fn in (("alert.json", alert), ("quakes.json", quakes), ("rivers.json", rivers)):
        log(name.split(".")[0])
        try:
            write(name, fn())
        except Exception as e:
            log(f"  ! {name} failed: {e}")
            failures.append(name)
    if not a.no_heli:
        log("helicorders")
        try:
            write("helicorders.json", helicorders(sts))
        except Exception as e:
            log(f"  ! helicorders failed: {e}")
    write("summary.json", {"fetched_at": iso(NOW), "stations": len(sts),
                           "live": sum(1 for s in sts if s["status"] == "live"), "failures": failures})
    if len(failures) >= 2:
        sys.exit(1)


if __name__ == "__main__":
    main()
