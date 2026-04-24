"""Excel workbook loading helpers used by the pipeline."""

from __future__ import annotations

import warnings
from pathlib import Path

import pandas as pd

# The CFTP workbook ships with sheet-level Data Validation (dropdowns, range
# constraints) that openpyxl drops on read. We don't consume those rules —
# only the cell values — so the warning is pure noise.
warnings.filterwarnings(
    "ignore",
    message="Data Validation extension is not supported",
    category=UserWarning,
    module="openpyxl.*",
)


def open_workbook(input_file: Path) -> pd.ExcelFile:
    """Open ``input_file`` as an :class:`pd.ExcelFile`.

    Raises :class:`FileNotFoundError` if the path does not exist.
    """
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    return pd.ExcelFile(input_file)


def read_sheet(xl: pd.ExcelFile, sheet_name: str) -> pd.DataFrame:
    """Read ``sheet_name`` from ``xl`` and strip unnamed trailing empty columns."""
    df = pd.read_excel(xl, sheet_name=sheet_name, header=0)
    return _drop_empty_trailing(df)


def _drop_empty_trailing(df: pd.DataFrame) -> pd.DataFrame:
    """Drop columns whose header is NaN or ``Unnamed: N`` and have no values.

    The source workbook ships with empty trailing columns past the real data;
    this keeps them from polluting downstream transforms.
    """
    keep = []
    for col in df.columns:
        name = col
        is_unnamed = (
            isinstance(name, float) and pd.isna(name)
        ) or (isinstance(name, str) and name.startswith("Unnamed:"))
        if is_unnamed and df[col].isna().all():
            continue
        keep.append(col)
    return df[keep]
