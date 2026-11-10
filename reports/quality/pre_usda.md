# Pre-integration quality: USDA 2019 Large Retailer Access Map (Illinois tracts)

Source file: `data/raw/usda/lram_2019_illinois.csv` (Illinois rows of the ERS national file)
Rows: **3115** tracts (expected 3123 for 2010 geography); columns: 147
Selected columns missing from the file: none

## Completeness
- Distinct counties (first 5 digits of `CensusTract`): **102** of 102
- Tracts with zero 2010 population: **0**
- `lapop1` missing in tracts that do have population: **1200**

| column | % missing |
|---|---|
| lalowi10 | 91.52 |
| lapop10 | 91.52 |
| LALOWI1_10 | 45.91 |
| LAPOP1_10 | 45.91 |
| lalowi1 | 38.52 |
| lapop1 | 38.52 |
| MedianFamilyIncome | 0.67 |

## Accuracy (logical consistency checks)
- `lapop1_gt_pop2010`: **0**
- `lalowi1_gt_lapop1`: **0**
- `LAPOP1_10_gt_pop2010`: **0**
- `poverty_rate_outside_0_100`: **0**
- `Urban_not_0_1`: **0**
- `LowIncomeTracts_not_0_1`: **0**
- `LA1and10_not_0_1`: **0**
- `LILATracts_1And10_not_0_1`: **0**
- `LATracts1_not_0_1`: **0**
- `LATracts10_not_0_1`: **0**
- `negative_values`: **0**

USDA counts are modelled (population is allocated to 1/2-km grid cells and distances are
measured to the nearest store in a 2019 list), so they are estimates, not observations.

## Consistency
- Tract id lengths: {11: 3115} (should be 11); all digits:
  True; all start with 17: True
- Duplicate tracts: 0
- County name format examples: ['Adams County', 'Alexander County', 'Bond County', 'Boone County', 'Brown County']
  (contains " County" suffix: True; TIGER uses bare names
  such as "Champaign", so names are **not** a safe join key; the FIPS code is)
- Each county FIPS maps to exactly one county name: True

## Timeliness
- Store locations: 2019. Population: 2010 Census. Tract income: ACS 2014-2018. Last updated by ERS
  2021-04-27. This is the oldest of our three sources (about 5-7 years older than the ACS and the
  OSM snapshot) and uses 2010 tract boundaries. Illinois county boundaries and FIPS codes did not
  change between 2010 and 2024, so county-level aggregation is still valid.
