"""Acquire 2020-2024 ACS 5-year county estimates for Illinois (Census Data API).

Owner: Anishka Khurana

Output: data/raw/census/acs5_2024_il_county.json  (raw API response: list of lists)

Variables
  B01003_001E / _001M  total population (estimate / margin of error)
  B19013_001E / _001M  median household income, past 12 months, 2024 dollars

A free API key is required (the API redirects keyless requests to
missing_key.html as of Nov 2026). Get one at https://api.census.gov/data/key_signup.html,
activate it from the confirmation email, and set it as an environment variable:
    export CENSUS_API_KEY=your_key      (Windows: set CENSUS_API_KEY=your_key)
The key is only sent to the API; it is never written to the repo, the raw file,
or the manifest. It is not needed to re-run the workflow from the committed data.

Usage:  python -m scripts.acquire.acquire_census_acs [--refresh]
"""
from __future__ import annotations

import argparse
import json
import os

import requests

from scripts.common import IL_STATE_FIPS, RAW, USER_AGENT, already_have, ensure_dirs, record_in_manifest, rel

YEAR = 2024
VARIABLES = ["NAME", "B01003_001E", "B01003_001M", "B19013_001E", "B19013_001M"]
BASE = f"https://api.census.gov/data/{YEAR}/acs/acs5"
OUT = RAW / "census" / f"acs5_{YEAR}_il_county.json"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    args = ap.parse_args()
    ensure_dirs()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if already_have(OUT, args.refresh):
        return

    params = {"get": ",".join(VARIABLES), "for": "county:*", "in": f"state:{IL_STATE_FIPS}"}
    key = os.environ.get("CENSUS_API_KEY")
    if key:
        params["key"] = key
    r = requests.get(BASE, params=params, headers={"User-Agent": USER_AGENT}, timeout=120)
    r.raise_for_status()
    if "key" in r.url and r.url.endswith(".html"):  # API redirects to missing_key.html / invalid_key.html
        raise SystemExit(f"Census API rejected the request ({r.url.rsplit('/', 1)[-1]}). "
                         "Set CENSUS_API_KEY to an activated key from https://api.census.gov/data/key_signup.html")
    rows = r.json()
    if not rows or rows[0][: len(VARIABLES)] != VARIABLES:
        raise SystemExit(f"Unexpected header from Census API: {rows[:1]}")

    OUT.write_text(json.dumps(rows, indent=0))
    public_url = f"{BASE}?get={params['get']}&for=county:*&in=state:{IL_STATE_FIPS}"
    entry = record_in_manifest(
        OUT,
        source=f"U.S. Census Bureau, ACS 5-year estimates {YEAR - 4}-{YEAR} (public domain)",
        url=public_url,
    )
    print(f"Saved {len(rows) - 1} county rows -> {rel(OUT)} (sha256 {entry['sha256'][:12]}...)")


if __name__ == "__main__":
    main()
