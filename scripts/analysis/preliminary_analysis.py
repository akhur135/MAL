"""Preliminary descriptive analysis of the integrated county table.

Owner: all (to be extended for the final report, due Dec 7)

Input : data/integrated/il_county_integrated.csv
Output: results/tables/summary_by_group.csv, results/tables/correlations.csv,
        results/figures/mcd_per_100k_vs_income.png,
        results/figures/mcd_per_100k_vs_low_access.png,
        results/figures/mcd_per_100k_urban_rural.png

Descriptive only: Spearman rank correlations and group medians. We do not
claim causation (see the research questions in ProjectPlan.md).

Usage:  python -m scripts.analysis.preliminary_analysis
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from scipy.stats import spearmanr

from scripts.common import INTEGRATED, RESULTS, ensure_dirs, rel

IN = INTEGRATED / "il_county_integrated.csv"
FIG, TAB = RESULTS / "figures", RESULTS / "tables"


def scatter(df, x, xlabel, fname):
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    for grp, color in [("urban", "#2a6f97"), ("rural", "#e09f3e")]:
        d = df[df["urban_rural"] == grp]
        ax.scatter(d[x], d["mcd_per_100k"], s=18 + d["acs_population"] ** 0.5 / 8, alpha=0.7,
                   color=color, label=f"{grp} ({len(d)})", edgecolor="white", linewidth=0.5)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("McDonald's per 100,000 residents")
    ax.legend(frameon=False, title="County type")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIG / fname, dpi=150)
    plt.close(fig)


def main() -> None:
    ensure_dirs()
    df = pd.read_csv(IN, dtype={"county_fips": str})

    rows = []
    for var in ["median_hh_income", "acs_population", "pct_low_access_1_10", "pct_low_access_1_10_upper",
                "pct_pop_in_lila_tracts", "pop_density_per_sqmi"]:
        d = df[["mcd_per_100k", var]].dropna()
        rho, p = spearmanr(d["mcd_per_100k"], d[var])
        rows.append({"variable": var, "n": len(d), "spearman_rho": round(rho, 3), "p_value": round(p, 4)})
    # Sensitivity: drop the smallest counties, where one restaurant swings the rate
    big = df[df["acs_population"] >= 20_000]
    for var in ["median_hh_income", "pct_low_access_1_10", "pct_pop_in_lila_tracts"]:
        rho, p = spearmanr(big["mcd_per_100k"], big[var])
        rows.append({"variable": var + " (counties >= 20k pop)", "n": len(big), "spearman_rho": round(rho, 3), "p_value": round(p, 4)})
    pd.DataFrame(rows).to_csv(TAB / "correlations.csv", index=False)

    groups = []
    for col in ["urban_rural", "income_quartile"]:
        g = df.groupby(col).agg(counties=("county_fips", "size"), restaurants=("mcd_count", "sum"),
                                population=("acs_population", "sum"),
                                median_mcd_per_100k=("mcd_per_100k", "median")).reset_index()
        g["pooled_mcd_per_100k"] = (g["restaurants"] / g["population"] * 1e5).round(2)
        g.insert(0, "grouping", col)
        groups.append(g.rename(columns={col: "group"}))
    pd.concat(groups).to_csv(TAB / "summary_by_group.csv", index=False)

    scatter(df, "median_hh_income", "Median household income (ACS 2020-2024, $)", "mcd_per_100k_vs_income.png")
    scatter(df, "pct_low_access_1_10", "% of population with low supermarket access (USDA 2019)",
            "mcd_per_100k_vs_low_access.png")

    fig, ax = plt.subplots(figsize=(5, 4.5))
    data = [df.loc[df["urban_rural"] == g, "mcd_per_100k"].dropna() for g in ["urban", "rural"]]
    ax.boxplot(data, tick_labels=["Urban", "Rural"], widths=0.5)
    ax.set_ylabel("McDonald's per 100,000 residents")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIG / "mcd_per_100k_urban_rural.png", dpi=150)
    plt.close(fig)

    print(pd.DataFrame(rows).to_string(index=False))
    print(f"Wrote tables to {rel(TAB)} and figures to {rel(FIG)}")


if __name__ == "__main__":
    main()
