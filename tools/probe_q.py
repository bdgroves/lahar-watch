import json, requests
out = {}
r = requests.get("https://earthquake.usgs.gov/fdsnws/event/1/query", params=dict(format="geojson", starttime="2006-09-25", endtime="2006-12-05", latitude=46.8529, longitude=-121.7603, maxradiuskm=30, minmagnitude=2.5, orderby="magnitude"), timeout=60)
out["top"] = [(f["properties"]["time"], f["properties"]["mag"], f["properties"]["magType"], f["properties"]["type"], f["properties"]["place"], f["geometry"]["coordinates"], f["id"]) for f in r.json()["features"][:12]]
r = requests.get("https://earthquake.usgs.gov/fdsnws/event/1/query", params=dict(format="geojson", starttime="2000-01-01", latitude=46.8529, longitude=-121.7603, maxradiuskm=30, minmagnitude=3.5, orderby="magnitude"), timeout=60)
out["m35"] = [(f["properties"]["time"], f["properties"]["mag"], f["properties"]["magType"], f["properties"]["type"], f["properties"]["place"], f["geometry"]["coordinates"], f["id"]) for f in r.json()["features"][:15]]
json.dump(out, open("tools/probe_out.json", "w"), indent=1)
