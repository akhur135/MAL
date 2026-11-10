"""Pre-integration quality assessment of the raw ACS 5-year county data.

Owner: Anishka Khurana

Input : data/raw/census/acs5_2024_il_county.json
Output: reports/quality/pre_census.md, reports/quality/pre_census_metrics.json

Usage:  python -m scripts.quality.profile_census
"""
from __future__ import annotations

import json

import pandas as pd

from scripts.common import IL_EXPECTED_COUNTIES, RAW, REPORTS, ensure_dirs, md_table, rel

IN = RAW / "census" / "acs5_2024_il_county.json"
# Census "annotation" values that stand in for missing/unreliable estimates.
SENTINELS = {-999999999, -888888888, -666666666, -555555555, -333333333, -222222222}
VALUE_COLS = ["B01003_001E", "B01003_001M", "B19013_001E", "B19013_001M"]


def load_raw() -> pd.DataFrame:
    rows = json.loads(IN.read_text())
    return pd.DataFrame(rows[1:], columns=rows[0])


def main() -> None:
    ensure_dirs()
    df = load_raw()
    n = len(df)
    num = df[VALUE_COLS].apply(pd.to_numeric, errors="coerce")
    sentinel_counts = {c: int(num[c].isin(SENTINELS).sum()) for c in VALUE_COLS}
    clean = num.mask(num.isin(SENTINELS))

    # Coefficient of variation: ACS MOEs are 90% intervals -> SE = MOE / 1.645
    cv_inc = (clean["B19013_001M"] / 1.645) / clean["B19013_001E"] * 100
    geoid = df["state"].str.zfill(2) + df["county"].str.zfill(3)

    m = {
        "n_rows": n,
        "completeness": {
            "expected_counties": IL_EXPECTED_COUNTIES,
            "missing_counties": IL_EXPECTED_COUNTIES - geoid.nunique(),
            "null_or_nonnumeric": {c: int(num[c].isna().sum()) for c in VALUE_COLS},
            "sentinel_values": sentinel_counts,
        },
        "accuracy": {
            "income_cv_pct_median": round(float(cv_inc.median()), 2),
            "income_cv_pct_max": round(float(cv_inc.max()), 2),
            "counties_income_cv_gt_15pct": int((cv_inc > 15).sum()),
            "counties_income_cv_gt_30pct": int((cv_inc > 30).sum()),
            "population_min": int(clean["B01003_001E"].min()),
            "population_max": int(clean["B01003_001E"].max()),
            "population_total": int(clean["B01003_001E"].sum()),
            "income_min": int(clean["B19013_001E"].min()),
            "income_max": int(clean["B19013_001E"].max()),
            "negative_values": int((clean < 0).sum().sum()),
        },
        "consistency": {
            "all_state_17": bool((df["state"] == "17").all()),
            "geoid_5_digits": bool(geoid.str.fullmatch(r"\d{5}").all()),
            "duplicate_geoids": int(geoid.duplicated().sum()),
            "names_end_with_county_illinois": int(df["NAME"].str.endswith("County, Illinois").sum()),
            "value_dtype_from_api": "string (JSON text) - must be cast to numeric",
        },
        "timeliness": {
            "survey_period": "2020-2024 (5-year pooled estimate; midpoint ~2022)",
            "income_dollars": "inflation-adjusted to 2024 dollars",
        },
    }
    (REPORTS / "pre_census_metrics.json").write_text(json.dumps(m, indent=2))

    least = (pd.DataFrame({"NAME": df["NAME"], "median_hh_income": clean["B19013_001E"],
                           "MOE": clean["B19013_001M"], "CV_%": cv_inc.round(1)})
             .sort_values("CV_%", ascending=False).head(5))
    a, c = m["accuracy"], m["completeness"]
    md = f"""# Pre-integration quality: ACS 5-year (2020-2024) Illinois counties

Source file: `{rel(IN)}`  |  rows: **{n}** (expected {IL_EXPECTED_COUNTIES})

## Completeness
- Counties missing: **{c['missing_counties']}**
- Null / non-numeric values: {c['null_or_nonnumeric']}
- Census annotation (sentinel) codes such as -666666666: {c['sentinel_values']}

## Accuracy
ACS values are survey **estimates** with 90% margins of error. We use the coefficient of
variation (CV = (MOE/1.645)/estimate) as a reliability measure for median household income.

- Median CV: **{a['income_cv_pct_median']}%**, max CV: **{a['income_cv_pct_max']}%**
- Counties with CV > 15% (use with caution): **{a['counties_income_cv_gt_15pct']}**; CV > 30% (unreliable): **{a['counties_income_cv_gt_30pct']}**
- Population range {a['population_min']:,} to {a['population_max']:,}; state total {a['population_total']:,}
- Income range ${a['income_min']:,} to ${a['income_max']:,}; negative values after removing sentinels: {a['negative_values']}

Least precise income estimates:

{md_table(least)}

## Consistency
- All rows state FIPS 17: {m['consistency']['all_state_17']}; 5-digit GEOIDs: {m['consistency']['geoid_5_digits']}; duplicate GEOIDs: {m['consistency']['duplicate_geoids']}
- Names in "X County, Illinois" form: {m['consistency']['names_end_with_county_illinois']} of {n}
- The API returns every value as text, so all values must be cast to numbers.

## Timeliness
- Pooled survey period 2020-2024; incomes in 2024 dollars. This is the most recent 5-year
  release, but it describes a period roughly 2-4 years before the OSM snapshot.
"""
    (REPORTS / "pre_census.md").write_text(md)
    print(f"Wrote {rel(REPORTS / 'pre_census.md')}")


if __name__ == "__main__":
    main()
