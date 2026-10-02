"""Probe: lahar hazard-zone services on ArcGIS Online; NWPS gauges for the lahar rivers; dataselect latency."""
import json, requests, datetime as dt
H = {"User-Agent": "lahar-watch/2.0 (github.com/bdgroves/lahar-watch)", "Origin": "https://brooksgroves.com"}
out = {}
for iid in ["e46e3932e8b54c2b811259c5cd900e18", "323abcfd7c2c48ffab1fdea0c15b497a"]:
    try:
        it = requests.get(f"https://www.arcgis.com/sharing/rest/content/items/{iid}", params={"f": "json"}, headers=H, timeout=40).json()
        rec = {k: it.get(k) for k in ("title", "type", "url", "owner", "snippet", "description", "licenseInfo", "accessInformation", "modified", "access")}
        if rec.get("description"): rec["description"] = rec["description"][:600]
        if it.get("url"):
            s = requests.get(it["url"], params={"f": "json"}, headers=H, timeout=40).json()
            rec["service"] = {k: s.get(k) for k in ("name", "layers", "description", "copyrightText", "maxRecordCount", "geometryType", "fields")}
            lyr = (s.get("layers") or [{"id": 0}])[0]["id"]
            base = it["url"].rstrip("/") + ("" if it["url"].rstrip("/").split("/")[-1].isdigit() else f"/{lyr}")
            info = requests.get(base, params={"f": "json"}, headers=H, timeout=40).json()
            rec["layer"] = {k: info.get(k) for k in ("name", "geometryType", "fields", "maxRecordCount", "drawingInfo")}
            if rec["layer"].get("fields"): rec["layer"]["fields"] = [f["name"] for f in rec["layer"]["fields"]]
            rec["layer"]["drawingInfo"] = str(rec["layer"].get("drawingInfo"))[:800]
            q = requests.get(base + "/query", params={"where": "1=1", "outFields": "*", "returnGeometry": "false", "f": "json", "resultRecordCount": 50}, headers=H, timeout=60)
            rec["sample"] = q.text[:2500]
            g = requests.get(base + "/query", params={"where": "1=1", "outFields": "*", "f": "geojson", "outSR": 4326, "maxAllowableOffset": 0.0005, "geometryPrecision": 5}, headers=H, timeout=90)
            rec["geojson_len"] = len(g.content); rec["geojson_head"] = g.text[:400]; rec["geojson_cors"] = g.headers.get("Access-Control-Allow-Origin")
        out[iid] = rec
    except Exception as e:
        out[iid] = str(e)[:300]
# NWPS gauges in bbox with usgs ids and flood categories
try:
    j = requests.get("https://api.water.noaa.gov/nwps/v1/gauges", params={"bbox.xmin": -122.5, "bbox.ymin": 46.6, "bbox.xmax": -121.4, "bbox.ymax": 47.35, "srid": "EPSG_4326"}, headers=H, timeout=60).json()
    out["nwps"] = [[g["lid"], g["name"], g["latitude"], g["longitude"], g["status"]["observed"].get("floodCategory")] for g in j.get("gauges", [])]
except Exception as e:
    out["nwps"] = str(e)
for lid in ["ORTW1", "PUYW1", "ADRW1", "MCKW1", "NATW1", "BCKW1", "MMDW1"]:
    try:
        g = requests.get(f"https://api.water.noaa.gov/nwps/v1/gauges/{lid}", headers=H, timeout=40).json()
        out["nwps_" + lid] = {"name": g.get("name"), "usgsId": g.get("usgsId"), "flood": (g.get("flood") or {}).get("categories"), "crests": ((g.get("flood") or {}).get("crests") or {}).get("historic", [])[:3]}
    except Exception as e:
        out["nwps_" + lid] = str(e)[:150]
# dataselect latency check: last 20 minutes from a few stations
now = dt.datetime.utcnow()
for net, sta, cha in [("CC", "PR05", "*HZ"), ("CC", "TABR", "*HZ"), ("CC", "PARA", "*HZ"), ("UW", "RCM", "*HZ"), ("CC", "LONR", "*HZ"), ("CC", "GRWR", "*HZ")]:
    for host in ["service.iris.edu", "service.earthscope.org"]:
        try:
            r = requests.get(f"https://{host}/fdsnws/dataselect/1/query", params={"net": net, "sta": sta, "cha": cha, "start": (now - dt.timedelta(minutes=20)).strftime("%Y-%m-%dT%H:%M:%S"), "end": now.strftime("%Y-%m-%dT%H:%M:%S"), "nodata": 404}, headers=H, timeout=40)
            out[f"ds_{host.split('.')[1]}_{sta}"] = [r.status_code, len(r.content)]
        except Exception as e:
            out[f"ds_{host.split('.')[1]}_{sta}"] = str(e)[:120]
json.dump(out, open("tools/probe_out.json", "w"), indent=1)
