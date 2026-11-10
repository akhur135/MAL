"""Acquire McDonald's locations in and around Illinois from OpenStreetMap via the ohsome API.

Owner: Elizabeth Abraham

Output: data/raw/osm/mcdonalds_il_ohsome.geojson  (raw ohsome GeoJSON response, unmodified)

Why ohsome and not Overpass: the plan named the Overpass API, but in November 2026
the public Overpass servers were overloaded (timeouts / "server too busy") and
refused connections from our environment. ohsome (HeiGIT, Heidelberg University)
serves the same OpenStreetMap data from a dated, fixed snapshot, which is also
better for reproducibility: the snapshot timestamp is stored in every feature
(@snapshotTimestamp) and pinned by SNAPSHOT below.

Query design
  * Area: a bounding box around Illinois. The box also contains restaurants in
    neighbouring states; those are removed in the spatial join (and logged), which
    is documented as a quality issue rather than hidden.
  * Filter: the McDonald's Wikidata brand id OR the McDonald's brand tag OR any
    common spelling of the name, plus "Ronald McDonald House" so the quality
    assessment can measure non-restaurant features that share the name.
  * Output: elements/bbox with tags and metadata (last edit time, version).
    Each feature's geometry is its bounding box; for a point it is degenerate
    and for a building outline its centre is used as the location.

Usage:  python -m scripts.acquire.acquire_osm [--refresh]
"""
from __future__ import annotations

import argparse
import json

import requests

from scripts.common import RAW, USER_AGENT, already_have, ensure_dirs, record_in_manifest, rel

OUT = RAW / "osm" / "mcdonalds_il_ohsome.geojson"
ENDPOINT = "https://api.ohsome.org/v1/elements/bbox"
SNAPSHOT = "2026-07-27T09:00:00Z"  # latest ohsome snapshot when the data was pulled (2026-11-10)
IL_BBOX = "-91.52,36.97,-87.49,42.51"  # lon_min, lat_min, lon_max, lat_max
NAME_VARIANTS = [
    "McDonald's", "McDonalds", "Mcdonald's", "Mcdonalds", "McDonald’s", "Mc Donald's",
    "MCDONALD'S", "MCDONALDS", "McDonald's Restaurant", "Ronald McDonald House",
]
FILTER = ('brand:wikidata=Q38076 or brand="McDonald\'s" or name in ('
          + ", ".join(f'"{n}"' for n in NAME_VARIANTS) + ")")
PARAMS = {"bboxes": IL_BBOX, "filter": FILTER, "properties": "tags,metadata", "time": SNAPSHOT}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="re-download even if a snapshot exists")
    args = ap.parse_args()
    ensure_dirs()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if already_have(OUT, args.refresh):
        return

    r = requests.get(ENDPOINT, params=PARAMS, headers={"User-Agent": USER_AGENT}, timeout=600)
    r.raise_for_status()
    payload = r.json()
    if payload.get("type") != "FeatureCollection":
        raise SystemExit(f"Unexpected ohsome response: {str(payload)[:300]}")
    payload["_request"] = {"endpoint": ENDPOINT, "params": PARAMS}  # provenance
    OUT.write_text(json.dumps(payload, indent=1, ensure_ascii=False))
    entry = record_in_manifest(
        OUT,
        source="OpenStreetMap contributors (ODbL 1.0) via ohsome API, HeiGIT",
        url=r.url,
        notes=f"OSM snapshot {SNAPSHOT}; bbox {IL_BBOX}",
    )
    print(f"Saved {len(payload['features'])} features -> {rel(OUT)} (sha256 {entry['sha256'][:12]}...)")


if __name__ == "__main__":
    main()
