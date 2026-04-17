from __future__ import annotations

import pandas as pd

from .config import Filters


def assemble_disintegration(
    disintegration: pd.DataFrame,
    items: pd.DataFrame,
    trials: pd.DataFrame,
    filters: Filters,
    output_columns: list[str],
) -> pd.DataFrame:
    df = disintegration.merge(items, on="Item ID", how="inner")
    df = df.merge(
        trials[["Trial ID", "Test Method", "Technology"]],
        on="Trial ID",
        how="inner",
    )

    if filters.exclude_material_class_ii:
        df = df[~df["Material Class II"].isin(filters.exclude_material_class_ii)]
    if filters.exclude_item_names:
        df = df[~df["Item Name"].isin(filters.exclude_item_names)]
    if filters.excluded_technologies:
        df = df[~df["Technology"].isin(filters.excluded_technologies)]
    if filters.include_timepoints:
        df = df[df["Timepoint"].isin(filters.include_timepoints)]
    if filters.outlier_mass_residual_max is not None:
        mass = df["% Residuals (Mass)"]
        df = df[mass.isna() | (mass < filters.outlier_mass_residual_max)]

    for col in output_columns:
        if col not in df.columns:
            df[col] = pd.NA
    return df[output_columns].reset_index(drop=True)
