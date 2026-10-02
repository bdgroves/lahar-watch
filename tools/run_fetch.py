"""Run the pipeline in Actions and summarise what it wrote (for checking before deploy)."""
import json, subprocess, sys, pathlib
p = subprocess.run([sys.executable, "scripts/fetch_sensors.py", *sys.argv[1:]], capture_output=True, text=True)
out = {"rc": p.returncode, "stdout": p.stdout[-6000:], "stderr": p.stderr[-4000:]}
d = pathlib.Path("data")
for f in sorted(d.glob("*.json")):
    j = json.loads(f.read_text())
    out[f.name] = j if f.stat().st_size < 30000 else {"_size": f.stat().st_size, "_head": f.read_text()[:3000]}
s = json.loads((d / "stations.json").read_text())["stations"] if (d / "stations.json").exists() else []
out["station_table"] = [[x["id"], x["name"], x["km_from_summit"], x["elev_ft"], x["since"], x["z"], x["infrasound"], x["status"], x.get("last_data"), x.get("rsam_now")] for x in s]
json.dump(out, open("tools/probe_out.json", "w"), indent=1, default=str)
