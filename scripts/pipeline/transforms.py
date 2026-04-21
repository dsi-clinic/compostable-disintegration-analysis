"""Sheet-level transforms driven by :class:`SheetSpec`.

``apply_sheet_spec`` handles the plumbing shared by every sheet (select,
rename, dropna/cast IDs, dedupe). The two domain-specific transforms layer
substantive logic on top: items normalizes a couple of string columns;
disintegration synthesizes a unified residuals-by-mass column from the
wet and dry measurements.
"""

from __future__ import annotations

import pandas as pd

from .config import SheetSpec


def apply_sheet_spec(raw: pd.DataFrame, spec: SheetSpec) -> pd.DataFrame:
    """Select required + available optional columns, apply ``spec`` renames,
    dropna/str-cast the ID columns, and optionally dedupe on ``dedupe_on``.
    """
    keep = [c for c in spec.required_columns if c in raw.columns]
    keep += [c for c in spec.optional_columns if c in raw.columns]
    df = raw[keep].copy()

    for c in spec.optional_columns:
        if c not in df.columns:
            df[c] = pd.NA

    if spec.rename:
        df = df.rename(columns=spec.rename)

    for c in spec.id_columns:
        df = df.dropna(subset=[c])
        df[c] = df[c].astype(str)

    if spec.dedupe_on:
        df = df.drop_duplicates(subset=[spec.dedupe_on])

    return df.reset_index(drop=True)


def transform_items(raw: pd.DataFrame, spec: SheetSpec) -> pd.DataFrame:
    """Apply ``spec`` and normalize the text columns the dashboard groups on."""
    df = apply_sheet_spec(raw, spec)
    df["Item Format"] = df["Item Format"].astype(str).str.strip().str.title()
    df["Item Brand"] = df["Item Brand"].astype(str)
    return df


def transform_disintegration(raw: pd.DataFrame, spec: SheetSpec) -> pd.DataFrame:
    """Apply ``spec`` and collapse wet/dry residuals into ``% Residuals (Mass)``.

    Per the data contract: when dry weight is available it takes precedence,
    otherwise wet weight is used. All residuals columns are returned as
    fractions in roughly ``[0, 1]``.
    """
    df = apply_sheet_spec(raw, spec)
    dry = _to_fraction(df["% Residuals (Dry Weight)"])
    wet = _to_fraction(df["% Residuals (Wet Weight)"])
    df["% Residuals (Mass)"] = dry.where(dry.notna(), wet)
    df["% Residuals (Area)"] = _to_fraction(df["% Residuals (Area)"])
    return df


def _to_fraction(series: pd.Series) -> pd.Series:
    """Normalize a residuals column to a [0,1]+ float fraction.

    Source values may arrive as:
      - NaN or empty
      - the literal string "no data" (case-insensitive)
      - a float already in fraction form (0.0..1.0+)
      - a string like "42%" or "42"
    Percent strings are divided by 100; bare numeric values are left as-is.
    """
    def convert(v: object) -> float:
        if pd.isna(v):
            return float("nan")
        if isinstance(v, str):
            s = v.strip()
            if not s or s.lower() == "no data":
                return float("nan")
            had_percent = s.endswith("%")
            s = s.rstrip("%").strip()
            try:
                num = float(s)
            except ValueError:
                return float("nan")
            return num / 100.0 if had_percent else num
        try:
            return float(v)
        except (TypeError, ValueError):
            return float("nan")

    return series.map(convert).astype(float)
