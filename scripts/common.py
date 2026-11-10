"""Shared helpers: project paths, checksums, and the acquisition manifest.

Every path in the project is built from ROOT (the repository root), so the
workflow runs from a fresh clone with no path edits.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DATA = ROOT / "data"
RAW = DATA / "raw"
PROCESSED = DATA / "processed"
INTEGRATED = DATA / "integrated"
REPORTS = ROOT / "reports" / "quality"
RESULTS = ROOT / "results"
MANIFEST = RAW / "manifest.json"

IL_STATE_FIPS = "17"
IL_EXPECTED_COUNTIES = 102  # Illinois has had 102 counties since 1859

USER_AGENT = "IS477-FA26-course-project (University of Illinois; academic use)"


def ensure_dirs() -> None:
    for d in (RAW, PROCESSED, INTEGRATED, REPORTS, RESULTS / "figures", RESULTS / "tables"):
        d.mkdir(parents=True, exist_ok=True)


def sha256_of(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def rel(path: Path) -> str:
    """Path relative to the repo root, with forward slashes (for docs/manifests)."""
    return Path(path).resolve().relative_to(ROOT).as_posix()


def record_in_manifest(path: Path, source: str, url: str, notes: str = "") -> dict:
    """Add or update a raw file's entry (URL, retrieval time, size, SHA-256)."""
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
    entry = {
        "source": source,
        "url": url,
        "retrieved_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "bytes": path.stat().st_size,
        "sha256": sha256_of(path),
        "notes": notes,
    }
    manifest[rel(path)] = entry
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return entry


def verify_against_manifest(path: Path) -> bool:
    """True if the file's current SHA-256 matches the one recorded at download."""
    if not MANIFEST.exists():
        return False
    entry = json.loads(MANIFEST.read_text()).get(rel(path))
    return bool(entry) and entry["sha256"] == sha256_of(path)


def already_have(path: Path, refresh: bool) -> bool:
    """Skip re-downloading a frozen raw snapshot unless --refresh is given.

    Raw files are committed to the repo so results are reproducible; OSM in
    particular changes daily, so re-downloading would change the results.
    """
    if refresh or not path.exists():
        return False
    ok = verify_against_manifest(path)
    print(f"[skip] {rel(path)} exists; checksum {'OK' if ok else 'NOT in manifest / MISMATCH'}")
    if not ok:
        raise SystemExit(
            f"Checksum check failed for {rel(path)}. Re-run with --refresh to re-download."
        )
    return True


def md_table(df, index: bool = False) -> str:
    """Render a DataFrame as a GitHub Markdown table without needing `tabulate`."""
    import pandas as pd

    d = df.reset_index() if index else df
    cols = [str(c) for c in d.columns]
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, row in d.iterrows():
        vals = []
        for v in row:
            if isinstance(v, float):
                vals.append("" if pd.isna(v) else f"{v:,.4g}")
            else:
                vals.append(str(v))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)
