"""Integrate restaurants, ACS, USDA and county geography into one county table.

Owner: all (integration step)

Inputs
  data/processed/osm_mcdonalds_with_county.csv
  data/processed/census_county_clean.csv
  data/processed/usda_county_clean.csv
  data/raw/tiger/il_counties_2024.geojson   (the authoritative list of 102 counties + land area)
Outputs
  data/integrated/il_county_integrated.csv
  reports/quality/integration_log.md

Join design: the 102 TIGER counties form the spine; every other source is
LEFT-joined on the 5-digit county FIPS with pandas `validate="one_to_one"`
and `indicator=True`, so any unmatched or duplicated key is caught.
A county with no restaurants gets a count of 0 (a true zero, not missing).

Usage:  python -m scripts.integrate.integrate_county
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from scripts.common import IL_EXPECTED_COUNTIES, INTEGRATED, PROCESSED, RAW, REPORTS, ensure_dirs, rel

COUNTIES = RAW / "tiger" / "il_counties_2024.geojson"
OUT = INTEGRATED / "il_county_integrated.csv"
SQM_PER_SQMI = 2_589_988.11


def county_spine() -> pd.DataFrame:
    """Read county ids, names and land area from the GeoJSON properties (no geometry needed)."""
    gj = json.loads(COUNTIES.read_text())
    rows = [{"county_fips": f["properties"]["GEOID"], "county_name": f["properties"]["NAME"],
             "land_area_sqmi": f["properties"]["ALAND"] / SQM_PER_SQMI} for f in gj["features"]]
    return pd.DataFrame(rows).sort_values("county_fips").reset_index(drop=True)


def main() -> None:
    ensure_dirs()
    spine = county_spine()
    rest = pd.read_csv(PROCESSED / "osm_mcdonalds_with_county.csv", dtype={"county_fips": str})
    acs = pd.read_csv(PROCESSED / "census_county_clean.csv", dtype={"county_fips": str})
    usda = pd.read_csv(PROCESSED / "usda_county_clean.csv", dtype={"county_fips": str})

    counts = rest.groupby("county_fips").size().rename("mcd_count").reset_index()
    log = [f"# Integration log\n", f"- County spine (TIGER): {len(spine)} counties"]

    df = spine.merge(counts, on="county_fips", how="left", validate="one_to_one", indicator="_m_osm")
    orphan_counts = set(counts["county_fips"]) - set(spine["county_fips"])
    log.append(f"- Restaurant counts: {len(counts)} counties with >=1 restaurant; "
               f"keys not in spine: {len(orphan_counts)}")
    df["mcd_count"] = df["mcd_count"].fillna(0).astype(int)

    df = df.merge(acs, on="county_fips", how="left", validate="one_to_one", indicator="_m_acs",
                  suffixes=("", "_acs"))
    df = df.merge(usda, on="county_fips", how="left", validate="one_to_one", indicator="_m_usda")
    for src, col in [("ACS", "_m_acs"), ("USDA", "_m_usda")]:
        log.append(f"- {src}: matched {int((df[col] == 'both').sum())} / {len(df)}; "
                   f"spine-only {int((df[col] == 'left_only').sum())}")
    extra_acs = set(acs["county_fips"]) - set(spine["county_fips"])
    extra_usda = set(usda["county_fips"]) - set(spine["county_fips"])
    log.append(f"- Keys in ACS not in spine: {sorted(extra_acs) or 'none'}; in USDA not in spine: {sorted(extra_usda) or 'none'}")

    # Derived measures
    pop = df["acs_population"].astype(float)
    df["mcd_per_100k"] = (df["mcd_count"] / pop * 100_000).round(3)
    df["mcd_per_1000_sqmi"] = (df["mcd_count"] / df["land_area_sqmi"] * 1000).round(3)
    df["pop_density_per_sqmi"] = (pop / df["land_area_sqmi"]).round(2)
    df["urban_rural"] = np.where(df["pct_pop_urban_tracts"] >= 50, "urban", "rural")
    df["income_quartile"] = pd.qcut(df["median_hh_income"].astype(float), 4, labels=["Q1 (lowest)", "Q2", "Q3", "Q4 (highest)"]).astype(str)
    df["pop_change_2010_to_acs_pct"] = ((pop / df["usda_pop2010"] - 1) * 100).round(2)

    df = df.drop(columns=[c for c in df.columns if c.startswith("_m_")])
    front = ["county_fips", "county_name", "mcd_count", "acs_population", "mcd_per_100k", "median_hh_income",
             "income_quartile", "pct_low_access_1_10", "pct_pop_in_lila_tracts", "urban_rural",
             "pct_pop_urban_tracts", "pop_density_per_sqmi", "land_area_sqmi", "mcd_per_1000_sqmi"]
    df = df[front + [c for c in df.columns if c not in front]]
    df.to_csv(OUT, index=False)

    log.append(f"- Output rows: {len(df)} (expected {IL_EXPECTED_COUNTIES}); "
               f"restaurants in output: {int(df['mcd_count'].sum())} of {len(rest)} assigned")
    (REPORTS / "integration_log.md").write_text("\n".join(log) + "\n")
    print("\n".join(log))
    print(f"-> {rel(OUT)}")


if __name__ == "__main__":
    main()
