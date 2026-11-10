"""Pre-integration quality assessment of the USDA 2019 LRAM / Food Access Research Atlas
(Illinois tracts).

Owner: Mahitha Pamulapati

Input : data/raw/usda/lram_2019_illinois.csv
Output: reports/quality/pre_usda.md, reports/quality/pre_usda_metrics.json

Usage:  python -m scripts.quality.profile_usda
"""
from __future__ import annotations

import json

import pandas as pd

from scripts.common import IL_EXPECTED_COUNTIES, RAW, REPORTS, ensure_dirs, md_table, rel

IN = RAW / "usda" / "lram_2019_illinois.csv"

# Columns this project uses (see docs/data_dictionary.md for definitions).
SELECTED = [
    "CensusTract", "State", "County", "Urban", "Pop2010", "OHU2010",
    "LowIncomeTracts", "PovertyRate", "MedianFamilyIncome",
    "LA1and10", "LILATracts_1And10", "LATracts1", "LATracts10",
    "lapop1", "lapop10", "lalowi1", "lalowi10", "LAPOP1_10", "LALOWI1_10",
    "TractHUNV",
]
FLAGS = ["Urban", "LowIncomeTracts", "LA1and10", "LILATracts_1And10", "LATracts1", "LATracts10"]
EXPECTED_IL_TRACTS_2010 = 3123  # 2010 Census tract count for Illinois


def main() -> None:
    ensure_dirs()
    df = pd.read_csv(IN, dtype={"CensusTract": str}, low_memory=False)
    n = len(df)
    present = [c for c in SELECTED if c in df.columns]
    absent = [c for c in SELECTED if c not in df.columns]
    tract = df["CensusTract"].astype(str).str.strip()
    county_fips = tract.str.zfill(11).str[:5]

    num = df[[c for c in present if c not in ("CensusTract", "State", "County")]].apply(
        pd.to_numeric, errors="coerce")

    # Accuracy / logical checks
    checks = {}
    if {"lapop1", "Pop2010"} <= set(num):
        checks["lapop1_gt_pop2010"] = int((num["lapop1"] > num["Pop2010"] + 0.5).sum())
    if {"lalowi1", "lapop1"} <= set(num):
        checks["lalowi1_gt_lapop1"] = int((num["lalowi1"] > num["lapop1"] + 0.5).sum())
    if {"LAPOP1_10", "Pop2010"} <= set(num):
        checks["LAPOP1_10_gt_pop2010"] = int((num["LAPOP1_10"] > num["Pop2010"] + 0.5).sum())
    if "PovertyRate" in num:
        checks["poverty_rate_outside_0_100"] = int((~num["PovertyRate"].dropna().between(0, 100)).sum())
    for f in FLAGS:
        if f in num:
            checks[f"{f}_not_0_1"] = int((~num[f].dropna().isin([0, 1])).sum())
    checks["negative_values"] = int((num < 0).sum().sum())

    missing = (num.isna().mean() * 100).round(2).sort_values(ascending=False)
    zero_pop = int((num.get("Pop2010", pd.Series(dtype=float)) == 0).sum())
    # Are missing low-access counts concentrated in zero-population tracts?
    miss_lapop1_nonzero_pop = int((num["lapop1"].isna() & (num["Pop2010"] > 0)).sum()) if "lapop1" in num else None

    m = {
        "n_tracts": n,
        "expected_tracts_2010": EXPECTED_IL_TRACTS_2010,
        "n_columns_total": int(df.shape[1]),
        "selected_columns_absent": absent,
        "completeness": {
            "pct_missing_by_column": missing.to_dict(),
            "tracts_with_zero_population": zero_pop,
            "lapop1_missing_in_populated_tracts": miss_lapop1_nonzero_pop,
            "distinct_counties": int(county_fips.nunique()),
            "expected_counties": IL_EXPECTED_COUNTIES,
        },
        "accuracy": checks,
        "consistency": {
            "tract_id_lengths": tract.str.len().value_counts().to_dict(),
            "tract_ids_all_digits": bool(tract.str.fullmatch(r"\d+").all()),
            "tract_ids_start_17": bool(tract.str.zfill(11).str.startswith("17").all()),
            "duplicate_tracts": int(tract.duplicated().sum()),
            "county_name_examples": df["County"].astype(str).drop_duplicates().head(5).tolist(),
            "county_name_has_suffix": bool(df["County"].astype(str).str.contains(" County").any()),
            "fips_to_name_one_to_one": bool(
                pd.DataFrame({"f": county_fips, "n": df["County"]}).drop_duplicates().groupby("f").size().max() == 1),
        },
        "timeliness": {
            "retailer_list_year": 2019,
            "population_basis": "2010 Decennial Census (Pop2010) on 2010 tract boundaries",
            "income_basis": "ACS 2014-2018 (tract poverty rate / median family income)",
            "ers_last_updated": "2021-04-27",
        },
    }
    (REPORTS / "pre_usda_metrics.json").write_text(json.dumps(m, indent=2))

    miss_tbl = missing[missing > 0].rename("% missing").reset_index().rename(columns={"index": "column"})
    md = f"""# Pre-integration quality: USDA 2019 Large Retailer Access Map (Illinois tracts)

Source file: `{rel(IN)}` (Illinois rows of the ERS national file)
Rows: **{n}** tracts (expected {EXPECTED_IL_TRACTS_2010} for 2010 geography); columns: {df.shape[1]}
Selected columns missing from the file: {absent or 'none'}

## Completeness
- Distinct counties (first 5 digits of `CensusTract`): **{m['completeness']['distinct_counties']}** of {IL_EXPECTED_COUNTIES}
- Tracts with zero 2010 population: **{zero_pop}**
- `lapop1` missing in tracts that do have population: **{miss_lapop1_nonzero_pop}**

{md_table(miss_tbl) if len(miss_tbl) else 'No missing values in the selected columns.'}

## Accuracy (logical consistency checks)
{chr(10).join(f'- `{k}`: **{v}**' for k, v in checks.items())}

USDA counts are modelled (population is allocated to 1/2-km grid cells and distances are
measured to the nearest store in a 2019 list), so they are estimates, not observations.

## Consistency
- Tract id lengths: {m['consistency']['tract_id_lengths']} (should be 11); all digits:
  {m['consistency']['tract_ids_all_digits']}; all start with 17: {m['consistency']['tract_ids_start_17']}
- Duplicate tracts: {m['consistency']['duplicate_tracts']}
- County name format examples: {m['consistency']['county_name_examples']}
  (contains " County" suffix: {m['consistency']['county_name_has_suffix']}; TIGER uses bare names
  such as "Champaign", so names are **not** a safe join key; the FIPS code is)
- Each county FIPS maps to exactly one county name: {m['consistency']['fips_to_name_one_to_one']}

## Timeliness
- Store locations: 2019. Population: 2010 Census. Tract income: ACS 2014-2018. Last updated by ERS
  2021-04-27. This is the oldest of our three sources (about 5-7 years older than the ACS and the
  OSM snapshot) and uses 2010 tract boundaries. Illinois county boundaries and FIPS codes did not
  change between 2010 and 2024, so county-level aggregation is still valid.
"""
    (REPORTS / "pre_usda.md").write_text(md)
    print(f"Wrote {rel(REPORTS / 'pre_usda.md')}")


if __name__ == "__main__":
    main()
