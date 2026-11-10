# Pre-integration quality: ACS 5-year (2020-2024) Illinois counties

Source file: `data/raw/census/acs5_2024_il_county.json`  |  rows: **102** (expected 102)

## Completeness
- Counties missing: **0**
- Null / non-numeric values: {'B01003_001E': 0, 'B01003_001M': 0, 'B19013_001E': 0, 'B19013_001M': 0}
- Census annotation (sentinel) codes such as -666666666: {'B01003_001E': 0, 'B01003_001M': 102, 'B19013_001E': 0, 'B19013_001M': 0}

## Accuracy
ACS values are survey **estimates** with 90% margins of error. We use the coefficient of
variation (CV = (MOE/1.645)/estimate) as a reliability measure for median household income.

- Median CV: **3.38%**, max CV: **13.74%**
- Counties with CV > 15% (use with caution): **0**; CV > 30% (unreliable): **0**
- Population range 3,605 to 5,182,090; state total 12,694,798
- Income range $42,463 to $112,096; negative values after removing sentinels: 0

Least precise income estimates:

| NAME | median_hh_income | MOE | CV_% |
|---|---|---|---|
| Hardin County, Illinois | 54271 | 12264 | 13.7 |
| Clay County, Illinois | 60417 | 11361 | 11.4 |
| Pope County, Illinois | 60050 | 8584 | 8.7 |
| Pulaski County, Illinois | 42463 | 5028 | 7.2 |
| Scott County, Illinois | 66705 | 7853 | 7.2 |

## Consistency
- All rows state FIPS 17: True; 5-digit GEOIDs: True; duplicate GEOIDs: 0
- Names in "X County, Illinois" form: 102 of 102
- The API returns every value as text, so all values must be cast to numbers.

## Timeliness
- Pooled survey period 2020-2024; incomes in 2024 dollars. This is the most recent 5-year
  release, but it describes a period roughly 2-4 years before the OSM snapshot.
