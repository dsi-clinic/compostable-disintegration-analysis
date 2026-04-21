"""Write the three pipeline outputs to the primary and dashboard directories."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import OutputSpec


def write_outputs(
    disintegration: pd.DataFrame,
    avg: pd.DataFrame,
    full: pd.DataFrame,
    outputs: OutputSpec,
    suffix: str = "",
) -> list[Path]:
    """Write all three CSVs to both output directories and return the paths.

    ``suffix`` is appended to each output filename stem (before the
    extension) — useful for generating side-by-side test outputs.
    """
    written: list[Path] = []
    for out_dir in (outputs.primary_dir, outputs.dashboard_dir):
        out_dir.mkdir(parents=True, exist_ok=True)
        written.append(_write(disintegration, out_dir, outputs.disintegration, suffix))
        written.append(_write(avg, out_dir, outputs.operating_conditions_avg, suffix))
        written.append(_write(full, out_dir, outputs.operating_conditions_full, suffix))
    return written


def _write(
    df: pd.DataFrame,
    out_dir: Path,
    filename: str,
    suffix: str,
) -> Path:
    """Write ``df`` to ``out_dir/filename`` as CSV, inserting ``suffix`` before ``.ext``."""
    stem, _, ext = filename.rpartition(".")
    name = f"{stem}{suffix}.{ext}" if suffix else filename
    path = out_dir / name
    df.to_csv(path, index=False)
    return path
