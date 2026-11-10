"""Helpers for turning raw OSM (ohsome GeoJSON) into a flat table (used by profiling and cleaning)."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

TAGS_OF_INTEREST = [
    "name", "brand", "brand:wikidata", "amenity", "shop", "leisure", "highway", "building", "cuisine",
    "addr:housenumber", "addr:street", "addr:city", "addr:state", "addr:postcode",
    "opening_hours", "drive_through", "check_date", "operator", "disused:amenity", "was:amenity", "end_date",
]

# Rough Illinois bounding box (with a small buffer) for a cheap plausibility check.
IL_BBOX = {"lat_min": 36.9, "lat_max": 42.6, "lon_min": -91.6, "lon_max": -87.0}


def load_osm(path: Path) -> tuple[pd.DataFrame, dict]:
    """Flatten the raw ohsome GeoJSON (elements/bbox) into one row per OSM feature.

    The location is the centre of each feature's bounding box: the point itself for
    a node, the centre of the outline for a building (way/relation).
    """
    payload = json.loads(Path(path).read_text())
    rows = []
    for f in payload["features"]:
        p = f["properties"]
        coords = f["geometry"]["coordinates"]
        if f["geometry"]["type"] == "Point":
            lon, lat = coords
        else:
            ring = coords[0] if f["geometry"]["type"] == "Polygon" else coords[0][0]
            xs, ys = [c[0] for c in ring], [c[1] for c in ring]
            lon, lat = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        osm_type, osm_id = p["@osmId"].split("/")
        tags = {k: v for k, v in p.items() if not k.startswith("@")}
        row = {
            "osm_type": osm_type,
            "osm_id": int(osm_id),
            "osm_uid": p["@osmId"],
            "lat": lat,
            "lon": lon,
            "osm_last_edit": p.get("@lastEdit"),
            "osm_version": p.get("@version"),
            "n_tags": len(tags),
        }
        for t in TAGS_OF_INTEREST:
            row[t] = tags.get(t)
        rows.append(row)
    df = pd.DataFrame(rows)
    for t in TAGS_OF_INTEREST:
        if t not in df:
            df[t] = None
    df["osm_last_edit"] = pd.to_datetime(df["osm_last_edit"], utc=True, errors="coerce")
    snap = payload["features"][0]["properties"].get("@snapshotTimestamp") if payload["features"] else None
    meta = {"osm_base": snap, "query": payload.get("_request")}
    return df, meta


def haversine_m(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6_371_000 * np.arcsin(np.sqrt(a))


def near_duplicate_pairs(df: pd.DataFrame, threshold_m: float = 75.0) -> pd.DataFrame:
    """All pairs of rows closer than threshold_m metres (O(n^2); fine for ~1k rows)."""
    d = df.dropna(subset=["lat", "lon"]).reset_index(drop=True)
    lat, lon = d["lat"].to_numpy(float), d["lon"].to_numpy(float)
    pairs = []
    for i in range(len(d)):
        dist = haversine_m(lat[i], lon[i], lat[i + 1:], lon[i + 1:])
        for k in np.nonzero(dist < threshold_m)[0]:
            j = i + 1 + k
            pairs.append({"uid_a": d.at[i, "osm_uid"], "uid_b": d.at[j, "osm_uid"], "distance_m": round(float(dist[k]), 1)})
    return pd.DataFrame(pairs, columns=["uid_a", "uid_b", "distance_m"])


def non_restaurant_reason(df: pd.DataFrame) -> pd.Series:
    """Why an OSM feature is NOT an operating McDonald's restaurant (None = it is one).

    Rules, checked in order:
      closed      - disused:/was: prefixes or an end_date (restaurant has closed)
      charity     - Ronald McDonald House (shares the name, not a restaurant)
      playground  - McDonald's PlayPlace mapped as its own feature (part of a restaurant)
      other object- a camera, sign or other object operated by McDonald's
      not McDonald's - no McDonald's brand id and the name/brand does not match
    A building carrying brand:wikidata=Q38076 but no amenity tag is KEPT: it is a
    restaurant with incomplete tagging (checked: no restaurant is mapped nearby).
    """
    norm = lambda s: s.fillna("").str.lower().str.replace("\u2019", "'", regex=False)
    name, brand = norm(df["name"]), norm(df["brand"])
    mcd = df["brand:wikidata"].eq("Q38076") | name.str.match(r"^mc ?donald'?s\b") | brand.str.match(r"^mc ?donald'?s\b")
    food = df["amenity"].isin(["fast_food", "restaurant"])
    brand_building = df["brand:wikidata"].eq("Q38076") & df["building"].notna() & df["amenity"].isna()
    reason = pd.Series(None, index=df.index, dtype=object)
    rules = [
        ("closed (disused/was/end_date tag)", df["disused:amenity"].notna() | df["was:amenity"].notna() | df["end_date"].notna()),
        ("charity: Ronald McDonald House", name.str.contains("ronald mcdonald")),
        ("PlayPlace playground mapped separately", name.str.contains("playplace") | df["leisure"].notna()),
        ("not McDonald's", ~mcd),
        ("other object (sign, camera, etc.), not a restaurant", ~food & ~brand_building),
    ]
    for label, mask in rules:
        reason = reason.where(reason.notna() | ~mask, label)
    return reason


def is_mcdonalds_restaurant(df: pd.DataFrame) -> pd.Series:
    """True for operating McDonald's restaurants (see non_restaurant_reason)."""
    return non_restaurant_reason(df).isna()
