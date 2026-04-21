"""Typed configuration model for the pipeline and the YAML loader."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class SheetSpec:
    """One input worksheet and how to reshape it into a pipeline table.

    ``required_columns`` are the Excel-native column names that must be
    present; validation fails if any are missing. ``optional_columns`` are
    carried through when present and filled with NA when absent.

    ``rename`` maps Excel-native names to the post-transform names the
    pipeline (and the dashboard) use downstream. ``id_columns`` and
    ``dedupe_on`` use post-rename names: every ``id_columns`` column is
    dropna'd and str-cast; ``dedupe_on`` (if set) selects the column used
    for row deduplication.
    """

    name: str
    required_columns: list[str] = field(default_factory=list)
    optional_columns: list[str] = field(default_factory=list)
    rename: dict[str, str] = field(default_factory=dict)
    id_columns: list[str] = field(default_factory=list)
    dedupe_on: str | None = None


@dataclass(frozen=True)
class ConditionSpec:
    """One operating-condition sheet (e.g. temperature, moisture)."""

    sheet: str
    condition: str
    include_in_avg: bool = False
    avg_column: str | None = None
    avg_window_days: int | None = None


@dataclass(frozen=True)
class Filters:
    """Row-level filters applied while assembling the disintegration table."""

    exclude_material_class_ii: list[str]
    exclude_item_names: list[str]
    outlier_mass_residual_max: float
    excluded_technologies: list[str]
    include_timepoints: list[str] | None = None


@dataclass(frozen=True)
class OutputSpec:
    """Destination directories and filenames for the three CSV outputs."""

    primary_dir: Path
    dashboard_dir: Path
    disintegration: str
    operating_conditions_avg: str
    operating_conditions_full: str


@dataclass(frozen=True)
class PipelineConfig:
    """Fully resolved pipeline configuration."""

    input_file: Path
    outputs: OutputSpec
    trials: SheetSpec
    items: SheetSpec
    disintegration: SheetSpec
    operating_conditions: list[ConditionSpec]
    filters: Filters
    output_columns: list[str]

    @property
    def all_sheet_names(self) -> list[str]:
        """Every worksheet name the pipeline expects to read."""
        names = [self.trials.name, self.items.name, self.disintegration.name]
        names.extend(c.sheet for c in self.operating_conditions)
        return names


def load_config(config_path: Path, repo_root: Path) -> PipelineConfig:
    """Parse a pipeline YAML file into a :class:`PipelineConfig`.

    Paths in the YAML are resolved relative to ``repo_root``.
    """
    with config_path.open("r") as f:
        raw: dict[str, Any] = yaml.safe_load(f)

    outputs_raw = raw["outputs"]
    filenames = outputs_raw["filenames"]
    outputs = OutputSpec(
        primary_dir=(repo_root / outputs_raw["primary_dir"]).resolve(),
        dashboard_dir=(repo_root / outputs_raw["dashboard_dir"]).resolve(),
        disintegration=filenames["disintegration"],
        operating_conditions_avg=filenames["operating_conditions_avg"],
        operating_conditions_full=filenames["operating_conditions_full"],
    )

    sheets = raw["sheets"]
    trials = _sheet_spec(sheets["trials"])
    items = _sheet_spec(sheets["items"])
    disintegration = _sheet_spec(sheets["disintegration"])

    conditions = [ConditionSpec(**c) for c in raw["operating_conditions"]]

    filters = Filters(**raw["filters"])

    return PipelineConfig(
        input_file=(repo_root / raw["input_file"]).resolve(),
        outputs=outputs,
        trials=trials,
        items=items,
        disintegration=disintegration,
        operating_conditions=conditions,
        filters=filters,
        output_columns=raw["output_columns"],
    )


def _sheet_spec(raw: dict[str, Any]) -> SheetSpec:
    return SheetSpec(
        name=raw["name"],
        required_columns=raw.get("required_columns", []),
        optional_columns=raw.get("optional_columns", []),
        rename=raw.get("rename", {}),
        id_columns=raw.get("id_columns", []),
        dedupe_on=raw.get("dedupe_on"),
    )
