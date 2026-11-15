"""Command-line interface for inflate-check.

Usage:
    python -m inflatecheck.cli original.md summary.md [--format text|json]
        [--threshold PCT] [--min-similarity 0.25]

Exit codes:
    0  no inflation above the threshold
    1  inflation rate exceeds --threshold (default: any inflation)
    2  usage / input error
"""

import argparse
import sys

from . import __version__
from .classify import audit
from .report import render_json, render_text


def build_parser():
    parser = argparse.ArgumentParser(
        prog="inflate-check",
        description=(
            "Detect constraint inflation in a compacted agent summary: "
            "preferences turned into requirements, one-offs into standing "
            "rules, narrow scopes into 'all', replaced values kept as current."
        ),
    )
    parser.add_argument("original", help="file with the original instructions")
    parser.add_argument("summary", help="file with the compacted summary")
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="output format (default: text)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.0,
        help="allowed inflation rate in percent; exit 1 above it (default: 0)",
    )
    parser.add_argument(
        "--min-similarity",
        type=float,
        default=0.25,
        help="token-Jaccard threshold for aligning items (default: 0.25)",
    )
    parser.add_argument(
        "--version", action="version", version="inflate-check %s" % __version__
    )
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        with open(args.original, encoding="utf-8") as fh:
            original_text = fh.read()
        with open(args.summary, encoding="utf-8") as fh:
            summary_text = fh.read()
    except OSError as exc:
        print("inflate-check: %s" % exc, file=sys.stderr)
        return 2
    if not original_text.strip():
        print("inflate-check: original file is empty", file=sys.stderr)
        return 2
    if not summary_text.strip():
        print("inflate-check: summary file is empty", file=sys.stderr)
        return 2

    report = audit(original_text, summary_text, min_similarity=args.min_similarity)
    if args.format == "json":
        print(render_json(report, args.threshold), end="")
    else:
        print(render_text(report, args.threshold), end="")
    return 1 if report["inflation_rate_pct"] > args.threshold else 0


if __name__ == "__main__":
    sys.exit(main())
