"""Clean the OSM McDonald's extract.

Owner: Elizabeth Abraham

Input : data/raw/osm/mcdonalds_il_ohsome.geojson
Output: data/processed/osm_mcdonalds_clean.csv
        reports/quality/clean_osm_log.csv   (every dropped or merged record and why)

Steps (each addresses an issue found in reports/quality/pre_osm.md)
  1. Keep only operating McDonald's restaurants (accuracy). Each dropped feature is
     labelled with a reason: closed, Ronald McDonald House, PlayPlace mapped
     separately, other object (sign, camera), or not McDonald's.
  2. Drop features with no coordinates (completeness: cannot be placed in a county).
  3. Drop exact duplicate OSM ids (consistency).
  4. Merge near-duplicates: the same restaurant mapped as both a point and a
     building outline. Two features are merged when they are < 50 m apart, or
     < 150 m apart and share the same normalised street address. The record with
     the most tags is kept (consistency / accuracy: avoids double counting).
  5. Standardise name, state, and postcode formats (consistency).

Usage:  python -m scripts.clean.clean_osm
"""
from __future__ import annotations

import pandas as pd

from scripts.common import PROCESSED, RAW, REPORTS, ensure_dirs, rel
from scripts.osm_utils import haversine_m, load_osm, non_restaurant_reason

IN = RAW / "osm" / "mcdonalds_il_ohsome.geojson"
OUT = PROCESSED / "osm_mcdonalds_clean.csv"
LOG = REPORTS / "clean_osm_log.csv"

NEAR_M = 50.0
NEAR_SAME_ADDR_M = 150.0


def norm_addr(df: pd.DataFrame) -> pd.Series:
    street = (df["addr:street"].fillna("").str.lower()
              .str.replace(r"[^a-z0-9 ]", "", regex=True).str.replace(r"\s+", " ", regex=True).str.strip())
    hn = df["addr:housenumber"].fillna("").str.strip()
    out = hn + " " + street
    return out.where((hn != "") & (street != ""))


def cluster_duplicates(df: pd.DataFrame) -> pd.Series:
    """Union-find over pairs that meet the duplicate rule; returns a cluster id per row."""
    parent = list(range(len(df)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    lat, lon = df["lat"].to_numpy(float), df["lon"].to_numpy(float)
    addr = df["addr_norm"].to_numpy(object)
    for i in range(len(df)):
        d = haversine_m(lat[i], lon[i], lat[i + 1:], lon[i + 1:])
        for k, dist in enumerate(d):
            j = i + 1 + k
            same_addr = addr[i] is not None and addr[i] == addr[j] and not pd.isna(addr[i])
            if dist < NEAR_M or (dist < NEAR_SAME_ADDR_M and same_addr):
                parent[find(j)] = find(i)
    return pd.Series([find(i) for i in range(len(df))], index=df.index)


def main() -> None:
    ensure_dirs()
    df, meta = load_osm(IN)
    log = []

    def drop(mask, reason):
        nonlocal df
        for _, r in df[mask].iterrows():
            log.append({"osm_uid": r["osm_uid"], "name": r["name"], "action": "dropped", "reason": reason})
        df = df[~mask].copy()

    n0 = len(df)
    reasons = non_restaurant_reason(df)
    for label in reasons.dropna().unique():
        drop(reasons.reindex(df.index).eq(label), label)
    df["tagging_note"] = None
    df.loc[df["amenity"].isna(), "tagging_note"] = "building with McDonald's brand but no amenity tag"
    drop(df["lat"].isna() | df["lon"].isna(), "missing coordinates")
    drop(df["osm_uid"].duplicated(), "duplicate OSM id")

    df = df.reset_index(drop=True)
    df["addr_norm"] = norm_addr(df)
    df["dup_cluster"] = cluster_duplicates(df)
    df["_type_rank"] = df["osm_type"].map({"node": 0, "way": 1, "relation": 2})
    df = df.sort_values(["dup_cluster", "n_tags", "_type_rank"], ascending=[True, False, True])
    keep = ~df["dup_cluster"].duplicated()
    kept_uid = df[keep].set_index("dup_cluster")["osm_uid"]
    for _, r in df[~keep].iterrows():
        log.append({"osm_uid": r["osm_uid"], "name": r["name"], "action": "merged",
                    "reason": f"near-duplicate of {kept_uid[r['dup_cluster']]}"})
    # carry the address over from the merged twin if the kept record lacks it
    addr_cols = ["addr:housenumber", "addr:street", "addr:city", "addr:postcode", "addr:state"]
    filled = df.groupby("dup_cluster")[addr_cols].transform("first")
    df[addr_cols] = df[addr_cols].fillna(filled)
    df["n_merged"] = df.groupby("dup_cluster")["osm_uid"].transform("size")
    df = df[keep].copy()

    # Standardise formats
    df["name_original"] = df["name"]
    df["name"] = "McDonald's"
    df["addr:state"] = df["addr:state"].str.strip().str.upper().replace({"ILLINOIS": "IL", "ILL": "IL"})
    df["addr:postcode"] = df["addr:postcode"].astype("string").str.extract(r"(\d{5})", expand=False)
    df["addr:city"] = df["addr:city"].str.strip().str.title()

    out = df[["osm_uid", "osm_type", "osm_id", "name", "name_original", "lat", "lon",
              "addr:housenumber", "addr:street", "addr:city", "addr:state", "addr:postcode",
              "brand:wikidata", "amenity", "drive_through", "osm_last_edit", "n_merged", "tagging_note"]]
    out = out.rename(columns=lambda c: c.replace("addr:", "addr_").replace("brand:wikidata", "brand_wikidata"))
    out = out.sort_values("osm_uid")
    out.to_csv(OUT, index=False)
    pd.DataFrame(log, columns=["osm_uid", "name", "action", "reason"]).to_csv(LOG, index=False)
    print(f"OSM: {n0} raw elements -> {len(out)} restaurants "
          f"({sum(l['action'] == 'dropped' for l in log)} dropped, "
          f"{sum(l['action'] == 'merged' for l in log)} merged) -> {rel(OUT)}")


if __name__ == "__main__":
    main()
