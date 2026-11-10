# Interim Status Report

**Project:** McDonald's, Income, and Food Access Across Illinois Counties
**Team:** Elizabeth Abraham, Anishka Khurana, Mahitha Pamulapati
**Milestone 3, November 19, 2026**

## 1. Summary

All tasks planned through November 19 are complete and have been run on real data. The pipeline
acquires, assesses, cleans and integrates all sources into one table covering Illinois's 102 counties, and it runs end to end with
Snakemake. The remaining work is analysis, visualization, metadata and the final README.

| Key numbers | Value |
|---|---|
| OSM features downloaded (snapshot 2026-07-27) | 864 |
| Operating McDonald's after cleaning | 829 |
| …located in Illinois | **652** |
| Counties with ≥1 restaurant / with none | 85 / 17 |
| Statewide McDonald's per 100,000 residents | 5.14 |
| ACS counties / USDA tracts | 102 / 3,115 |

## 2. Task updates

### 2.1 Acquisition: complete
| Source | Script | Raw data |
|---|---|---|
| OpenStreetMap (ohsome API) | [`acquire_osm.py`](scripts/acquire/acquire_osm.py) | [`data/raw/osm/`](data/raw/osm/) |
| ACS 2020-2024 (Census API) | [`acquire_census_acs.py`](scripts/acquire/acquire_census_acs.py) | [`data/raw/census/`](data/raw/census/) |
| USDA 2019 Large Retailer Access Map | [`acquire_usda_fara.py`](scripts/acquire/acquire_usda_fara.py) | [`data/raw/usda/`](data/raw/usda/) |
| TIGER/Line 2024 counties | [`acquire_tiger_counties.py`](scripts/acquire/acquire_tiger_counties.py) | [`data/raw/tiger/`](data/raw/tiger/) |

Every raw file's URL, retrieval time and SHA-256 checksum are recorded in [`manifest.json`](data/raw/manifest.json). The scripts
verify the checksum and skip downloading if the file is already present.

### 2.2 Pre-integration quality assessment: complete
Reports: [`pre_osm.md`](reports/quality/pre_osm.md), [`pre_census.md`](reports/quality/pre_census.md), [`pre_usda.md`](reports/quality/pre_usda.md).

- **OSM.** *Accuracy:* 34 of 864 features are not operating restaurants: 23 PlayPlace playgrounds, 7 Ronald McDonald Houses,
  2 closed restaurants, a camera and a sign. *Completeness:* 85-88% of features have address fields, and 104 have no state tag. *Consistency:* one
  restaurant is mapped twice, and postcodes mix 5-digit and ZIP+4. *Timeliness:* the median time since the last edit is 2.2 years, but only 14% of features carry a survey date.
- **ACS.** All 102 counties are present with no missing estimates. Incomes are survey estimates; the coefficient of variation
  (CV = (MOE/1.645)/estimate) is at most 13.7% (Hardin County), so no county exceeds the 15% caution threshold. Values arrive as text.
- **USDA.** There are 3,115 tracts covering all counties, and every logical check passes. Low-access counts are blank in 38.5% of tracts. We found that blanks
  occur **only** in tracts not flagged as low-access, a pattern the ERS documentation does not explain. The data is 2019 stores on 2010 tracts,
  our oldest source.

All sources can be reduced to the 5-digit county FIPS code, and Illinois county boundaries have not changed since 2010.

### 2.3 Cleaning: complete
- [`clean_osm.py`](scripts/clean/clean_osm.py) drops the 34 non-restaurants and merges the duplicate, logging a reason for every change in
  [`clean_osm_log.csv`](reports/quality/clean_osm_log.csv). It keeps two real restaurants that are tagged only as branded buildings, and standardizes formats.
- [`clean_census.py`](scripts/clean/clean_census.py) converts values to numbers, replaces missing-value codes, builds the FIPS key, and adds a reliability flag.
- [`clean_usda.py`](scripts/clean/clean_usda.py) builds the low-access measure (1 mile for urban tracts, 10 miles for rural), which matches ERS's own field in all 1,685
  tracts where both exist. USDA flags a tract when at least 500 people *or* at least 33% of residents are low-access, so a blank in an unflagged tract must lie between
  0 and min(499, 33% of the tract's population). We use 0 as the main value and keep the upper bound for a sensitivity check. The two give the same conclusions.

### 2.4 Integration: complete
[`assign_counties.py`](scripts/integrate/assign_counties.py) places each restaurant in a county with a GeoPandas point-in-polygon join:
652 fall in Illinois and 177 lie across the border, all logged. [`integrate_county.py`](scripts/integrate/integrate_county.py) left-joins
restaurant counts, ACS and USDA onto the 102 TIGER counties by FIPS with `validate="one_to_one"`. Output:
[`il_county_integrated.csv`](data/integrated/il_county_integrated.csv), documented in the [data dictionary](docs/data_dictionary.md).

### 2.5 Post-integration quality assessment: complete
[`post_integration.md`](reports/quality/post_integration.md): 102/102 counties, with no missing key values. County names agree across all
three sources for 102/102 counties, an independent check of the FIPS join. Every restaurant whose address is tagged Illinois falls in an Illinois
county; the one exception is a Keokuk, Iowa restaurant mis-tagged "IL" in OSM. **This check caught a bug in our own integration.**
A 1 km nearest-county fallback had pulled 4 out-of-state restaurants into Illinois, so we removed it. Counties whose
population changed by more than 15% since 2010, for example Alexander County (−41%), are flagged because their USDA shares are dated.

### 2.6 Workflow: complete
The [`Snakefile`](Snakefile) and [`run_all.sh`](run_all.sh) run every step. A run on a fresh copy reproduced the integrated table exactly.

### 2.7 Analysis: started
[`preliminary_analysis.py`](scripts/analysis/preliminary_analysis.py) produces [tables](results/tables/) and [figures](results/figures/).
We see no clear relationship between restaurant density and income (ρ = −0.05). Rural counties have slightly more restaurants per resident when pooled (5.88 vs. 5.06 per 100k), but all 17 counties with no
restaurants are rural. These are descriptive associations only.

## 3. Updated timeline

| Task | Planned | Status |
|---|---|---|
| Plan; acquisition; quality assessment; cleaning | Oct 12-Nov 12 | Done |
| Integration; post-integration assessment; workflow | Nov 13-19 | Done |
| Analysis and visualizations, including a county map | Nov 20-30 | In progress |
| Spot check of OSM against the McDonald's locator | Nov 20-26 | Not started |
| Metadata, licenses, `pip freeze`, data dictionary | Dec 1-4 | Dictionary drafted |
| Final README; fresh-clone test | Dec 1-6 | Not started |
| `final-project` release | Dec 7 | Not started |

## 4. Changes to the plan

- **OSM source: ohsome instead of Overpass.** The public Overpass servers were overloaded and timed out on three servers. ohsome
  (HeiGIT, Heidelberg University) serves the same OSM data from a dated snapshot, which is easier to reproduce.
- **USDA file name.** ERS renamed the dataset the *2019 Large Retailer Access Map*.
- **Measures defined.** We added bounded low-access values and a rule for urban counties: at least 50% of the county's population lives in USDA urban tracts.
- **Census API key.** The Census Bureau now requires a key. Ours is read from an environment variable and never committed.
- **New plan sections:** lifecycle, storage, ethics, constraints and gaps ([ProjectPlan.md](ProjectPlan.md)).
- **Milestone 2 feedback.** The only deduction was the missing `project-plan` tag and release. We tagged the original plan commit and
  published the release.

## 5. Challenges

1. **Overpass was unusable.** We switched to ohsome and pinned the snapshot.
2. **Non-restaurant features.** We wrote explicit rules and logged a reason for every exclusion.
3. **Out-of-state restaurants.** The spatial join decides which state a restaurant is in. A cross-check with address tags exposed and fixed a faulty fallback.
4. **Undocumented USDA blanks.** We derived bounds from the ERS flag rule instead of guessing values.
5. **Different years and geographies across sources.** We integrate at the county level and flag counties whose population changed a lot.

## 6. Individual contributions

