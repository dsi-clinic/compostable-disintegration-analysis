from __future__ import annotations

from pathlib import Path

import pandas as pd


def open_workbook(input_file: Path) -> pd.ExcelFile:
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    return pd.ExcelFile(input_file)


def read_sheet(xl: pd.ExcelFile, sheet_name: str) -> pd.DataFrame:
    df = pd.read_excel(xl, sheet_name=sheet_name, header=0)
    return _drop_empty_trailing(df)


def _drop_empty_trailing(df: pd.DataFrame) -> pd.DataFrame:
    # The new workbook has unnamed/empty trailing columns beyond the real data.
    # Drop columns whose header is NaN or an "Unnamed: N" placeholder AND that
    # have no non-null values.
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
