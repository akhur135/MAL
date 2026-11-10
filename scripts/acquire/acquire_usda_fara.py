"""Acquire the USDA ERS 2019 Large Retailer Access Map (LRAM) data,
formerly the Food Access Research Atlas (FARA), and extract Illinois tracts.

Owner: Mahitha Pamulapati

Outputs
  data/raw/usda/lram_2019.zip              original ZIP from ERS (~9 MB), checksummed
  data/raw/usda/lram_2019_illinois.csv     Illinois rows only, every column kept,
                                           CensusTract stored as text

The national file has ~72,500 tracts and ~147 columns. We keep the original
ZIP for provenance and write an Illinois-only extract (no other changes) so
later steps do not have to re-read an 80 MB spreadsheet. The 2019 data is
built on 2010 census tract boundaries.

Usage:  python -m scripts.acquire.acquire_usda_fara [--refresh]
"""
from __future__ import annotations

import argparse
import io
import zipfile

import pandas as pd
import requests

from scripts.common import RAW, USER_AGENT, already_have, ensure_dirs, record_in_manifest, rel

URL = (
    "https://www.ers.usda.gov/media/5627/"
    "2019-large-retailer-access-map-lram-formerly-known-as-the-food-access-research-atlas-fara-data.zip"
)
ZIP_OUT = RAW / "usda" / "lram_2019.zip"
IL_OUT = RAW / "usda" / "lram_2019_illinois.csv"


def download() -> None:
    r = requests.get(URL, headers={"User-Agent": USER_AGENT}, timeout=600)
    r.raise_for_status()
    ZIP_OUT.write_bytes(r.content)
    entry = record_in_manifest(
        ZIP_OUT,
        source="USDA ERS, 2019 Large Retailer Access Map / Food Access Research Atlas (public domain)",
        url=URL,
        notes="Data last updated by ERS 2021-04-27; 2010 census tract geography",
    )
    print(f"Saved {rel(ZIP_OUT)} ({entry['bytes']:,} bytes, sha256 {entry['sha256'][:12]}...)")


def find_data_sheet(xls: pd.ExcelFile) -> str:
    # The data sheet is named 'Food Access Research Atlas'; a second sheet is the variable lookup.
    for name in xls.sheet_names:
        if "food access" in name.lower() or "lram" in name.lower():
            return name
    return xls.sheet_names[0]


def extract_illinois() -> None:
    with zipfile.ZipFile(ZIP_OUT) as zf:
        members = [m for m in zf.namelist() if m.lower().endswith((".xlsx", ".csv"))]
        if not members:
            raise SystemExit(f"No .xlsx/.csv inside {rel(ZIP_OUT)}: {zf.namelist()}")
        member = max(members, key=lambda m: zf.getinfo(m).file_size)  # the data file
        raw = zf.read(member)
    print(f"Reading {member} ...")
    if member.lower().endswith(".csv"):
        df = pd.read_csv(io.BytesIO(raw), dtype={"CensusTract": str}, low_memory=False)
    else:
        xls = pd.ExcelFile(io.BytesIO(raw))
        df = pd.read_excel(xls, sheet_name=find_data_sheet(xls), dtype={"CensusTract": str})
    print(f"National file: {len(df):,} rows x {df.shape[1]} columns")
    il = df[df["State"].astype(str).str.strip().str.lower() == "illinois"].copy()
    if il.empty:
        raise SystemExit("No Illinois rows found - check the 'State' column")
    il.to_csv(IL_OUT, index=False)
    record_in_manifest(IL_OUT, source="Derived: Illinois rows of lram_2019.zip, unmodified", url=URL)
    print(f"Saved {len(il):,} Illinois tracts -> {rel(IL_OUT)}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    args = ap.parse_args()
    ensure_dirs()
    ZIP_OUT.parent.mkdir(parents=True, exist_ok=True)
    if not already_have(ZIP_OUT, args.refresh):
        download()
    if args.refresh or not IL_OUT.exists():
        extract_illinois()


if __name__ == "__main__":
    main()
