"""Clean USDA 2019 LRAM tract data and aggregate it to counties.

Owner: Mahitha Pamulapati

Input : data/raw/usda/lram_2019_illinois.csv
Output: data/processed/usda_tract_clean.csv    (tract level, selected columns, cleaned)
        data/processed/usda_county_clean.csv   (county level, joined in integration)

Steps (each addresses an issue in reports/quality/pre_usda.md)
  1. Keep the selected columns; zero-pad CensusTract to 11 digits and derive the
     5-digit county FIPS from it (consistency: the FIPS is the join key; names
     are not, because naming styles differ across sources).
  2. Cast flags to integers and counts to numbers (consistency).
  3. Blank low-access counts (completeness). Blanks occur only in tracts that ERS did
     NOT flag as low access. Under the ERS flag rule (>= 500 people or >= 33% beyond
     the distance) such a tract has between 0 and min(499, 33% of Pop2010) low-access
     residents. Blanks are set to 0 (lower bound, main measure) and the upper bound is
     kept in *_upper columns for a sensitivity check. Counts are logged in
     reports/quality/clean_usda_blanks.json.
  4. Tract low-access population = lapop1 for urban tracts, lapop10 for rural
     tracts - the "1 mile urban / 10 miles rural" standard. Where ERS also supplies
     LAPOP1_10 we cross-check our value against it (accuracy).
  5. Aggregate to counties with sums of counts (never averages of percentages),
     then compute county percentages from the summed counts.

Usage:  python -m scripts.clean.clean_usda
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from scripts.common import PROCESSED, RAW, REPORTS, ensure_dirs, rel

IN = RAW / "usda" / "lram_2019_illinois.csv"
OUT_TRACT = PROCESSED / "usda_tract_clean.csv"
OUT_COUNTY = PROCESSED / "usda_county_clean.csv"

COUNT_COLS = ["Pop2010", "OHU2010", "lapop1", "lapop10", "lalowi1", "lalowi10", "LAPOP1_10", "LALOWI1_10", "TractHUNV"]
FLAG_COLS = ["Urban", "LowIncomeTracts", "LA1and10", "LILATracts_1And10"]
OTHER = ["PovertyRate", "MedianFamilyIncome"]


def main() -> None:
    ensure_dirs()
    raw = pd.read_csv(IN, dtype={"CensusTract": str}, low_memory=False)
    keep = ["CensusTract", "County"] + [c for c in COUNT_COLS + FLAG_COLS + OTHER if c in raw.columns]
    t = raw[keep].copy()

    t["tract_fips"] = t["CensusTract"].str.strip().str.replace(r"\.0$", "", regex=True).str.zfill(11)
    t["county_fips"] = t["tract_fips"].str[:5]
    t["county_name_usda"] = t["County"].astype(str).str.replace(r"\s+County$", "", regex=True).str.strip()
    num_cols = [c for c in COUNT_COLS + FLAG_COLS + OTHER if c in t.columns]
    t[num_cols] = t[num_cols].apply(pd.to_numeric, errors="coerce")
    for f in [c for c in FLAG_COLS if c in t.columns]:
        t[f] = t[f].astype("Int64")

    # Step 3: zero-population tracts
    zero = t["Pop2010"].fillna(0) == 0
    for c in ["lapop1", "lapop10", "lalowi1", "lalowi10", "LAPOP1_10", "LALOWI1_10"]:
        if c in t:
            t.loc[zero & t[c].isna(), c] = 0.0

    # Step 3b: blanks in populated tracts. Profiling showed blanks occur ONLY in tracts whose
    # low-access flag is 0 (LATracts1 for 1 mile, LATracts10 for 10 miles); ERS does not
    # document them. A tract is flagged when >= 500 people OR >= 33% of its population live
    # beyond the distance, so an unflagged tract has between 0 and min(499, 0.33 * Pop2010)
    # such people. We keep both bounds: lower bound (blank -> 0) is the main measure,
    # the upper bound is used for a sensitivity check.
    blank_log = {}
    for count_col, flag_col in [("lapop1", "LATracts1"), ("lalowi1", "LATracts1"),
                                ("lapop10", "LATracts10"), ("lalowi10", "LATracts10")]:
        if count_col not in t or flag_col not in raw:
            continue
        flag = pd.to_numeric(raw[flag_col], errors="coerce")
        blank = t[count_col].isna()
        blank_log[count_col] = {"blank_flag0": int((blank & (flag == 0)).sum()),
                                "blank_flag1": int((blank & (flag == 1)).sum())}
        ub = np.minimum(499, np.floor(0.33 * t["Pop2010"]))
        t[count_col + "_upper"] = t[count_col].where(~(blank & (flag == 0)), ub)
        t[count_col] = t[count_col].where(~(blank & (flag == 0)), 0.0)
    (REPORTS / "clean_usda_blanks.json").write_text(json.dumps(blank_log, indent=2))

    # Step 4: urban -> 1 mile, rural -> 10 miles
    urban = t["Urban"] == 1
    t["la_pop_1_10"] = np.where(urban, t["lapop1"], t["lapop10"])
    t["la_pop_1_10_upper"] = np.where(urban, t["lapop1_upper"], t["lapop10_upper"])
    t["la_lowinc_pop_1_10"] = np.where(urban, t["lalowi1"], t["lalowi10"])
    if "LAPOP1_10" in t:
        both = t["LAPOP1_10"].notna() & t["la_pop_1_10"].notna()
        diff = (t.loc[both, "LAPOP1_10"] - t.loc[both, "la_pop_1_10"]).abs()
        (REPORTS / "clean_usda_crosscheck.txt").write_text(
            f"Tracts where ERS LAPOP1_10 and our lapop1/lapop10 rule are both present: {int(both.sum())}\n"
            f"Tracts differing by more than 1 person: {int((diff > 1).sum())}\n"
            f"Max absolute difference: {float(diff.max()) if len(diff) else 0:.1f}\n")
    t["la_value_present"] = t["la_pop_1_10"].notna()

    t.drop(columns=["CensusTract", "County"]).to_csv(OUT_TRACT, index=False)

    # Step 5: aggregate to county
    t["pop_urban"] = t["Pop2010"].where(urban, 0)
    t["pop_lila"] = t["Pop2010"].where(t["LILATracts_1And10"] == 1, 0)
    t["pop_with_la_value"] = t["Pop2010"].where(t["la_value_present"], 0)
    g = t.groupby("county_fips")
    c = pd.DataFrame({
        "county_name_usda": g["county_name_usda"].first(),
        "usda_n_tracts": g.size(),
        "usda_pop2010": g["Pop2010"].sum(),
        "usda_pop_urban_tracts": g["pop_urban"].sum(),
        "usda_la_pop_1_10": g["la_pop_1_10"].sum(min_count=1),
        "usda_la_pop_1_10_upper": g["la_pop_1_10_upper"].sum(min_count=1),
        "usda_la_lowinc_pop_1_10": g["la_lowinc_pop_1_10"].sum(min_count=1),
        "usda_n_lila_tracts": g["LILATracts_1And10"].sum(),
        "usda_pop_in_lila_tracts": g["pop_lila"].sum(),
        "usda_pop_with_la_value": g["pop_with_la_value"].sum(),
    }).reset_index()
    p = c["usda_pop2010"].replace(0, np.nan)
    c["pct_pop_urban_tracts"] = (100 * c["usda_pop_urban_tracts"] / p).round(2)
    c["pct_low_access_1_10"] = (100 * c["usda_la_pop_1_10"] / c["usda_pop_with_la_value"].replace(0, np.nan)).round(2)
    c["pct_low_access_1_10_upper"] = (100 * c["usda_la_pop_1_10_upper"] / c["usda_pop_with_la_value"].replace(0, np.nan)).round(2)
    c["pct_lowinc_low_access_1_10"] = (100 * c["usda_la_lowinc_pop_1_10"] / c["usda_pop_with_la_value"].replace(0, np.nan)).round(2)
    c["pct_pop_in_lila_tracts"] = (100 * c["usda_pop_in_lila_tracts"] / p).round(2)
    c["usda_la_coverage_pct"] = (100 * c["usda_pop_with_la_value"] / p).round(2)
    c = c.sort_values("county_fips")
    assert c["county_fips"].is_unique
    c.to_csv(OUT_COUNTY, index=False)
    print(f"USDA: {len(t)} tracts -> {len(c)} counties -> {rel(OUT_COUNTY)}")


if __name__ == "__main__":
    main()
