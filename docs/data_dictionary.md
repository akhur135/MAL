# Data dictionary

Draft, interim milestone. The final version will be completed for the Dec 7 release.

## Integrated dataset: `data/integrated/il_county_integrated.csv`

One row per Illinois county (102 rows). Primary key: `county_fips`.

| Column | Type | Source | Definition |
|---|---|---|---|
| county_fips | text(5) | TIGER/Line 2024 | State FIPS (17) plus 3-digit county FIPS; the join key |
| county_name | text | TIGER/Line 2024 | County name without "County" (e.g. `Champaign`) |
| mcd_count | integer | OSM (cleaned, spatially joined) | McDonald's restaurants located in the county; 0 means none were mapped |
| acs_population | integer | ACS 2020-2024, B01003_001E | Total population estimate |
| mcd_per_100k | float | derived | `mcd_count / acs_population * 100,000` |
| median_hh_income | integer | ACS 2020-2024, B19013_001E | Median household income, 2024 dollars |
| income_quartile | category | derived | Quartile of `median_hh_income` across the 102 counties |
| pct_low_access_1_10 | float (%) | USDA LRAM 2019 | Share of the 2010 population living more than 1 mile (urban tract) or 10 miles (rural tract) from a supermarket. Blank tract counts (only in tracts not flagged low-access) are counted as 0 (lower bound) |
| pct_low_access_1_10_upper | float (%) | derived | Same measure with blank tract counts set to their maximum possible value, min(499, 33% of tract population); used for sensitivity checks |
| usda_la_pop_1_10_upper | float | derived | Upper-bound low-access population count |
| pct_pop_in_lila_tracts | float (%) | USDA LRAM 2019 | Share of the 2010 population living in tracts flagged low-income and low-access (`LILATracts_1And10 = 1`) |
| urban_rural | category | derived from USDA `Urban` | `urban` if 50% or more of the county's 2010 population lives in urban tracts, otherwise `rural` |
| pct_pop_urban_tracts | float (%) | USDA LRAM 2019 | Share of the 2010 population living in urban tracts |
| pop_density_per_sqmi | float | derived | `acs_population / land_area_sqmi` |
| land_area_sqmi | float | TIGER/Line 2024 `ALAND` | Land area in square miles |
| mcd_per_1000_sqmi | float | derived | Restaurants per 1,000 square miles of land |
| county_name_acs | text | ACS | County name as published by the ACS (used for the consistency check) |
| acs_population_moe | integer | ACS, B01003_001M | Margin of error, 90%. Usually blank for county totals, which are controlled to official population estimates |
| median_hh_income_moe | integer | ACS, B19013_001M | Margin of error, 90% |
| income_cv_pct | float (%) | derived | Coefficient of variation: `(MOE / 1.645) / estimate * 100` |
| income_reliability | category | derived | `high` (CV ≤ 15), `medium` (15 < CV ≤ 30), `low` (CV > 30) |
| county_name_usda | text | USDA | County name as published by USDA (used for the consistency check) |
| usda_n_tracts | integer | USDA | Number of 2010 census tracts in the county |
| usda_pop2010 | integer | USDA `Pop2010` | 2010 Census population, the denominator for USDA percentages |
| usda_pop_urban_tracts | integer | USDA | 2010 population living in urban tracts |
| usda_la_pop_1_10 | float | USDA `lapop1` / `lapop10` | Low-access population count (1 mile urban / 10 miles rural) |
| usda_la_lowinc_pop_1_10 | float | USDA `lalowi1` / `lalowi10` | Low-income and low-access population count |
| usda_n_lila_tracts | integer | USDA | Number of low-income, low-access tracts |
| usda_pop_in_lila_tracts | integer | USDA | 2010 population living in those tracts |
| usda_pop_with_la_value | integer | derived | 2010 population in tracts where the low-access count is not missing |
| pct_lowinc_low_access_1_10 | float (%) | derived | `usda_la_lowinc_pop_1_10 / usda_pop_with_la_value * 100` |
| usda_la_coverage_pct | float (%) | derived | Share of the county's 2010 population covered by non-missing low-access values |
| pop_change_2010_to_acs_pct | float (%) | derived | `(acs_population / usda_pop2010 - 1) * 100`; shows how dated the USDA base is |

## Intermediate files (`data/processed/`)

| File | Grain | Produced by |
|---|---|---|
| `osm_mcdonalds_clean.csv` | one row per restaurant | `scripts/clean/clean_osm.py` |
| `osm_mcdonalds_with_county.csv` | one row per restaurant, with county | `scripts/integrate/assign_counties.py` |
| `census_county_clean.csv` | one row per county | `scripts/clean/clean_census.py` |
| `usda_tract_clean.csv` | one row per 2010 census tract | `scripts/clean/clean_usda.py` |
| `usda_county_clean.csv` | one row per county | `scripts/clean/clean_usda.py` |

## Restaurant-level columns (`osm_mcdonalds_with_county.csv`)

| Column | Definition |
|---|---|
| osm_uid | `type/id` of the OSM feature (e.g. `node/123`); unique |
| osm_type, osm_id | OSM element type (node/way/relation) and numeric id |
| name | Standardised to `McDonald's` |
| name_original | Name exactly as tagged in OSM |
| lat, lon | WGS84 coordinates (for ways, the centre of the building outline) |
| addr_housenumber, addr_street, addr_city, addr_state, addr_postcode | Address tags; state standardised to `IL`, postcode to 5 digits |
| brand_wikidata | `Q38076` when tagged |
| amenity | `fast_food` (or `restaurant`) |
| drive_through | OSM `drive_through` tag |
| osm_last_edit | Timestamp of the feature's last edit in OSM |
| n_merged | Number of OSM features merged into this record during de-duplication |
| county_fips, county_name_tiger | County assigned by the spatial join |
| tagging_note | Set when the restaurant is mapped only as a branded building without an `amenity` tag |
