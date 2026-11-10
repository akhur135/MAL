#!/usr/bin/env bash
# Run-all alternative to Snakemake. Calls each single-purpose stage script in order.
# Usage (from the repository root):  bash run_all.sh            # uses committed raw data
#                                    bash run_all.sh --refresh  # re-downloads all sources
set -euo pipefail
cd "$(dirname "$0")"
REFRESH="${1:-}"

echo "== 1. Acquisition =="
python -m scripts.acquire.acquire_osm $REFRESH
python -m scripts.acquire.acquire_census_acs $REFRESH
python -m scripts.acquire.acquire_usda_fara $REFRESH
python -m scripts.acquire.acquire_tiger_counties $REFRESH

echo "== 2. Pre-integration quality assessment =="
python -m scripts.quality.profile_osm
python -m scripts.quality.profile_census
python -m scripts.quality.profile_usda

echo "== 3. Cleaning =="
python -m scripts.clean.clean_osm
python -m scripts.clean.clean_census
python -m scripts.clean.clean_usda

echo "== 4. Integration =="
python -m scripts.integrate.assign_counties
python -m scripts.integrate.integrate_county

echo "== 5. Post-integration quality assessment =="
python -m scripts.quality.assess_integrated

echo "== 6. Analysis =="
python -m scripts.analysis.preliminary_analysis
echo "Done."
