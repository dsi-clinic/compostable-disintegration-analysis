"""Build the full and per-trial-average operating-conditions output tables."""

from __future__ import annotations

import pandas as pd

from .config import ConditionSpec

META_COLS = ["Operating Condition", "Time Unit", "Time Step"]


def build_full_conditions(
    sheets: dict[str, pd.DataFrame],
    specs: list[ConditionSpec],
    valid_trial_ids: set[str],
) -> tuple[pd.DataFrame, list[str]]:
    """Concatenate all operating-conditions sheets into one long table.

    Returns (df, dropped_columns_log). Columns with headers that aren't real
    trial IDs (e.g. typos like "CAPS009-01") are dropped and logged.
    """
    dropped_log: list[str] = []
    frames: list[pd.DataFrame] = []

    for spec in specs:
        df = sheets[spec.sheet].copy()
        trial_cols = [c for c in df.columns if c not in META_COLS]
        stray = [c for c in trial_cols if str(c) not in valid_trial_ids]
        if stray:
            dropped_log.append(f"{spec.sheet}: dropped {stray}")
            df = df.drop(columns=stray)
        # Overwrite the condition label from config to normalize (source is
        # populated but we don't want to trust any typos there either).
        df["Operating Condition"] = spec.condition
        frames.append(df)

    full = pd.concat(frames, axis=0, ignore_index=True)
    # Put metadata columns first; trial columns after in consistent order.
    trial_cols = [c for c in full.columns if c not in META_COLS]
    full = full[META_COLS + trial_cols]
    return full, dropped_log


def build_avg_conditions(
    sheets: dict[str, pd.DataFrame],
    specs: list[ConditionSpec],
    trials: pd.DataFrame,
) -> pd.DataFrame:
    """Assemble per-trial average temperature/moisture + Trial Duration.

    Output columns: Trial ID, Trial Duration, <avg columns for each spec where
    include_in_avg=True>.
    """
    base = trials[["Trial ID", "Trial Duration"]].copy()
    base = base.set_index("Trial ID")

    for spec in specs:
        if not spec.include_in_avg:
            continue
        df = sheets[spec.sheet]
        trial_cols = [c for c in df.columns if c not in META_COLS and str(c) in base.index]
        numeric = df[trial_cols].apply(pd.to_numeric, errors="coerce")
        if spec.avg_window_days is not None:
            numeric = numeric.iloc[: spec.avg_window_days]
        avg = numeric.mean(axis=0)
        avg.index = avg.index.astype(str)
        base[spec.avg_column] = avg

    base = base.reset_index()
    return base
