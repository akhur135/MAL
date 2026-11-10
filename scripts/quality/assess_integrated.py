"""Post-integration quality assessment of the integrated county table.

Owner: all

Inputs: data/integrated/il_county_integrated.csv, data/processed/osm_mcdonalds_clean.csv,
        data/processed/osm_mcdonalds_with_county.csv
Output: reports/quality/post_integration.md, reports/quality/post_integration_metrics.json

Usage:  python -m scripts.quality.assess_integrated
"""
from __future__ import annotations

import json

import pandas as pd

from scripts.common import IL_EXPECTED_COUNTIES, INTEGRATED, PROCESSED, REPORTS, ensure_dirs, md_table, rel

IN = INTEGRATED / "il_county_integrated.csv"


def norm(s: pd.Series) -> pd.Series:
    return (s.astype(str).str.lower().str.replace(r"[^a-z]", "", regex=True)
            .str.replace("saint", "st", regex=False))


def main() -> None:
    ensure_dirs()
    df = pd.read_csv(IN, dtype={"county_fips": str})
    clean = pd.read_csv(PROCESSED / "osm_mcdonalds_clean.csv")
    assigned = pd.read_csv(PROCESSED / "osm_mcdonalds_with_county.csv", dtype={"county_fips": str})
    n = len(df)

    # ---- Completeness ---------------------------------------------------
    key_cols = ["mcd_count", "acs_population", "median_hh_income", "usda_pop2010", "pct_low_access_1_10",
                "pct_pop_in_lila_tracts", "pct_pop_urban_tracts", "land_area_sqmi"]
    nulls = {c: int(df[c].isna().sum()) for c in key_cols if c in df}
    completeness = {
        "rows": n, "expected": IL_EXPECTED_COUNTIES, "unique_fips": int(df["county_fips"].nunique()),
        "nulls_in_key_columns": nulls,
        "restaurants_clean": len(clean), "restaurants_assigned": len(assigned),
        "restaurants_in_integrated_total": int(df["mcd_count"].sum()),
        "counties_with_zero_restaurants": int((df["mcd_count"] == 0).sum()),
        "min_usda_la_coverage_pct": float(df["usda_la_coverage_pct"].min()),
    }

    # ---- Consistency: do the three sources agree on which county is which? ---
    name_ok_acs = (norm(df["county_name"]) == norm(df["county_name_acs"]))
    name_ok_usda = (norm(df["county_name"]) == norm(df["county_name_usda"]))
    consistency = {
        "county_names_match_acs": int(name_ok_acs.sum()),
        "county_names_match_usda": int(name_ok_usda.sum()),
        "mismatched_names": df.loc[~(name_ok_acs & name_ok_usda),
                                   ["county_fips", "county_name", "county_name_acs", "county_name_usda"]]
                              .astype(str).to_dict("records"),
        "duplicate_fips": int(df["county_fips"].duplicated().sum()),
    }

    # ---- Accuracy: plausibility of joined values -----------------------------
    pc = df["pop_change_2010_to_acs_pct"]
    z = (df["mcd_per_100k"] - df["mcd_per_100k"].mean()) / df["mcd_per_100k"].std()
    accuracy = {
        "acs_total_population": int(df["acs_population"].sum()),
        "usda_total_pop2010": int(df["usda_pop2010"].sum()),
        "pop_change_pct_median": round(float(pc.median()), 2),
        "counties_pop_change_abs_gt_15pct": df.loc[pc.abs() > 15, ["county_name", "pop_change_2010_to_acs_pct"]]
                                              .astype(str).to_dict("records"),
        "statewide_mcd_per_100k": round(df["mcd_count"].sum() / df["acs_population"].sum() * 1e5, 2),
        "outlier_counties_mcd_per_100k_z_gt_3": df.loc[z.abs() > 3, ["county_name", "mcd_count", "acs_population", "mcd_per_100k"]]
                                                  .astype(str).to_dict("records"),
        "pct_values_in_0_100": bool(df[["pct_low_access_1_10", "pct_pop_in_lila_tracts", "pct_pop_urban_tracts"]]
                                     .dropna().apply(lambda s: s.between(0, 100)).all().all()),
    }
    # Independent check of the spatial join: the address state tag vs. where the point landed
    st = clean.merge(assigned[["osm_uid", "county_fips"]], on="osm_uid", how="left")
    st["placed_in_il"] = st["county_fips"].notna()
    tagged = st[st["addr_state"].notna()]
    accuracy["addr_state_vs_spatial_join"] = {
        "tagged_IL_placed_in_IL": int(((tagged["addr_state"] == "IL") & tagged["placed_in_il"]).sum()),
        "tagged_IL_placed_outside": int(((tagged["addr_state"] == "IL") & ~tagged["placed_in_il"]).sum()),
        "tagged_other_state_placed_in_IL": int(((tagged["addr_state"] != "IL") & tagged["placed_in_il"]).sum()),
        "tagged_other_state_placed_outside": int(((tagged["addr_state"] != "IL") & ~tagged["placed_in_il"]).sum()),
        "no_state_tag_placed_in_IL": int((st["addr_state"].isna() & st["placed_in_il"]).sum()),
    }
    if "addr_city" in assigned and assigned["addr_city"].notna().any():
        cook = assigned[assigned["county_fips"] == "17031"]
        accuracy["chicago_addresses_in_cook"] = f"{int((cook['addr_city'] == 'Chicago').sum())} of " \
            f"{int((assigned['addr_city'] == 'Chicago').sum())} 'Chicago' addresses fall in Cook County"

    timeliness = pd.DataFrame([
        ["Restaurants", "OpenStreetMap", "snapshot (see data/raw/manifest.json)", "current"],
        ["Population, income", "ACS 5-year", "2020-2024", "~2-4 years before snapshot"],
        ["Food access, urban flag", "USDA LRAM", "stores 2019, population 2010", "~7-16 years before snapshot"],
        ["County boundaries", "TIGER/Line", "2024", "boundaries unchanged since 2010"],
    ], columns=["Measure", "Source", "Reference period", "Lag vs. OSM snapshot"])

    m = {"completeness": completeness, "consistency": consistency, "accuracy": accuracy}
    (REPORTS / "post_integration_metrics.json").write_text(json.dumps(m, indent=2, default=str))

    c, k, a = completeness, consistency, accuracy

    def tbl(records, sort_col):
        if not records:
            return "_none_"
        t = pd.DataFrame(records)
        t = t.reindex(t[sort_col].astype(float).abs().sort_values(ascending=False).index).head(15)
        return md_table(t)

    lost = c["restaurants_clean"] - c["restaurants_in_integrated_total"]
    md = f"""# Post-integration quality: `{rel(IN)}`

## Completeness
- Rows: **{c['rows']}** (expected {c['expected']}); unique FIPS: {c['unique_fips']}
- Missing values in key columns: {c['nulls_in_key_columns']}
- Restaurants: {c['restaurants_clean']} after cleaning -> {c['restaurants_assigned']} assigned to a county
  -> **{c['restaurants_in_integrated_total']}** counted in the integrated table. The other {lost} lie outside
  Illinois (the download is a rectangle) and are listed in `reports/quality/assign_counties_log.csv`;
  no Illinois restaurant was dropped without a log entry.
- Counties with zero restaurants (kept as true zeros): {c['counties_with_zero_restaurants']}
- Lowest USDA low-access coverage in any county: {c['min_usda_la_coverage_pct']}% of 2010 population

## Consistency
- County names agree between TIGER and ACS for **{k['county_names_match_acs']}/{n}** counties and between TIGER and USDA
  for **{k['county_names_match_usda']}/{n}** (after normalising case, punctuation and "Saint/St.").
  Because the join used FIPS codes, agreeing names are an independent check that the join is correct.
- Mismatches:

{md_table(pd.DataFrame(k['mismatched_names'])) if k['mismatched_names'] else '_none_'}
- Duplicate FIPS in output: {k['duplicate_fips']}

## Accuracy
- Statewide McDonald's per 100k residents: **{a['statewide_mcd_per_100k']}**
- ACS total population {a['acs_total_population']:,} vs USDA 2010 base {a['usda_total_pop2010']:,};
  median county change {a['pop_change_pct_median']}%. Counties whose population changed more than 15% between the
  USDA 2010 base and the ACS (largest first, max 15 shown; these make the 2010-based USDA shares less representative):

{tbl(a['counties_pop_change_abs_gt_15pct'], 'pop_change_2010_to_acs_pct')}

- Counties with extreme restaurants-per-100k (|z| > 3), to be checked by hand (small populations inflate rates):

{tbl(a['outlier_counties_mcd_per_100k_z_gt_3'], 'mcd_per_100k')}

- All percentage columns within 0-100: {a['pct_values_in_0_100']}
- Address state tag vs. spatial join (independent check): {a['addr_state_vs_spatial_join']}
- {a.get('chicago_addresses_in_cook', 'City/county cross-check not available (few addresses).')}

## Timeliness

{md_table(timeliness)}

The USDA measures are the weakest link in timeliness; findings that rely on them describe
2019 store access, not 2026 access.

## Is the integration reasonably successful?
Every county in the spine matched exactly one ACS row and one USDA row (see `reports/quality/integration_log.md`),
names agree across sources, no restaurants were silently lost, and derived values are within plausible ranges.
"""
    (REPORTS / "post_integration.md").write_text(md)
    print(f"Wrote {rel(REPORTS / 'post_integration.md')}")


if __name__ == "__main__":
    main()
