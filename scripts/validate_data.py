"""
validate_data.py
────────────────
Validates all JSON files in data/ after a fetch run.
Exits non-zero if any file is missing or malformed — used in CI.

    pixi run validate
"""

import json
import sys
from pathlib import Path

from rich.console import Console

console = Console()

DATA_DIR = Path(__file__).parent.parent / "data"

REQUIRED_FILES = {
    "summary.json": ["fetched_at", "alert_level", "seismic_count"],
    "volcano_alert.json": ["fetched_at", "alert_level", "volcano"],
    "seismicity.json": ["fetched_at", "events", "count"],
    "stream_gauges.json": ["fetched_at", "gauges"],
    "station_status.json": ["fetched_at", "stations"],
}


def validate() -> bool:
    all_ok = True

    for filename, required_keys in REQUIRED_FILES.items():
        path = DATA_DIR / filename

        if not path.exists():
            console.print(f"[red]✗ MISSING[/red] {filename}")
            all_ok = False
            continue

        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError as e:
            console.print(f"[red]✗ INVALID JSON[/red] {filename}: {e}")
            all_ok = False
            continue

        missing_keys = [k for k in required_keys if k not in data]
        if missing_keys:
            console.print(f"[yellow]⚠ MISSING KEYS[/yellow] {filename}: {missing_keys}")
            all_ok = False
        else:
            console.print(f"[green]✓[/green] {filename}")

    return all_ok


if __name__ == "__main__":
    console.rule("[bold]lahar-watch · Data Validation[/bold]")
    ok = validate()
    if ok:
        console.print("\n[green bold]All data files valid.[/green bold]")
        sys.exit(0)
    else:
        console.print("\n[red bold]Validation failed — run `pixi run fetch` first.[/red bold]")
        sys.exit(1)
