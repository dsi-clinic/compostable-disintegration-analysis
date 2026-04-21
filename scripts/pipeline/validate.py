"""Pre-run validation of the input workbook against the pipeline config."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from .config import PipelineConfig
from .load import read_sheet

CONDITIONS_META_COLS = ("Operating Condition", "Time Unit", "Time Step")


class ValidationError(Exception):
    """Raised when input validation produces any blocking errors."""


@dataclass
class ValidationReport:
    """Accumulator for validation errors (blocking) and warnings (informational)."""

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def error(self, msg: str) -> None:
        """Record a blocking error message."""
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        """Record a non-blocking warning message."""
        self.warnings.append(msg)

    def ok(self) -> bool:
        """Return True when there are no blocking errors."""
        return not self.errors


def validate_input(xl: pd.ExcelFile, config: PipelineConfig) -> ValidationReport:
    """Check that ``xl`` has the sheets, columns, and foreign keys ``config`` expects.

    Returns a :class:`ValidationReport`. Missing required columns or sheets
    are errors; operating-condition columns with unknown Trial IDs are
    warnings (they will be dropped at assembly time).
    """
    report = ValidationReport()

    available = set(xl.sheet_names)
    for expected in config.all_sheet_names:
        if expected not in available:
            report.error(f"Missing sheet: {expected!r}")

    if report.errors:
        return report

    _check_columns(xl, config.trials.name, config.trials.required_columns, report)
    _check_columns(xl, config.items.name, config.items.required_columns, report)
    _check_columns(
        xl,
        config.disintegration.name,
        config.disintegration.required_columns,
        report,
    )

    trial_ids: set[str] = set()
    item_ids: set[str] = set()
    if report.ok():
        trials = read_sheet(xl, config.trials.name)
        items = read_sheet(xl, config.items.name)
        disintegration = read_sheet(xl, config.disintegration.name)

        trial_ids = set(trials["Public Trial ID"].dropna().astype(str))
        item_ids = set(items["Item ID"].dropna().astype(str))

        _check_foreign_key(
            disintegration, "Public Trial ID", trial_ids, "TrialDetails", report
        )
        _check_foreign_key(
            disintegration, "Item ID", item_ids, "ItemInventory", report
        )

    for cond in config.operating_conditions:
        df = read_sheet(xl, cond.sheet)
        missing = [c for c in CONDITIONS_META_COLS if c not in df.columns]
        if missing:
            report.error(
                f"Sheet {cond.sheet!r} missing metadata columns: {missing}"
            )
            continue
        trial_cols = [c for c in df.columns if c not in CONDITIONS_META_COLS]
        stray = [c for c in trial_cols if str(c) not in trial_ids]
        if stray and trial_ids:
            report.warn(
                f"Sheet {cond.sheet!r} has trial columns not in TrialDetails "
                f"(will be dropped): {stray}"
            )

    return report


def _check_columns(
    xl: pd.ExcelFile,
    sheet: str,
    required: list[str],
    report: ValidationReport,
) -> None:
    """Record an error in ``report`` for each required column missing from ``sheet``."""
    df = read_sheet(xl, sheet)
    present = set(df.columns)
    for col in required:
        if col not in present:
            report.error(f"Sheet {sheet!r} missing column: {col!r}")


def _check_foreign_key(
    df: pd.DataFrame,
    col: str,
    valid: set[str],
    target: str,
    report: ValidationReport,
) -> None:
    """Warn if values in ``df[col]`` are not present in ``valid``.

    ``target`` names the referenced sheet and is used only in the warning text.
    """
    values = set(df[col].dropna().astype(str))
    missing = values - valid
    if missing:
        sample = sorted(missing)[:10]
        report.warn(
            f"DisintegrationData.{col!r} has {len(missing)} value(s) "
            f"not found in {target} (rows will be dropped). Sample: {sample}"
        )


def format_report(report: ValidationReport) -> str:
    """Render ``report`` as a multi-line human-readable string."""
    lines: list[str] = []
    if report.warnings:
        lines.append("Warnings:")
        lines.extend(f"  - {w}" for w in report.warnings)
    if report.errors:
        lines.append("Errors:")
        lines.extend(f"  - {e}" for e in report.errors)
    return "\n".join(lines)
