#!/usr/bin/env python3
"""Write a compact, offline JSON summary of complete Milestone 2 predictions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from alphapulldown_dnaaf_screen.milestone2_results import (
    ResultValidationError,
    summarize_results_root,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    try:
        summaries = summarize_results_root(args.results_root)
    except ResultValidationError as error:
        parser.error(str(error))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps([summary.as_dict() for summary in summaries], indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
