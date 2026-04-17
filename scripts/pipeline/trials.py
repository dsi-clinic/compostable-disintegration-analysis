from __future__ import annotations

import pandas as pd


def transform_trials(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw[
        [
            "Public Trial ID",
            "Test Method",
            "Detailed Compost Technology",
            "Display Compost Technology",
            "Midpoint Duration",
            "Final Duration",
            "Annual Tonnage (tpy)",
        ]
    ].copy()
    df = df.rename(
        columns={
            "Public Trial ID": "Trial ID",
            "Display Compost Technology": "Technology",
            "Final Duration": "Trial Duration",
        }
    )
    df = df.dropna(subset=["Trial ID"]).drop_duplicates(subset=["Trial ID"])
    df["Trial ID"] = df["Trial ID"].astype(str)
    return df
