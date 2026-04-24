#!/usr/bin/env python3
"""CFTP disintegration pipeline — single-source entrypoint."""
from __future__ import annotations

import sys
import traceback
from dataclasses import replace
from pathlib import Path

import click
from pipeline import load_config, run
from pipeline.config import PipelineConfig
from pipeline.validate import ValidationError

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = REPO_ROOT / "pipeline_config.yaml"

PathArg = click.Path(dir_okay=False, path_type=Path)
DirArg = click.Path(file_okay=False, path_type=Path)


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "--config", "config_path", type=PathArg,
    default=DEFAULT_CONFIG, show_default=True,
    help="Path to pipeline_config.yaml.",
)
@click.option(
    "--input", "input_path", type=PathArg, default=None,
    help="Override input_file from config.",
)
@click.option(
    "--output-dir", type=DirArg, default=None,
    help="Override primary output directory from config.",
)
@click.option(
    "--dashboard-dir", type=DirArg, default=None,
    help="Override dashboard output directory from config.",
)
@click.option(
    "--suffix", default="",
    help="Suffix appended to output filenames (e.g. _test).",
)
@click.option(
    "--validate-only", is_flag=True,
    help="Run input validation and exit without writing outputs.",
)
@click.option(
    "--verbose", "-v", is_flag=True,
    help="Log per-stage row counts and distinct categorical values.",
)
def main(
    config_path: Path,
    input_path: Path | None,
    output_dir: Path | None,
    dashboard_dir: Path | None,
    suffix: str,
    validate_only: bool,
    verbose: bool,
) -> None:
    """Run the CFTP disintegration pipeline against the configured workbook.

    Validates the input, transforms each domain table, and writes three CSVs
    to the primary and dashboard output directories declared in
    pipeline_config.yaml.
    """
    try:
        config = load_config(config_path.expanduser(), REPO_ROOT)
    except FileNotFoundError as exc:
        raise click.ClickException(f"Config file not found: {exc}") from exc
    except Exception as exc:  # noqa: BLE001 — CLI boundary
        if verbose:
            traceback.print_exc()
        raise click.ClickException(f"Failed to load config: {exc}") from exc

    config = _apply_overrides(config, input_path, output_dir, dashboard_dir)

    try:
        run(config, suffix=suffix, validate_only=validate_only, verbose=verbose)
    except ValidationError as exc:
        raise click.ClickException(f"Validation failed:\n{exc}") from exc
    except FileNotFoundError as exc:
        raise click.ClickException(str(exc)) from exc
    except KeyboardInterrupt:
        click.echo("Interrupted.", err=True)
        sys.exit(130)
    except Exception as exc:  # noqa: BLE001 — CLI boundary; map to exit 2
        click.echo(f"Pipeline failed: {exc}", err=True)
        if verbose:
            traceback.print_exc()
        sys.exit(2)

    click.echo(
        "Validation-only run complete. No outputs written."
        if validate_only
        else "Pipeline complete."
    )


def _apply_overrides(
    config: PipelineConfig,
    input_path: Path | None,
    output_dir: Path | None,
    dashboard_dir: Path | None,
) -> PipelineConfig:
    """Apply CLI path overrides on top of a loaded config."""
    outputs = replace(
        config.outputs,
        primary_dir=(
            output_dir.expanduser().resolve()
            if output_dir
            else config.outputs.primary_dir
        ),
        dashboard_dir=(
            dashboard_dir.expanduser().resolve()
            if dashboard_dir
            else config.outputs.dashboard_dir
        ),
    )
    input_file = (
        input_path.expanduser().resolve() if input_path else config.input_file
    )
    return replace(config, input_file=input_file, outputs=outputs)


if __name__ == "__main__":
    main()
