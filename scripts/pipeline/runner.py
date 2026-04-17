from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from . import assemble, conditions, disintegration, items, load, trials, validate, write
from .config import PipelineConfig


@dataclass
class RunResult:
    disintegration: pd.DataFrame
    avg: pd.DataFrame
    full: pd.DataFrame
    written: list[Path]
    dropped_condition_cols: list[str]


def run(
    config: PipelineConfig,
    *,
    suffix: str = "",
    validate_only: bool = False,
    verbose: bool = False,
) -> RunResult | None:
    xl = load.open_workbook(config.input_file)
    _v(verbose, f"Opened {config.input_file} ({len(xl.sheet_names)} sheets)")

    report = validate.validate_input(xl, config)
    if not report.ok():
        raise validate.ValidationError(validate.format_report(report))
    if report.warnings and verbose:
        print(validate.format_report(report))
    _v(verbose, "Validation passed.")

    if validate_only:
        return None

    trials_df = trials.transform_trials(load.read_sheet(xl, config.trials.name))
    items_df = items.transform_items(load.read_sheet(xl, config.items.name))
    disint_df = disintegration.transform_disintegration(
        load.read_sheet(xl, config.disintegration.name)
    )
    _v(verbose, f"Loaded trials={len(trials_df)} items={len(items_df)} disintegration={len(disint_df)}")

    condition_sheets = {
        spec.sheet: load.read_sheet(xl, spec.sheet) for spec in config.operating_conditions
    }

    final = assemble.assemble_disintegration(
        disint_df, items_df, trials_df, config.filters, config.output_columns
    )
    _v(verbose, f"Assembled disintegration rows: {len(final)}")
    if verbose:
        _log_unique(final, "Timepoint")
        _log_unique(final, "Technology")
        _log_unique(final, "Test Method")

    valid_ids = set(trials_df["Trial ID"])
    full, dropped = conditions.build_full_conditions(
        condition_sheets, config.operating_conditions, valid_ids
    )
    surviving_ids = set(final["Trial ID"].dropna().astype(str))
    avg = conditions.build_avg_conditions(
        condition_sheets,
        config.operating_conditions,
        trials_df[trials_df["Trial ID"].isin(surviving_ids)],
    )
    if dropped:
        print("Dropped stray trial columns from operating conditions:")
        for entry in dropped:
            print(f"  - {entry}")

    written = write.write_outputs(final, avg, full, config.outputs, suffix=suffix)
    if verbose:
        for p in written:
            print(f"Wrote {p}")

    return RunResult(
        disintegration=final,
        avg=avg,
        full=full,
        written=written,
        dropped_condition_cols=dropped,
    )


def _v(verbose: bool, msg: str) -> None:
    if verbose:
        print(msg)


def _log_unique(df: pd.DataFrame, col: str) -> None:
    if col not in df.columns:
        return
    uniq = sorted({str(v) for v in df[col].dropna().unique()})
    print(f"  {col}: {uniq}")
