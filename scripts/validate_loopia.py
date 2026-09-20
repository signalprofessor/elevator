"""Validate the static Loopia artifact before deployment."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_json(path: Path):
    return json.loads(
        path.read_text(encoding="utf-8"),
        parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"Invalid {value}")),
    )


parser = argparse.ArgumentParser()
parser.add_argument("directory", type=Path)
args = parser.parse_args()
root = args.directory.resolve()

required = [root / "index.html", root / "favicon.svg", root / "data" / "index.json"]
missing = [str(path.relative_to(root)) for path in required if not path.is_file()]
if missing:
    raise SystemExit(f"Missing deployment files: {', '.join(missing)}")

index = load_json(root / "data" / "index.json")
associations = index.get("associations", [])
if not associations:
    raise SystemExit("No associations in data/index.json")

series_count = 0
association_ids = [association.get("id") for association in associations]
if len(association_ids) != len(set(association_ids)):
    raise SystemExit("Duplicate association id in data/index.json")
for association in associations:
    series = association.get("series", [])
    if not series:
        raise SystemExit(f"No measurement series for {association.get('id')}")
    if association.get("defaultDate") not in {entry.get("date") for entry in series}:
        raise SystemExit(f"Invalid defaultDate for {association.get('id')}")
    for entry in series:
        series_count += 1
        path = root / "data" / association["id"] / f"{entry['date']}.json"
        data = load_json(path)
        elevators = data.get("elevators", [])
        ids = [elevator.get("id") for elevator in elevators]
        if not elevators or len(ids) != len(set(ids)):
            raise SystemExit(f"Invalid elevator list in {path}")
        for elevator in elevators:
            for field in ("profile", "startProfile", "stopProfile", "velocity", "spectrum", "heightEnergy", "spatialSpectrum"):
                if not elevator.get(field):
                    raise SystemExit(f"Missing {field} for {elevator.get('id')} in {path}")

for forbidden in (".openai", "wrangler.json", "server/index.js"):
    if any(forbidden in str(path.relative_to(root)) for path in root.rglob("*")):
        raise SystemExit(f"Forbidden hosted artifact found: {forbidden}")

print(f"Validated {series_count} measurement series across {len(associations)} associations for Loopia deployment")
