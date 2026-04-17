from __future__ import annotations

import pandas as pd


ITEM_COLS = [
    "Item ID",
    "Item Type",
    "Brand for Display",
    "Item Name",
    "Material Class I",
    "Material Class II",
    "Material Class III",
]


def transform_items(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw[ITEM_COLS].copy()
    if "Item Description Refined" in raw.columns:
        df["Item Description Refined"] = raw["Item Description Refined"]
    else:
        df["Item Description Refined"] = pd.NA

    df = df.rename(
        columns={
            "Item Type": "Item Format",
            "Brand for Display": "Item Brand",
        }
    )
    df = df.dropna(subset=["Item ID"]).drop_duplicates(subset=["Item ID"])
    df["Item ID"] = df["Item ID"].astype(str)
    df["Item Brand"] = df["Item Brand"].astype(str)
    df["Item Format"] = df["Item Format"].astype(str).str.strip().str.title()
    return df
