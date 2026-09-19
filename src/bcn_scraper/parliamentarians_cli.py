"""Refresh existing parliamentary Parquet tables; run explicitly with python -m."""
from __future__ import annotations

import argparse
import os
from datetime import datetime, timezone
from pathlib import Path
import shutil
import tempfile
from typing import Optional, Sequence

import pandas as pd

from .parliamentary_data import (
    CachedRDFJsonFetcher,
    _militancy_options,
    debug_parliamentarian_data_errors,
    missing_parliamentarian_data_mask,
)


def _write_parquet(result, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{destination.stem}-", suffix=".parquet",
                                             dir=destination.parent)
    os.close(descriptor)
    try:
        result.to_parquet(temporary, index=False)
        if destination.exists():
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
            backup = destination.with_name(f"{destination.name}.{stamp}.bak")
            shutil.copy2(destination, backup)
            print(f"Backup: {backup}")
        os.replace(temporary, destination)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", nargs="+", required=True, type=Path,
                        help="Existing Parquet tables with a person_href column")
    parser.add_argument("--date", default="current", metavar="YYYY-MM-DD|all|current|discussions",
                        help="Date, all history, current affiliation (default), or each discussion date")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--max-attempts", type=int, default=2)
    parser.add_argument("--backoff-seconds", type=float, default=2.0)
    parser.add_argument("--only-incomplete", action="store_true",
                        help="For scalar dates, retry only incomplete rows; discussions always reuses saved data")
    parser.add_argument("--limit", type=int, help="Maximum total rows to process; requires --output-dir")
    parser.add_argument("--output-dir", type=Path,
                        help="Write separate files named <source-parent>_<source-name>")
    parser.add_argument("--no-progress", action="store_true")
    parser.add_argument("--cache-dir", type=Path, default=Path(".cache/bcn-scraper/rdf"),
                        help="Persistent RDF cache for --date discussions")
    parser.add_argument("--offline", action="store_true",
                        help="With --date discussions, resolve only saved histories without requests")
    args = parser.parse_args(argv)
    try:
        if args.date != "discussions":
            _militancy_options(args.date, False, False)
    except (TypeError, ValueError) as exc:
        parser.error(str(exc))
    if args.timeout <= 0 or args.max_attempts <= 0 or args.backoff_seconds < 0:
        parser.error("timeout and max-attempts must be positive; backoff-seconds must be nonnegative")
    if args.limit is not None and (args.limit <= 0 or args.output_dir is None):
        parser.error("--limit must be positive and requires --output-dir to preserve full tables")

    if args.date == "discussions":
        from .discussion_affiliations import run_discussions
        return run_discussions(args, parser, _write_parquet)
    if args.offline:
        parser.error("--offline requires --date discussions")

    sources = list(dict.fromkeys(path.resolve() for path in args.input))
    tables = []
    destinations = set()
    for source in sources:
        if not source.is_file():
            parser.error(f"Input file does not exist: {source}")
        frame = pd.read_parquet(source)
        if "person_href" not in frame:
            parser.error(f"Missing person_href column: {source}")
        destination = (args.output_dir / f"{source.parent.name}_{source.name}"
                       if args.output_dir is not None else source)
        destination = destination.resolve()
        if (destination in destinations or
                (destination in sources and (args.limit is not None or destination != source))):
            parser.error(f"Output would collide with another table: {destination}")
        destinations.add(destination)
        tables.append((source, destination, frame))

    loader = CachedRDFJsonFetcher(timeout=args.timeout, max_attempts=args.max_attempts,
                                  backoff_seconds=args.backoff_seconds)
    remaining = args.limit
    for source, destination, frame in tables:
        if remaining is not None:
            if remaining == 0:
                break
            frame = frame.head(remaining).copy()
            remaining -= len(frame)
        result = debug_parliamentarian_data_errors(
            frame.reset_index(drop=True), date=args.date, fetcher=loader,
            force=not args.only_incomplete, show_progress=not args.no_progress,
        )
        _write_parquet(result, destination)
        statuses = result["data_status"].value_counts().to_dict() if "data_status" in result else {}
        print(f"{destination}: {len(result)} rows; {statuses}")
        incomplete = int(missing_parliamentarian_data_mask(result, date=args.date).sum())
        if incomplete:
            print(f"Rows with missing or incomplete data: {incomplete}; inspect before analysis")
        if "militancy_at_date_status" in result:
            historical = result["militancy_at_date_status"].dropna().value_counts().to_dict()
            if historical:
                print(f"Historical resolution: {historical}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
