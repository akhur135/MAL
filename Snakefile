# Snakemake workflow: raw data acquisition -> quality assessment -> cleaning ->
# integration -> post-integration quality -> analysis.
# Run from the repository root:   snakemake --cores 1
# Each rule calls one single-purpose script in scripts/.  Raw files are committed
# (frozen snapshot + SHA-256 in data/raw/manifest.json), so acquisition rules are
# skipped on a fresh clone unless you delete the raw file or run
# `snakemake --cores 1 --forcerun acquire_osm` (which needs network access).

PY = "python -m"

rule all:
    input:
        "reports/quality/pre_osm.md",
        "reports/quality/pre_census.md",
        "reports/quality/pre_usda.md",
        "reports/quality/post_integration.md",
        "results/tables/correlations.csv",
        "results/figures/mcd_per_100k_vs_income.png"

# ---------- 1. Acquisition ----------
rule acquire_osm:
    output: "data/raw/osm/mcdonalds_il_ohsome.geojson"
    shell: "{PY} scripts.acquire.acquire_osm"

rule acquire_census:
    output: "data/raw/census/acs5_2024_il_county.json"
    shell: "{PY} scripts.acquire.acquire_census_acs"

rule acquire_usda:
    output: "data/raw/usda/lram_2019_illinois.csv"
    shell: "{PY} scripts.acquire.acquire_usda_fara"

rule acquire_tiger:
    output: "data/raw/tiger/il_counties_2024.geojson"
    shell: "{PY} scripts.acquire.acquire_tiger_counties"

# ---------- 2. Pre-integration quality assessment ----------
rule profile_osm:
    input: rules.acquire_osm.output
    output: "reports/quality/pre_osm.md"
    shell: "{PY} scripts.quality.profile_osm"

rule profile_census:
    input: rules.acquire_census.output
    output: "reports/quality/pre_census.md"
    shell: "{PY} scripts.quality.profile_census"

rule profile_usda:
    input: rules.acquire_usda.output
    output: "reports/quality/pre_usda.md"
    shell: "{PY} scripts.quality.profile_usda"

# ---------- 3. Cleaning ----------
rule clean_osm:
    input: rules.acquire_osm.output, "reports/quality/pre_osm.md"
    output: "data/processed/osm_mcdonalds_clean.csv"
    shell: "{PY} scripts.clean.clean_osm"

rule clean_census:
    input: rules.acquire_census.output, "reports/quality/pre_census.md"
    output: "data/processed/census_county_clean.csv"
    shell: "{PY} scripts.clean.clean_census"

rule clean_usda:
    input: rules.acquire_usda.output, "reports/quality/pre_usda.md"
    output: "data/processed/usda_county_clean.csv", "data/processed/usda_tract_clean.csv"
    shell: "{PY} scripts.clean.clean_usda"

# ---------- 4. Integration ----------
rule assign_counties:
    input: rules.clean_osm.output, rules.acquire_tiger.output
    output: "data/processed/osm_mcdonalds_with_county.csv"
    shell: "{PY} scripts.integrate.assign_counties"

rule integrate:
    input:
        rules.assign_counties.output,
        rules.clean_census.output,
        "data/processed/usda_county_clean.csv",
        rules.acquire_tiger.output
    output: "data/integrated/il_county_integrated.csv"
    shell: "{PY} scripts.integrate.integrate_county"

# ---------- 5. Post-integration quality ----------
rule assess_integrated:
    input: rules.integrate.output
    output: "reports/quality/post_integration.md"
    shell: "{PY} scripts.quality.assess_integrated"

# ---------- 6. Analysis ----------
rule analysis:
    input: rules.integrate.output, "reports/quality/post_integration.md"
    output:
        "results/tables/correlations.csv",
        "results/tables/summary_by_group.csv",
        "results/figures/mcd_per_100k_vs_income.png",
        "results/figures/mcd_per_100k_vs_low_access.png",
        "results/figures/mcd_per_100k_urban_rural.png"
    shell: "{PY} scripts.analysis.preliminary_analysis"
