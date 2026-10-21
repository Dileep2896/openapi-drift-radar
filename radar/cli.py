"""``python -m radar.cli --before a.yaml --after b.yaml --docs ./docs [--format md|json]``"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from radar.drafter import get_drafter
from radar.models import Severity
from radar.report import analyze, load_docs, to_markdown
from radar.spec_loader import SpecError


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="drift-radar", description="Find docs lines made stale by an OpenAPI change.")
    p.add_argument("--before", required=True, type=Path, help="OpenAPI spec on the base branch")
    p.add_argument("--after", required=True, type=Path, help="OpenAPI spec on the PR branch")
    p.add_argument("--docs", required=True, type=Path, help="Folder of .md/.mdx docs pages")
    p.add_argument("--format", choices=["md", "json"], default="md")
    p.add_argument("--fail-on-breaking", action="store_true", help="Exit 1 when a breaking change hits the docs")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        before = args.before.read_text(encoding="utf-8")
        after = args.after.read_text(encoding="utf-8")
        docs = load_docs(args.docs)
        report = analyze(before, after, docs, get_drafter(os.environ))
    except (OSError, SpecError) as exc:
        sys.stderr.write(f"drift-radar error: {exc}\n")
        return 2
    sys.stdout.write(report.model_dump_json(indent=2) if args.format == "json" else to_markdown(report))
    sys.stdout.write("\n")
    if args.fail_on_breaking and any(i.severity is Severity.BREAKING for i in report.impacts):
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
