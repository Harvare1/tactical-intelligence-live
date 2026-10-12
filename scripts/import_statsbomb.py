"""Import any StatsBomb events JSON file into the local match library."""
import argparse
import json
import shutil
import urllib.request
from pathlib import Path

from core.statsbomb_adapter import DATA_DIR, load_match


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", help="Local events JSON path or HTTPS URL")
    parser.add_argument("--id", required=True, help="Stable local match id")
    parser.add_argument("--competition", default="Imported match")
    parser.add_argument("--date", default="")
    parser.add_argument("--score", default="")
    args = parser.parse_args()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    destination = DATA_DIR / f"{args.id}.json"
    if args.source.startswith(("https://", "http://")):
        with urllib.request.urlopen(args.source, timeout=30) as response, destination.open("wb") as output:
            shutil.copyfileobj(response, output)
    else:
        shutil.copyfile(Path(args.source), destination)
    _, events, inferred = load_match(destination)
    catalog_path = DATA_DIR / "catalog.json"
    catalog = json.loads(catalog_path.read_text()) if catalog_path.exists() else {}
    catalog[args.id] = {"id": args.id, "competition": args.competition, "date": args.date,
                        "score": args.score or inferred["score"], "source": "StatsBomb Open Data",
                        "source_url": "https://github.com/statsbomb/open-data"}
    catalog_path.write_text(json.dumps(catalog, indent=2) + "\n")
    print(f"Imported {inferred['home']} v {inferred['away']}: {len(events)} mapped events")
    print("Restart server.py to load the new match.")


if __name__ == "__main__":
    main()
