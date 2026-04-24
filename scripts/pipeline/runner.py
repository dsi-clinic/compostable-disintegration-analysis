"""Pipeline orchestrator: reads the workbook, transforms each sheet, assembles
the final tables, and writes the CSV outputs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from . import assemble, conditions, load, transforms, validate, write
from .config import PipelineConfig


@dataclass
class RunResult:
    """Outputs of a successful pipeline run.

    ``dropped_condition_cols`` lists operating-condition columns that were
    dropped because their header did not match a known Trial ID.
    """

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
    """Execute the pipeline end-to-end.

    Validates the input workbook, transforms the trials/items/disintegration
    sheets, assembles filtered disintegration rows, builds the full and
    per-trial-average operating-conditions tables, and writes CSVs. Returns
    ``None`` when ``validate_only`` is true. Raises
    :class:`validate.ValidationError` if validation fails. ``suffix`` is
    appended to each output filename stem.
    """
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

    trials_df = transforms.apply_sheet_spec(
        load.read_sheet(xl, config.trials.name), config.trials
    )
    items_df = transforms.transform_items(
        load.read_sheet(xl, config.items.name), config.items
    )
    disint_df = transforms.transform_disintegration(
        load.read_sheet(xl, config.disintegration.name), config.disintegration
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
    """Print ``msg`` when ``verbose`` is true."""
    if verbose:
        print(msg)


def _log_unique(df: pd.DataFrame, col: str) -> None:
    """Print the sorted unique values of ``col`` if it exists in ``df``."""
    if col not in df.columns:
        return
    uniq = sorted({str(v) for v in df[col].dropna().unique()})
    print(f"  {col}: {uniq}")
