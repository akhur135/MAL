# Project Plan: McDonald's, Income, and Food Access Across Illinois Counties

_Updated for Milestone 3 (Nov 19, 2026). Changes since the Oct 12 version are listed in
[StatusReport.md](StatusReport.md#changes-to-the-project-plan)._

## Overview

This project looks at how McDonald's restaurants are distributed across Illinois counties and how that
distribution relates to income, population, and access to grocery stores. McDonald's operates in urban,
suburban, and rural communities, but the number of restaurants a community has may depend on its
characteristics.

We integrate three public sources: restaurant locations from OpenStreetMap (OSM), county demographics from
the U.S. Census Bureau's American Community Survey (ACS), and tract-level food access measures from the
USDA Economic Research Service. Using Python, Pandas, and GeoPandas, we acquire each dataset with a script,
assess its quality, clean it, assign restaurant coordinates to counties with Census TIGER/Line boundaries,
and merge everything on the 5-digit county FIPS code. We then compare restaurant density (per 100,000
residents) with median household income, low grocery access, and urban/rural status.

The focus is the data curation process rather than advanced statistics. We aim to show how data from
different sources can be evaluated, cleaned, and integrated into one dataset that answers meaningful
questions. Deliverables are an integrated county dataset, a reproducible Snakemake workflow, quality and
cleaning documentation, and visualizations comparing Illinois counties.

## Team

| Member | Role | Responsibilities |
|---|---|---|
| Elizabeth Abraham | OSM data lead | Acquire McDonald's locations from OpenStreetMap (ohsome API); profile, filter and de-duplicate them; assign restaurants to counties (spatial join) |
| Anishka Khurana | Census data lead | Acquire ACS county estimates through the Census API; choose variables; handle missing-value codes and margins of error; prepare the FIPS key |
| Mahitha Pamulapati | USDA data lead | Acquire the USDA food access file; review its documentation; assess quality and limitations; aggregate tracts to counties |

Shared by all: integration, post-integration quality assessment, workflow (Snakefile), analysis,
documentation, metadata, and the final README. Each member commits their own scripts and report sections
so contributions are visible in the Git history.

## Research Questions

**Main question:** How does the distribution of McDonald's restaurants across Illinois counties relate to
household income, population, and access to grocery stores?

1. Do counties with higher median household incomes have more or fewer McDonald's restaurants per capita
   than lower-income counties?
2. How does the number of McDonald's restaurants vary with county population size?
3. Is McDonald's density related to the share of residents with low access to a supermarket?
4. Do urban and rural counties differ in McDonald's distribution?

We aim to describe patterns and relationships, not to show that one factor causes another.

## Datasets

None of the datasets come from Kaggle.

### Dataset 1: McDonald's locations, OpenStreetMap
- **Source:** OpenStreetMap, © OpenStreetMap contributors, ODbL 1.0. We retrieve it through the **ohsome API**
  (https://api.ohsome.org, HeiGIT / Heidelberg University), pinned to the OSM snapshot of 2026-07-27.
  The original plan named the Overpass API, but the public Overpass servers were overloaded and refused our requests
  in November 2026 (see the status report). ohsome serves the same OSM data from a dated snapshot, which is also
  easier to reproduce.
- **Content:** every OSM feature in a rectangle around Illinois that carries the McDonald's brand id
  (`brand:wikidata=Q38076`), the McDonald's brand tag, or a common spelling of the name. This also includes
  "Ronald McDonald House", so we can measure features that share the name but are not restaurants. Fields include the OSM id,
  location, address tags, and last edit time and version.
- **Format:** GeoJSON. 864 features (about 1 MB).
- **Role:** provides the restaurant count for each county.
- **Known issues:** volunteer-maintained, so restaurants may be missing, closed, mis-tagged or mapped twice. The
  rectangle also includes restaurants in neighbouring states.

### Dataset 2: American Community Survey 5-year estimates, U.S. Census Bureau
- **Source:** Census Data API, 2020-2024 ACS 5-year (https://api.census.gov/data/2024/acs/acs5.html).
- **Content:** 102 Illinois counties; total population (`B01003_001E`) and median household income
  (`B19013_001E`), each with its margin of error.
- **Format:** JSON (array of arrays), public domain. A free API key is required (kept out of the repository).
- **Role:** population for per-capita rates; income for questions 1 and 2.
- **Known issues:** these are survey estimates with sampling error, and missing values are coded as large negative numbers.

### Dataset 3: Food access, USDA Economic Research Service
- **Source:** 2019 Large Retailer Access Map (LRAM), formerly the Food Access Research Atlas
  (https://ers.usda.gov/data-products/food-access-research-atlas/download-the-data).
- **Content:** about 3,100 Illinois census tracts (2010 boundaries). We use population, the urban flag,
  low-income and low-access flags, and counts of people living more than 1 mile (urban) or 10 miles (rural)
  from a supermarket.
- **Format:** ZIP containing an Excel workbook, public domain.
- **Role:** low-access shares for question 3 and the urban/rural classification for question 4.
- **Known issues:** the oldest source (stores 2019, population 2010) and at a finer grain, so it must be
  aggregated to counties.

### Supporting geography: TIGER/Line 2024 counties
County polygons from the Census Bureau, used to place each restaurant in a county and to provide land area.

## Integration Plan

1. **Spatial join:** each restaurant coordinate is assigned to the TIGER county polygon that contains it. Restaurants that fall in no Illinois county are outside the state and are dropped, with a log entry.
2. **Key preparation:** ACS `state` plus `county` becomes the 5-digit FIPS. The USDA county FIPS is the
   first 5 digits of the 11-digit tract id.
3. **Aggregation:** USDA tract counts are summed to counties, and percentages are computed from the summed counts rather than averaged.
4. **Merge:** the 102 TIGER counties form the base table. Restaurant counts, ACS, and USDA data are left-joined on
   `county_fips`, using one-to-one validation and match indicators.
5. **Derived measures:** restaurants per 100,000 residents, per 1,000 square miles, population density,
   income quartile, and urban/rural status (urban if at least 50% of the county's population lives in urban
   tracts).

## Data Lifecycle

We follow the **USGS Science Data Lifecycle Model**: _Plan_ (this document) → _Acquire_ (scripts in
`scripts/acquire/`) → _Process_ (quality assessment, cleaning, integration) → _Analyze_ → _Preserve_
(GitHub release with frozen raw data and checksums) → _Publish/Share_ (public repository). Its
cross-cutting activities map to our metadata and data dictionary (_Describe_), our pre- and
post-integration quality reports (_Manage Quality_), and Git version control (_Backup & Secure_).

## Storage and Organization

The project uses file-based storage with a layered folder structure: `data/raw` (unchanged downloads in
their original formats: JSON, ZIP/XLSX, GeoJSON), `data/processed` (cleaned single-source tables in
tidy CSV format), and `data/integrated` (one table with one row per county). Every raw file is recorded in
`data/raw/manifest.json` with its URL, retrieval time, size, and SHA-256 checksum. The model is
relational: each table has a clear grain (restaurant, tract, or county) and keys (`osm_uid`, `tract_fips`,
`county_fips`).

## Ethical and Legal Considerations

- **OSM (ODbL 1.0):** requires attribution, and any derived database we publish must be shared under ODbL. Our
  restaurant tables and the integrated table will carry an ODbL notice. We send a single request to ohsome
  with an identifying User-Agent and cite HeiGIT as the provider.
- **Census and TIGER:** public domain. The Census API terms of service require the statement "This product uses
  the Census Bureau Data API but is not endorsed or certified by the Census Bureau."
- **USDA ERS:** public domain (federal work). We will cite it as requested by ERS.
- **Privacy:** none of the data describes individuals. We request only edit timestamps and versions from
  OSM, not mapper usernames. Our Census API key is a personal credential. It is read from an environment variable
  and never committed.
- **Interpretation:** results are county-level associations. We will avoid statements about individuals
  (the ecological fallacy) and avoid stigmatizing low-income or rural communities.

## Timeline

| Dates | Task | Owner |
|---|---|---|
| Oct 12 | Project plan; repository; dataset selection | All |
| Oct 13-25 | Acquisition scripts and raw data with checksums | Elizabeth (OSM), Anishka (ACS), Mahitha (USDA); TIGER: Elizabeth |
| Oct 26-Nov 5 | Pre-integration quality assessment (accuracy, completeness, timeliness, consistency) | Each member for their dataset; all review |
| Nov 6-12 | Cleaning scripts for each source | Each member for their dataset |
| Nov 13-19 | Spatial join, integration, post-integration quality assessment, Snakefile, status report | All |
| Nov 20-30 | Analysis and visualizations (questions 1-4); refine findings | Anishka (income/population), Mahitha (food access, urban/rural), Elizabeth (maps) |
| Dec 1-4 | Metadata (Schema.org/DCAT JSON-LD), data dictionary, licenses, `pip freeze`, final README | All |
| Dec 5-6 | Test the workflow on a fresh clone; fix issues | All |
| Dec 7 | `final-project` release | All |

## Constraints

- OSM completeness is unknown. There is no official public list of Illinois McDonald's to check against.
- The public Overpass servers were unreliable (overloaded and blocking cloud traffic), so we switched to ohsome. Its snapshot (July 27, 2026) is about 3.5 months old.
- The sources describe different years: OSM is a 2026 snapshot, ACS covers 2020-2024, and USDA covers 2019 stores and 2010 population.
- ACS estimates have sampling error, which is larger for small rural counties.
- USDA uses 2010 tract boundaries. County boundaries did not change, which is why we integrate at the county level.
- Per-capita rates are unstable for very small counties, where a single restaurant changes the rate a lot.
- The analysis is correlational only, and the sample is limited to 102 counties.

## Gaps

- We have no independent source to check how complete OSM is. We are considering a manual spot check of
  OSM against the official McDonald's restaurant locator for a sample of counties.
- Our urban/rural rule uses USDA tract flags. We may compare it with USDA Rural-Urban Continuum Codes.
- We will choose the metadata standard (Schema.org or DCAT) during Module 15.
