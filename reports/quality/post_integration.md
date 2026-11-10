# Post-integration quality: `data/integrated/il_county_integrated.csv`

## Completeness
- Rows: **102** (expected 102); unique FIPS: 102
- Missing values in key columns: {'mcd_count': 0, 'acs_population': 0, 'median_hh_income': 0, 'usda_pop2010': 0, 'pct_low_access_1_10': 0, 'pct_pop_in_lila_tracts': 0, 'pct_pop_urban_tracts': 0, 'land_area_sqmi': 0}
- Restaurants: 829 after cleaning -> 652 assigned to a county
  -> **652** counted in the integrated table. The other 177 lie outside
  Illinois (the download is a rectangle) and are listed in `reports/quality/assign_counties_log.csv`;
  no Illinois restaurant was dropped without a log entry.
- Counties with zero restaurants (kept as true zeros): 17
- Lowest USDA low-access coverage in any county: 100.0% of 2010 population

## Consistency
- County names agree between TIGER and ACS for **102/102** counties and between TIGER and USDA
  for **102/102** (after normalising case, punctuation and "Saint/St.").
  Because the join used FIPS codes, agreeing names are an independent check that the join is correct.
- Mismatches:

_none_
- Duplicate FIPS in output: 0

## Accuracy
- Statewide McDonald's per 100k residents: **5.14**
- ACS total population 12,694,798 vs USDA 2010 base 12,830,632;
  median county change -6.12%. Counties whose population changed more than 15% between the
  USDA 2010 base and the ACS (largest first, max 15 shown; these make the 2010-based USDA shares less representative):

| county_name | pop_change_2010_to_acs_pct |
|---|---|
| Alexander | -40.82 |
| Kendall | 19.99 |
| Pulaski | -18.6 |
| McDonough | -17.45 |
| Hardin | -16.55 |
| Pope | -16.35 |
| Greene | -15.86 |
| Henderson | -15.52 |

- Counties with extreme restaurants-per-100k (|z| > 3), to be checked by hand (small populations inflate rates):

| county_name | mcd_count | acs_population | mcd_per_100k |
|---|---|---|---|
| Edwards | 1 | 6075 | 16.461 |
| Brown | 1 | 6322 | 15.818 |

- All percentage columns within 0-100: True
- Address state tag vs. spatial join (independent check): {'tagged_IL_placed_in_IL': 585, 'tagged_IL_placed_outside': 1, 'tagged_other_state_placed_in_IL': 0, 'tagged_other_state_placed_outside': 139, 'no_state_tag_placed_in_IL': 67}
- 102 of 102 'Chicago' addresses fall in Cook County

## Timeliness

| Measure | Source | Reference period | Lag vs. OSM snapshot |
|---|---|---|---|
| Restaurants | OpenStreetMap | snapshot (see data/raw/manifest.json) | current |
| Population, income | ACS 5-year | 2020-2024 | ~2-4 years before snapshot |
| Food access, urban flag | USDA LRAM | stores 2019, population 2010 | ~7-16 years before snapshot |
| County boundaries | TIGER/Line | 2024 | boundaries unchanged since 2010 |

The USDA measures are the weakest link in timeliness; findings that rely on them describe
2019 store access, not 2026 access.

## Is the integration reasonably successful?
Every county in the spine matched exactly one ACS row and one USDA row (see `reports/quality/integration_log.md`),
names agree across sources, no restaurants were silently lost, and derived values are within plausible ranges.
