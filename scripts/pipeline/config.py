from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class SheetSpec:
    name: str
    required_columns: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ConditionSpec:
    sheet: str
    condition: str
    include_in_avg: bool = False
    avg_column: str | None = None
    avg_window_days: int | None = None


@dataclass(frozen=True)
class Filters:
    exclude_material_class_ii: list[str]
    exclude_item_names: list[str]
    outlier_mass_residual_max: float
    excluded_technologies: list[str]
    include_timepoints: list[str] | None = None


@dataclass(frozen=True)
class OutputSpec:
    primary_dir: Path
    dashboard_dir: Path
    disintegration: str
    operating_conditions_avg: str
    operating_conditions_full: str


@dataclass(frozen=True)
class PipelineConfig:
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
        names = [self.trials.name, self.items.name, self.disintegration.name]
        names.extend(c.sheet for c in self.operating_conditions)
        return names


def load_config(config_path: Path, repo_root: Path) -> PipelineConfig:
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
    trials = SheetSpec(sheets["trials"]["name"], sheets["trials"]["required_columns"])
    items = SheetSpec(sheets["items"]["name"], sheets["items"]["required_columns"])
    disintegration = SheetSpec(
        sheets["disintegration"]["name"],
        sheets["disintegration"]["required_columns"],
    )

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
