"""Probe real sources for lahar-watch: stations, data latency, HANS, gauges, flood stages, hazard layers."""
import json, traceback, requests, datetime as dt
H = {"User-Agent": "lahar-watch/2.0 (github.com/bdgroves/lahar-watch)", "Origin": "https://brooksgroves.com"}
out = {}
def t(name, url, params=None, n=1500, js=False):
    try:
        r = requests.get(url, params=params, headers=H, timeout=60)
        rec = {"url": r.url[:300], "status": r.status_code, "cors": r.headers.get("Access-Control-Allow-Origin"), "type": r.headers.get("Content-Type"), "len": len(r.content)}
        rec["body"] = r.text[:n]
        out[name] = rec
        return r
    except Exception as e:
        out[name] = {"err": str(e)[:300]}
LAT, LON = 46.853, -121.760
# stations near Rainier
t("iris_sta", "https://service.iris.edu/fdsnws/station/1/query", {"latitude": LAT, "longitude": LON, "maxradius": 0.45, "level": "station", "format": "text", "endafter": dt.date.today().isoformat()}, n=8000)
t("iris_cha_cc", "https://service.iris.edu/fdsnws/station/1/query", {"network": "CC", "latitude": LAT, "longitude": LON, "maxradius": 0.45, "level": "channel", "format": "text", "endafter": dt.date.today().isoformat()}, n=12000)
t("es_sta", "https://service.earthscope.org/fdsnws/station/1/query", {"latitude": LAT, "longitude": LON, "maxradius": 0.2, "level": "station", "format": "text"}, n=600)
# latency / availability
t("iris_avail_extent", "https://service.iris.edu/fdsnws/availability/1/extent", {"network": "UW,CC", "station": "RCM,RCS,STOR,TDH,PARA,CRYS,MILD,PUPY,FMW,WOW,PR05", "format": "text", "merge": "samplerate,quality"}, n=4000)
t("es_avail_extent", "https://service.earthscope.org/fdsnws/availability/1/extent", {"network": "UW,CC", "station": "RCM,PARA", "format": "text"}, n=1500)
t("pnsn_api1", "https://pnsn.org/api/v1/stations?network=CC", n=500)
t("pnsn_latency", "https://pnsn.org/api/station_latency", n=500)
# HANS
r = t("hans_monitored", "https://volcanoes.usgs.gov/hans-public/api/volcano/getMonitoredVolcanoes", n=200)
try:
    out["hans_wa6"] = [v for v in r.json() if v.get("volcano_cd") == "wa6"]
except Exception as e:
    out["hans_wa6"] = str(e)
t("hans_newest", "https://volcanoes.usgs.gov/hans-public/api/notice/getNewestOrRecentNotices", n=1500)
t("hans_vol", "https://volcanoes.usgs.gov/hans-public/api/volcano/getVolcano/wa6", n=1500)
t("hans_notices_wa6", "https://volcanoes.usgs.gov/hans-public/api/notice/getNoticesByVolcano/wa6", n=1500)
t("hans_cap", "https://volcanoes.usgs.gov/hans-public/api/volcano/getCapElevated", n=800)
# gauges: new Water Data API latest values, and NWPS flood stages
t("wd_latest", "https://api.waterdata.usgs.gov/ogcapi/v0/collections/latest-continuous/items", {"monitoring_location_id": "USGS-12093500", "f": "json"}, n=1500)
t("wd_sites_bbox", "https://api.waterdata.usgs.gov/ogcapi/v0/collections/monitoring-locations/items", {"bbox": "-122.6,46.6,-121.4,47.35", "site_type_code": "ST", "f": "json", "limit": 200, "properties": "monitoring_location_number,monitoring_location_name"}, n=6000)
t("nwps_bbox", "https://api.water.noaa.gov/nwps/v1/gauges", {"bbox.xmin": -122.6, "bbox.ymin": 46.6, "bbox.xmax": -121.4, "bbox.ymax": 47.35, "srid": "EPSG_4326"}, n=6000)
t("nwps_ortw1", "https://api.water.noaa.gov/nwps/v1/gauges/ORTW1", n=2500)
# hazard layers
for nm, u in [("dnr_volc", "https://gis.dnr.wa.gov/site3/rest/services/Public_Geology/Volcanic_Hazards/MapServer?f=json"),
              ("dnr_geohaz", "https://gis.dnr.wa.gov/site3/rest/services/Public_Geology/Geologic_Hazards/MapServer?f=json"),
              ("dnr_list", "https://gis.dnr.wa.gov/site3/rest/services/Public_Geology?f=json"),
              ("pierce_list", "https://gisdata.piercecowa.gov/arcgis/rest/services?f=json")]:
    t(nm, u, n=3000)
# seismicity history at Rainier (within 20 km) by year
try:
    yrs = {}
    for y in range(2000, 2027):
        r = requests.get("https://earthquake.usgs.gov/fdsnws/event/1/count", params={"latitude": LAT, "longitude": LON, "maxradiuskm": 20, "starttime": f"{y}-01-01", "endtime": f"{y+1}-01-01", "minmagnitude": 0}, timeout=30)
        yrs[y] = r.text.strip()
    out["eq_per_year_20km"] = yrs
except Exception as e:
    out["eq_per_year_20km"] = str(e)
json.dump(out, open("tools/probe_out.json", "w"), indent=1)
