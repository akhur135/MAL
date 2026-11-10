# McDonald's, Income, and Food Access Across Illinois Counties

IS 477 (Fall 2026) course project: a data curation pipeline that integrates OpenStreetMap restaurant
locations, U.S. Census ACS demographics, and USDA food access data at the Illinois county level.

> **Status:** interim (Milestone 3). The full project report will replace this README for the
> final release on Dec 7. See [ProjectPlan.md](ProjectPlan.md) and [StatusReport.md](StatusReport.md).

## Contributors
- Elizabeth Abraham
- Anishka Khurana
- Mahitha Pamulapati

## Repository layout

```
data/
  raw/            unmodified downloads (frozen snapshot) + manifest.json (URL, time, SHA-256)
    osm/          mcdonalds_il_ohsome.geojson
    census/       acs5_2024_il_county.json
    usda/         lram_2019.zip, lram_2019_illinois.csv
    tiger/        il_counties_2024.geojson
  processed/      cleaned, single-source tables
  integrated/     il_county_integrated.csv  (one row per county)
  cache/          large national downloads, git-ignored
scripts/
  acquire/        one script per source
  quality/        pre-integration profiling (one per source) + post-integration assessment
  clean/          one cleaning script per source
  integrate/      spatial join to counties; FIPS-based merge
  analysis/       preliminary descriptive analysis and figures
reports/quality/  generated quality reports and cleaning/integration logs
results/          tables/ and figures/
docs/             data dictionary
Snakefile         workflow (orchestrator)
run_all.sh        equivalent run-all script
```

Naming convention: `<source>_<year>_<geography>.<ext>` for raw files, `<source>_<grain>_clean.csv` for processed files.

## Reproducing (current state)

Requires Python 3.11+.

```bash
git clone <this repo> && cd <repo>
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
snakemake --cores 1          # or: bash run_all.sh
```

Raw data is committed with SHA-256 checksums in `data/raw/manifest.json`, so the workflow re-uses that
snapshot and does not need network access. The one exception is the national TIGER/Line county file
(over 50 MB, not committed); it is downloaded only if `data/raw/tiger/il_counties_2024.geojson` is missing.
To pull fresh data from every source, set a free Census API key (`export CENSUS_API_KEY=...`, see
`scripts/acquire/acquire_census_acs.py`) and run `bash run_all.sh --refresh`. The OSM download is pinned to the
ohsome snapshot of 2026-07-27, so it returns the same records.

Order of steps: acquire → profile (pre-integration quality) → clean → assign counties → integrate →
post-integration quality → analysis.

## Data sources and licenses
- © OpenStreetMap contributors, available under the [Open Database License (ODbL) 1.0](https://opendatacommons.org/licenses/odbl/1-0/); retrieved through the [ohsome API](https://api.ohsome.org) (HeiGIT).
- U.S. Census Bureau, American Community Survey 2020-2024 5-year estimates and TIGER/Line 2024 (public domain).
  This product uses the Census Bureau Data API but is not endorsed or certified by the Census Bureau.
- USDA Economic Research Service, 2019 Large Retailer Access Map (formerly the Food Access Research Atlas) (public domain).
