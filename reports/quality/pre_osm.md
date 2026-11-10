# Pre-integration quality: OpenStreetMap McDonald's (Illinois)

Source file: `data/raw/osm/mcdonalds_il_ohsome.geojson`  |  OSM snapshot (`osm_base`): **2026-07-27T09:00:00Z**

Raw elements returned: **864** (way: 642, node: 221, relation: 1).
Classified as McDonald's restaurants by the rule in `scripts/osm_utils.py`: **830**.

## Accuracy
- Features that are **not** operating McDonald's restaurants: **34**, by reason:
  {'PlayPlace playground mapped separately': 23, 'charity: Ronald McDonald House': 7, 'closed (disused/was/end_date tag)': 2, 'other object (sign, camera, etc.), not a restaurant': 2}
- Restaurants mapped only as a branded building with no `amenity` tag (kept, incomplete tagging):
  **2**
- The download covers a rectangle around Illinois, so it includes restaurants in neighbouring states.
  Their `addr:state` tags: {'IL': 587, '<missing>': 104, 'MO': 91, 'IA': 22, 'IN': 19, 'KY': 6, 'WI': 1}. Out-of-state restaurants are removed by the
  spatial join (`reports/quality/assign_counties_log.csv`); the 104 with no state tag show why a spatial
  join is needed instead of the address.
- Restaurants missing the `brand:wikidata=Q38076` tag (found only by name): **0**

## Completeness
Missing coordinates: **0**. Share of restaurants with each field:

| field | % present |
|---|---|
| lat | 100 |
| lon | 100 |
| brand:wikidata | 100 |
| addr:housenumber | 85.9 |
| addr:street | 85.5 |
| addr:city | 82.3 |
| addr:postcode | 87.7 |
| opening_hours | 80 |
| drive_through | 90.1 |

## Consistency
- Duplicate OSM ids: **0**
- Restaurant pairs closer than 75 m (likely the same restaurant mapped twice, e.g. a node and
  a building outline): **1**
  (listed in `reports/quality/pre_osm_near_duplicates.csv`)
- Postcode formats: {'5_digit': 633, 'zip_plus_4': 95, 'other': 0}
- Name variants: {"McDonald's": 828, '<missing>': 2}

## Timeliness
- Last edit range: 2019-07-27 22:30:00+00:00 to 2026-07-21 23:11:46+00:00
- Median years since last edit: **2.21**
- Note: 99.8% were edited within 3 years, which points to a recent bulk edit (e.g. brand tags added in
  one sweep), so "last edit" shows recent attention, not that each restaurant was re-surveyed.
- Edited within 1 year: 13.0%; within 3 years:
  99.8%; not edited in 5+ years: 0.1%
- Restaurants carrying a `check_date` survey tag: 14.1%
