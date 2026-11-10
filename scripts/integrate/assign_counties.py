"""Assign each cleaned McDonald's restaurant to an Illinois county (spatial join).

Owner: Elizabeth Abraham

Inputs: data/processed/osm_mcdonalds_clean.csv, data/raw/tiger/il_counties_2024.geojson
Output: data/processed/osm_mcdonalds_with_county.csv
        reports/quality/assign_counties_log.csv  (restaurants outside Illinois)

Method
  * Point-in-polygon join (predicate "within") in an equal-area projection
    (EPSG:5070, NAD83 / CONUS Albers).
  * Points in no Illinois county are outside the state (the download is a
    rectangle) and are dropped and logged. TIGER county polygons include rivers
    and Lake Michigan, so an Illinois restaurant cannot fall between counties.
    An earlier version assigned points within 1 km to the nearest county; the
    address-state cross-check in assess_integrated.py showed that all 4 such
    points were across the border (Clinton IA, Munster IN, Le Claire IA,
    Beloit WI), so that fallback was removed.

Usage:  python -m scripts.integrate.assign_counties
"""
from __future__ import annotations

import geopandas as gpd
import pandas as pd

from scripts.common import PROCESSED, RAW, REPORTS, ensure_dirs, rel

POINTS = PROCESSED / "osm_mcdonalds_clean.csv"
COUNTIES = RAW / "tiger" / "il_counties_2024.geojson"
OUT = PROCESSED / "osm_mcdonalds_with_county.csv"
LOG = REPORTS / "assign_counties_log.csv"
CRS_EQUAL_AREA = 5070


def main() -> None:
    ensure_dirs()
    pts = pd.read_csv(POINTS)
    gpts = gpd.GeoDataFrame(pts, geometry=gpd.points_from_xy(pts["lon"], pts["lat"]), crs=4326).to_crs(CRS_EQUAL_AREA)
    cty = gpd.read_file(COUNTIES)[["GEOID", "NAME", "geometry"]].to_crs(CRS_EQUAL_AREA)
    cty = cty.rename(columns={"GEOID": "county_fips", "NAME": "county_name_tiger"})

    joined = gpd.sjoin(gpts, cty, how="left", predicate="within").drop(columns="index_right")
    joined = joined[~joined.index.duplicated(keep="first")]  # a point on a shared border can match twice

    unmatched = joined["county_fips"].isna()
    log = [{"osm_uid": r["osm_uid"], "action": "dropped (outside Illinois)", "addr_city": r.get("addr_city"),
            "addr_state": r.get("addr_state")} for _, r in joined[unmatched].iterrows()]

    out = pd.DataFrame(joined.drop(columns="geometry"))
    out = out[out["county_fips"].notna()].copy()
    out["county_fips"] = out["county_fips"].astype(str).str.zfill(5)
    out.to_csv(OUT, index=False)
    pd.DataFrame(log, columns=["osm_uid", "action", "addr_city", "addr_state"]).to_csv(LOG, index=False)
    print(f"Assigned {len(out)} of {len(pts)} restaurants to counties ({len(log)} outside Illinois) -> {rel(OUT)}")


if __name__ == "__main__":
    main()
