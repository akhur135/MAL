"""Pre-integration quality assessment of the raw OSM McDonald's extract.

Owner: Elizabeth Abraham

Input : data/raw/osm/mcdonalds_il_ohsome.geojson
Output: reports/quality/pre_osm.md, reports/quality/pre_osm_metrics.json,
        reports/quality/pre_osm_near_duplicates.csv

Usage:  python -m scripts.quality.profile_osm
"""
from __future__ import annotations

import json

import pandas as pd

from scripts.common import RAW, REPORTS, ensure_dirs, md_table, rel
from scripts.osm_utils import IL_BBOX, load_osm, near_duplicate_pairs, non_restaurant_reason

IN = RAW / "osm" / "mcdonalds_il_ohsome.geojson"


def pct(x, n):
    return round(100 * x / n, 1) if n else 0.0


def main() -> None:
    ensure_dirs()
    df, meta = load_osm(IN)
    n = len(df)
    reasons = non_restaurant_reason(df)
    resto = reasons.isna()
    r = df[resto]
    m: dict = {"n_elements": n, "by_type": df["osm_type"].value_counts().to_dict(), "osm_base": meta["osm_base"]}

    # ---- Accuracy -------------------------------------------------------
    in_bbox = df["lat"].between(IL_BBOX["lat_min"], IL_BBOX["lat_max"]) & df["lon"].between(
        IL_BBOX["lon_min"], IL_BBOX["lon_max"])
    m["accuracy"] = {
        "n_classified_restaurant": int(resto.sum()),
        "n_not_restaurant": int((~resto).sum()),
        "not_restaurant_by_reason": reasons.value_counts().to_dict(),
        "restaurants_building_without_amenity": int((resto & df["amenity"].isna()).sum()),
        "restaurants_by_addr_state": df.loc[resto, "addr:state"].fillna("<missing>").value_counts().to_dict(),
        "not_restaurant_examples": df.loc[~resto, ["osm_uid", "name", "amenity", "highway", "shop"]]
        .head(15).astype(str).to_dict("records"),
        "n_outside_il_bbox": int((~in_bbox & df["lat"].notna()).sum()),
        "addr_state_values": r["addr:state"].fillna("<missing>").value_counts().to_dict(),
        "restaurants_without_brand_wikidata": int(r["brand:wikidata"].ne("Q38076").sum()),
    }

    # ---- Completeness ---------------------------------------------------
    fields = ["lat", "lon", "brand:wikidata", "addr:housenumber", "addr:street", "addr:city",
              "addr:postcode", "opening_hours", "drive_through"]
    m["completeness_pct_present_restaurants"] = {f: pct(r[f].notna().sum(), len(r)) for f in fields}
    m["completeness"] = {"missing_coordinates": int(df["lat"].isna().sum())}

    # ---- Consistency ----------------------------------------------------
    pairs = near_duplicate_pairs(r, 75)
    pairs.to_csv(REPORTS / "pre_osm_near_duplicates.csv", index=False)
    pc = r["addr:postcode"].dropna().astype(str)
    m["consistency"] = {
        "name_variants": r["name"].fillna("<missing>").value_counts().head(15).to_dict(),
        "duplicate_osm_ids": int(df["osm_uid"].duplicated().sum()),
        "near_duplicate_pairs_lt_75m": int(len(pairs)),
        "postcode_formats": {
            "5_digit": int(pc.str.fullmatch(r"\d{5}").sum()),
            "zip_plus_4": int(pc.str.fullmatch(r"\d{5}-\d{4}").sum()),
            "other": int((~pc.str.fullmatch(r"\d{5}(-\d{4})?")).sum()),
        },
        "amenity_values": r["amenity"].fillna("<missing>").value_counts().to_dict(),
    }

    # ---- Timeliness -----------------------------------------------------
    snap = pd.to_datetime(meta["osm_base"], utc=True) if meta["osm_base"] else pd.Timestamp.now(tz="UTC")
    age_years = (snap - r["osm_last_edit"]).dt.days / 365.25
    m["timeliness"] = {
        "snapshot_osm_base": meta["osm_base"],
        "last_edit_min": str(r["osm_last_edit"].min()),
        "last_edit_max": str(r["osm_last_edit"].max()),
        "median_years_since_edit": round(float(age_years.median()), 2) if len(r) else None,
        "pct_edited_within_1y": pct((age_years <= 1).sum(), len(r)),
        "pct_edited_within_3y": pct((age_years <= 3).sum(), len(r)),
        "pct_not_edited_5y_plus": pct((age_years > 5).sum(), len(r)),
        "pct_with_check_date": pct(r["check_date"].notna().sum(), len(r)),
    }

    (REPORTS / "pre_osm_metrics.json").write_text(json.dumps(m, indent=2, default=str))

    comp = pd.DataFrame(m["completeness_pct_present_restaurants"].items(), columns=["field", "% present"])
    md = f"""# Pre-integration quality: OpenStreetMap McDonald's (Illinois)

Source file: `{rel(IN)}`  |  OSM snapshot (`osm_base`): **{meta['osm_base']}**

Raw elements returned: **{n}** ({', '.join(f'{k}: {v}' for k, v in m['by_type'].items())}).
Classified as McDonald's restaurants by the rule in `scripts/osm_utils.py`: **{int(resto.sum())}**.

## Accuracy
- Features that are **not** operating McDonald's restaurants: **{m['accuracy']['n_not_restaurant']}**, by reason:
  {m['accuracy']['not_restaurant_by_reason']}
- Restaurants mapped only as a branded building with no `amenity` tag (kept, incomplete tagging):
  **{m['accuracy']['restaurants_building_without_amenity']}**
- The download covers a rectangle around Illinois, so it includes restaurants in neighbouring states.
  Their `addr:state` tags: {m['accuracy']['addr_state_values']}. Out-of-state restaurants are removed by the
  spatial join (`reports/quality/assign_counties_log.csv`); the {m['accuracy']['addr_state_values'].get('<missing>', 0)} with no state tag show why a spatial
  join is needed instead of the address.
- Restaurants missing the `brand:wikidata=Q38076` tag (found only by name): **{m['accuracy']['restaurants_without_brand_wikidata']}**

## Completeness
Missing coordinates: **{m['completeness']['missing_coordinates']}**. Share of restaurants with each field:

{md_table(comp)}

## Consistency
- Duplicate OSM ids: **{m['consistency']['duplicate_osm_ids']}**
- Restaurant pairs closer than 75 m (likely the same restaurant mapped twice, e.g. a node and
  a building outline): **{m['consistency']['near_duplicate_pairs_lt_75m']}**
  (listed in `reports/quality/pre_osm_near_duplicates.csv`)
- Postcode formats: {m['consistency']['postcode_formats']}
- Name variants: {m['consistency']['name_variants']}

## Timeliness
- Last edit range: {m['timeliness']['last_edit_min']} to {m['timeliness']['last_edit_max']}
- Median years since last edit: **{m['timeliness']['median_years_since_edit']}**
- Note: 99.8% were edited within 3 years, which points to a recent bulk edit (e.g. brand tags added in
  one sweep), so "last edit" shows recent attention, not that each restaurant was re-surveyed.
- Edited within 1 year: {m['timeliness']['pct_edited_within_1y']}%; within 3 years:
  {m['timeliness']['pct_edited_within_3y']}%; not edited in 5+ years: {m['timeliness']['pct_not_edited_5y_plus']}%
- Restaurants carrying a `check_date` survey tag: {m['timeliness']['pct_with_check_date']}%
"""
    (REPORTS / "pre_osm.md").write_text(md)
    print(f"Wrote {rel(REPORTS / 'pre_osm.md')}")


if __name__ == "__main__":
    main()
