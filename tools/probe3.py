"""Probe: filtered timeseriesplot options, and the cost of a true dayplot from 24 h of data."""
import json, base64, time, io, requests, datetime as dt
H = {"User-Agent": "lahar-watch/2.0 (github.com/bdgroves/lahar-watch)"}
out = {}
end = dt.datetime.utcnow().replace(microsecond=0); start = end - dt.timedelta(hours=24)
base = {"net": "CC", "sta": "TABR", "loc": "--", "cha": "BHZ", "start": start.isoformat(), "end": end.isoformat(), "width": 1000, "height": 220}
U = "https://service.earthscope.org/irisws/timeseriesplot/1/query"
for name, extra in [("raw", {}), ("demean", {"demean": "true"}), ("bp", {"bp": "1-10"}), ("bp_demean", {"bp": "1-10", "demean": "true"}), ("hp", {"hp": "0.5"})]:
    try:
        r = requests.get(U, params={**base, **extra}, headers=H, timeout=90)
        out[name] = {"url": r.url, "status": r.status_code, "type": r.headers.get("content-type"), "len": len(r.content),
                     "png": base64.b64encode(r.content).decode() if "image" in r.headers.get("content-type", "") else r.text[:500]}
    except Exception as e:
        out[name] = {"err": str(e)}
# channel for TABR
try:
    out["tabr_cha"] = requests.get("https://service.earthscope.org/fdsnws/station/1/query", params={"net": "CC", "sta": "TABR", "level": "channel", "format": "text", "endafter": end.date().isoformat()}, headers=H, timeout=60).text[:2000]
except Exception as e:
    out["tabr_cha"] = str(e)
# dayplot cost
try:
    from obspy import read
    t0 = time.time()
    r = requests.get("https://service.earthscope.org/fdsnws/dataselect/1/query", params={"net": "CC", "sta": "TABR", "loc": "--", "cha": "BHZ", "start": start.isoformat(), "end": end.isoformat()}, headers=H, timeout=180)
    out["ds"] = {"status": r.status_code, "bytes": len(r.content), "secs": round(time.time() - t0, 1)}
    st = read(io.BytesIO(r.content)); st.merge(fill_value="interpolate")
    st.detrend("demean"); st.filter("bandpass", freqmin=1, freqmax=10, corners=2); st.decimate(2) if st[0].stats.sampling_rate >= 40 else None
    out["ds"]["sr"] = st[0].stats.sampling_rate
    t1 = time.time(); buf = io.BytesIO()
    st.plot(type="dayplot", interval=60, one_tick_per_line=True, color=["k", "r", "b", "g"], size=(1000, 900), outfile=buf, format="png", title="CC.TABR BHZ 1-10 Hz", tick_format="%H:%M", vertical_scaling_range=None)
    out["ds"]["plot_secs"] = round(time.time() - t1, 1)
    out["dayplot"] = base64.b64encode(buf.getvalue()).decode()
except Exception as e:
    import traceback; out["ds_err"] = traceback.format_exc()[-1500:]
json.dump(out, open("tools/probe_out.json", "w"))
