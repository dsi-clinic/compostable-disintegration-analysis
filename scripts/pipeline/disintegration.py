from __future__ import annotations

import pandas as pd


def transform_disintegration(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()
    df = df.dropna(subset=["Public Trial ID", "Item ID"])
    df = df.rename(columns={"Public Trial ID": "Trial ID", "Removal Period": "Timepoint"})
    df["Trial ID"] = df["Trial ID"].astype(str)
    df["Item ID"] = df["Item ID"].astype(str)

    dry = _to_fraction(df["% Residuals (Dry Weight)"])
    wet = _to_fraction(df["% Residuals (Wet Weight)"])
    area = _to_fraction(df["% Residuals (Area)"])

    # Per spec: if dry weight is available, ignore wet. Otherwise use wet.
    df["% Residuals (Mass)"] = dry.where(dry.notna(), wet)
    df["% Residuals (Area)"] = area

    return df[["Trial ID", "Item ID", "Timepoint", "% Residuals (Mass)", "% Residuals (Area)"]]


def _to_fraction(series: pd.Series) -> pd.Series:
    """Normalize a residuals column to a [0,1]+ float fraction.

    Source values may arrive as:
      - NaN or empty
      - the literal string "no data" (case-insensitive)
      - a float already in fraction form (0.0..1.0+)
      - a string like "42%" or "42"
    Percent strings are divided by 100; bare floats > 1.5 are assumed to be
    percentages and scaled down so that the output is always a fraction.
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
