#!/usr/bin/env python3
"""CFTP disintegration pipeline — single-source entrypoint.

Reads data/CFTP_FullDataSet_Lvl3.xlsx (per pipeline_config.yaml), validates the
input, transforms each domain table, and writes three CSVs to the primary and
dashboard data directories.
"""
from __future__ import annotations

import argparse
import sys
import traceback
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

from pipeline import load_config, run  # noqa: E402
from pipeline.validate import ValidationError  # noqa: E402

DEFAULT_CONFIG = REPO_ROOT / "pipeline_config.yaml"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", type=Path, default=DEFAULT_CONFIG,
                   help="Path to pipeline_config.yaml (default: repo root).")
    p.add_argument("--input", type=Path, default=None,
                   help="Override input_file from config.")
    p.add_argument("--output-dir", type=Path, default=None,
                   help="Override primary output directory from config.")
    p.add_argument("--dashboard-dir", type=Path, default=None,
                   help="Override dashboard output directory from config.")
    p.add_argument("--suffix", default="",
                   help="Optional suffix appended to output filenames (e.g. _test).")
    p.add_argument("--validate-only", action="store_true",
                   help="Run input validation and exit without writing outputs.")
    p.add_argument("--verbose", "-v", action="store_true",
                   help="Log per-stage row counts and distinct categorical values.")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        config = load_config(args.config, REPO_ROOT)
    except FileNotFoundError as exc:
        print(f"Config file not found: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to load config: {exc}", file=sys.stderr)
        if args.verbose:
            traceback.print_exc()
        return 2

    config = _apply_overrides(config, args)

    try:
        run(
            config,
            suffix=args.suffix,
            validate_only=args.validate_only,
            verbose=args.verbose,
        )
    except ValidationError as exc:
        print("Validation failed:", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 1
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"Pipeline failed: {exc}", file=sys.stderr)
        if args.verbose:
            traceback.print_exc()
        return 2

    if args.validate_only:
        print("Validation-only run complete. No outputs written.")
    else:
        print("Pipeline complete.")
    return 0


def _apply_overrides(config, args):
    from dataclasses import replace

    outputs = config.outputs
    if args.output_dir is not None or args.dashboard_dir is not None:
        outputs = replace(
            outputs,
            primary_dir=(args.output_dir or outputs.primary_dir).resolve(),
            dashboard_dir=(args.dashboard_dir or outputs.dashboard_dir).resolve(),
        )
    input_file = args.input.resolve() if args.input else config.input_file
    return replace(config, input_file=input_file, outputs=outputs)


if __name__ == "__main__":
    sys.exit(main())
