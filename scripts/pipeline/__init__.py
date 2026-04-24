"""Pipeline package for transforming the compost-trial workbook into the CSV
outputs consumed by the dashboard.

Public entry points: :func:`load_config` to parse a YAML pipeline config, and
:func:`run` to execute the full pipeline against an input workbook.
"""

from .config import PipelineConfig, load_config
from .runner import run

__all__ = ["PipelineConfig", "load_config", "run"]
