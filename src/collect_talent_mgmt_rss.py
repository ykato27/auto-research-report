"""Collect daily talent management RSS candidates into JSONL."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from talent_mgmt_rss import collect_all, load_config, read_jsonl, write_jsonl, write_status


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect trusted RSS items for talent/skills monitoring."
    )
    parser.add_argument("--config", default="feeds/talent_mgmt.yaml")
    parser.add_argument("--store", default="data/talent_mgmt_items.jsonl")
    parser.add_argument("--status", default="data/talent_mgmt_source_status.json")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Collect and summarize without writing JSONL/status files.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    existing_rows = read_jsonl(args.store)
    merged_rows, status = collect_all(config, existing_rows)

    print(json.dumps(status, ensure_ascii=False, indent=2, sort_keys=True))

    if args.dry_run:
        print("INFO: dry-run mode; no files written.")
        return

    Path(args.store).parent.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.store, merged_rows)
    write_status(args.status, status)


if __name__ == "__main__":
    main()
