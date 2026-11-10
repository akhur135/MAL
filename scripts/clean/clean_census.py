"""Clean ACS county data.

Owner: Anishka Khurana

Input : data/raw/census/acs5_2024_il_county.json
Output: data/processed/census_county_clean.csv

Steps (each addresses an issue in reports/quality/pre_census.md)
  1. Cast text values to numbers (consistency).
  2. Replace Census annotation codes (-666666666 etc.) with missing (accuracy).
  3. Build a zero-padded 5-digit county FIPS (GEOID) as the join key (consistency).
  4. Split NAME into a bare county name ("Champaign") for cross-source checks (consistency).
  5. Compute income coefficient of variation and a reliability flag (accuracy).

Usage:  python -m scripts.clean.clean_census
"""
from __future__ import annotations

import json

import pandas as pd

from scripts.common import PROCESSED, RAW, ensure_dirs, rel

IN = RAW / "census" / "acs5_2024_il_county.json"
OUT = PROCESSED / "census_county_clean.csv"
SENTINELS = [-999999999, -888888888, -666666666, -555555555, -333333333, -222222222]


def main() -> None:
    ensure_dirs()
    rows = json.loads(IN.read_text())
    df = pd.DataFrame(rows[1:], columns=rows[0])

    vals = ["B01003_001E", "B01003_001M", "B19013_001E", "B19013_001M"]
    df[vals] = df[vals].apply(pd.to_numeric, errors="coerce")
    df[vals] = df[vals].mask(df[vals].isin(SENTINELS))

    out = pd.DataFrame({
        "county_fips": df["state"].str.zfill(2) + df["county"].str.zfill(3),
        "county_name": df["NAME"].str.replace(r",\s*Illinois$", "", regex=True)
                                 .str.replace(r"\s+County$", "", regex=True).str.strip(),
        "acs_population": df["B01003_001E"].astype("Int64"),
        "acs_population_moe": df["B01003_001M"].astype("Int64"),
        "median_hh_income": df["B19013_001E"].astype("Int64"),
        "median_hh_income_moe": df["B19013_001M"].astype("Int64"),
    })
    cv = (out["median_hh_income_moe"].astype(float) / 1.645) / out["median_hh_income"].astype(float) * 100
    out["income_cv_pct"] = cv.round(2)
    out["income_reliability"] = pd.cut(cv, [-0.01, 15, 30, float("inf")], labels=["high", "medium", "low"]).astype(str)
    out = out.sort_values("county_fips")
    assert out["county_fips"].is_unique, "duplicate county FIPS in ACS data"
    out.to_csv(OUT, index=False)
    print(f"Census: {len(out)} counties -> {rel(OUT)}")


if __name__ == "__main__":
    main()
