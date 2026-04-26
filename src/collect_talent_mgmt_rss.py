"""Collect daily talent management RSS candidates into monthly JSONL partitions."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from talent_mgmt_rss import JST, collect_all, load_config, read_jsonl, write_jsonl, write_status


def monthly_store_path(store_dir: str | Path, now: datetime) -> Path:
    """Return data/items/YYYYMM.jsonl for the given datetime."""
    month = now.astimezone(JST).strftime("%Y%m")
    return Path(store_dir) / f"{month}.jsonl"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect trusted RSS items for talent/skills monitoring."
    )
    parser.add_argument("--config", default="feeds/talent_mgmt.yaml")
    parser.add_argument(
        "--store-dir",
        default="data/items",
        help="Directory for monthly JSONL partitions (YYYYMM.jsonl).",
    )
    parser.add_argument("--status", default="data/talent_mgmt_source_status.json")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Collect and summarize without writing files.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    now = datetime.now(timezone.utc)
    config = load_config(args.config)

    store_path = monthly_store_path(args.store_dir, now)
    existing_rows = read_jsonl(store_path)
    merged_rows, status = collect_all(config, existing_rows, now=now)

    status["store_path"] = str(store_path)
    print(json.dumps(status, ensure_ascii=False, indent=2, sort_keys=True))

    if args.dry_run:
        print("INFO: dry-run mode; no files written.")
        return

    store_path.parent.mkdir(parents=True, exist_ok=True)
    write_jsonl(store_path, merged_rows)
    write_status(args.status, status)


if __name__ == "__main__":
    main()
