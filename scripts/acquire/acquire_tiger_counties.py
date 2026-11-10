"""Acquire 2024 TIGER/Line county boundaries and keep Illinois only.

Supporting geography used to assign each restaurant coordinate to a county.

Outputs
  data/raw/tiger/il_counties_2024.geojson   Illinois counties (EPSG:4269, as published)
  (the ~80 MB national ZIP is downloaded to data/cache/ and git-ignored)

Usage:  python -m scripts.acquire.acquire_tiger_counties [--refresh]
"""
from __future__ import annotations

import argparse

import geopandas as gpd
import requests

from scripts.common import DATA, IL_STATE_FIPS, RAW, USER_AGENT, already_have, ensure_dirs, record_in_manifest, rel

YEAR = 2024
URL = f"https://www2.census.gov/geo/tiger/TIGER{YEAR}/COUNTY/tl_{YEAR}_us_county.zip"
CACHE = DATA / "cache" / f"tl_{YEAR}_us_county.zip"
OUT = RAW / "tiger" / f"il_counties_{YEAR}.geojson"
KEEP = ["STATEFP", "COUNTYFP", "GEOID", "NAME", "NAMELSAD", "ALAND", "AWATER", "geometry"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    args = ap.parse_args()
    ensure_dirs()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if already_have(OUT, args.refresh):
        return

    CACHE.parent.mkdir(parents=True, exist_ok=True)
    if args.refresh or not CACHE.exists():
        print(f"GET {URL}")
        with requests.get(URL, headers={"User-Agent": USER_AGENT}, stream=True, timeout=600) as r:
            r.raise_for_status()
            with open(CACHE, "wb") as f:
                for chunk in r.iter_content(1 << 20):
                    f.write(chunk)
    record_in_manifest(CACHE, source=f"U.S. Census Bureau TIGER/Line {YEAR} (public domain)", url=URL,
                       notes="National file, not committed (>50 MB); re-downloaded by this script")

    counties = gpd.read_file(CACHE)
    il = counties.loc[counties["STATEFP"] == IL_STATE_FIPS, KEEP].sort_values("GEOID")
    il.to_file(OUT, driver="GeoJSON")
    record_in_manifest(OUT, source=f"Derived: Illinois rows of TIGER/Line {YEAR} counties", url=URL)
    print(f"Saved {len(il)} Illinois counties -> {rel(OUT)}")


if __name__ == "__main__":
    main()
