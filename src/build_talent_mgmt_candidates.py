"""Build a weekly candidate Markdown file from stored talent management RSS data."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

from talent_mgmt_rss import JST, parse_iso_datetime, read_jsonl


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render recent talent management RSS items for later AI reporting."
    )
    parser.add_argument("--store", default="data/talent_mgmt_items.jsonl")
    parser.add_argument("--since-days", type=int, default=7)
    parser.add_argument("--limit", type=int, default=80)
    parser.add_argument("--output", default="")
    return parser.parse_args()


def recent_rows(rows: list[dict], since_days: int) -> list[dict]:
    cutoff = datetime.now(timezone.utc).astimezone(JST) - timedelta(days=since_days)
    filtered = []
    for row in rows:
        published = parse_iso_datetime(row.get("published_at"))
        if published and published >= cutoff:
            filtered.append(row)

    filtered.sort(
        key=lambda row: (
            int(row.get("score", 0)),
            parse_iso_datetime(row.get("published_at")) or datetime.min.replace(tzinfo=JST),
        ),
        reverse=True,
    )
    return filtered


def render_markdown(rows: list[dict], since_days: int) -> str:
    today = datetime.now(JST).strftime("%Y/%m/%d")
    lines = [
        f"# タレントマネジメントRSS候補（直近{since_days}日 / {today}生成）",
        "",
        "このファイルはRSS/Google News RSSから取得した候補一覧です。",
        "週次レポート作成時は、score、source、published_at、matched_keywordsを参考に重要度を判断してください。",
        "",
        f"候補件数: {len(rows)}件",
        "",
    ]

    for index, row in enumerate(rows, start=1):
        keywords = ", ".join(row.get("matched_keywords", [])[:8])
        summary = row.get("summary", "")
        if len(summary) > 500:
            summary = summary[:497] + "..."

        lines.extend(
            [
                f"## {index}. {row.get('title', '')}",
                "",
                f"- score: {row.get('score', 0)}",
                f"- category: {row.get('category_guess', 'uncategorized')}",
                f"- source: {row.get('source_name', '')}",
                f"- published_at: {row.get('published_at', '')}",
                f"- matched_keywords: {keywords}",
                f"- url: {row.get('canonical_url', '')}",
                "",
                summary,
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def default_output_path() -> Path:
    today = datetime.now(JST).strftime("%Y%m%d")
    return Path(f"reports/talent_mgmt_candidates_{today}.md")


def main() -> None:
    args = parse_args()
    rows = recent_rows(read_jsonl(args.store), args.since_days)[: args.limit]
    markdown = render_markdown(rows, args.since_days)
    output_path = Path(args.output) if args.output else default_output_path()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8", newline="\n")
    print(f"OK: wrote {len(rows)} candidates to {output_path}")


if __name__ == "__main__":
    main()
