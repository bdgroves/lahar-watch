"""
validate_data.py
────────────────
Checks the files fetch_sensors.py wrote before the site is deployed. Exits non-zero if the
station data is missing or empty, so a broken run never replaces a good site.

    python scripts/validate_data.py
"""
import json
import sys
from pathlib import Path

DATA = Path(__file__).parent.parent / "data"
REQUIRED = {
    "stations.json": ["fetched_at", "stations"],
    "summary.json": ["fetched_at", "stations", "live"],
}
OPTIONAL = {
    "alert.json": ["fetched_at", "color_code"],
    "quakes.json": ["fetched_at", "events", "weeks", "years"],
    "rivers.json": ["fetched_at", "gauges"],
    "helicorders.json": ["fetched_at", "stations"],
}


def check(name, keys, required):
    p = DATA / name
    if not p.exists():
        print(f"{'✗' if required else '·'} {name} missing")
        return not required
    try:
        j = json.loads(p.read_text())
    except json.JSONDecodeError as e:
        print(f"✗ {name} is not valid JSON: {e}")
        return False
    miss = [k for k in keys if k not in j]
    if miss:
        print(f"{'✗' if required else '·'} {name} lacks {miss}")
        return not required
    print(f"✓ {name}")
    return True


ok = all([check(n, k, True) for n, k in REQUIRED.items()] + [check(n, k, False) for n, k in OPTIONAL.items()])
st = json.loads((DATA / "stations.json").read_text()).get("stations", []) if (DATA / "stations.json").exists() else []
if len(st) < 10:
    print(f"✗ only {len(st)} stations — the catalogue query probably failed")
    ok = False
sys.exit(0 if ok else 1)
