"""One-off: USGS Mount Rainier volcano hazard zones (Hoblitt et al. 1998, digital data USGS OFR 2007-1220,
as published on ArcGIS Online) to a small GeoJSON for the map. The parcels layer is deliberately not used.
Writes tools/probe_out.json (picked up by the probe workflow) — copy it to data/hazard_zones.geojson."""
import json, requests
SVC = "https://services.arcgis.com/aY6P1IjnU1hzETf0/arcgis/rest/services/MtRainier_lahar_hazards/FeatureServer"
LAYERS = {1: "case3", 2: "case2", 3: "case1", 4: "postlahar", 5: "pyroclastic"}
fc = {"type": "FeatureCollection", "source": "USGS Open-File Report 98-428 (Hoblitt and others, 1998); digital data USGS OFR 2007-1220", "features": []}
for lid, zone in LAYERS.items():
    g = requests.get(f"{SVC}/{lid}/query", params={"where": "1=1", "outFields": "", "returnGeometry": "true", "f": "geojson", "outSR": 4326,
                                                   "maxAllowableOffset": 0.0004, "geometryPrecision": 4}, timeout=120).json()
    for f in g.get("features", []):
        fc["features"].append({"type": "Feature", "properties": {"zone": zone}, "geometry": f["geometry"]})
    print(zone, len(g.get("features", [])), g.get("properties"))
json.dump(fc, open("tools/probe_out.json", "w"), separators=(",", ":"))
print(len(json.dumps(fc, separators=(",", ":"))), "bytes")
