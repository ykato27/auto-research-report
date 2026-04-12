"""Validate generated talent management weekly reports.

The generator is an LLM prompt, so this script guards the delivery workflows
against stale or weakly sourced items before email or Teams posting.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse


BLOCKED_DOMAINS = {
    "crescendo.ai",
    "insightfulpost.com",
    "gitnux.org",
    "worldmetrics.org",
    "wifitalents.com",
}

MIN_TARGET_TOPICS = 25

DATE_LINE_RE = re.compile(r"^（公開日:\s*(\d{4})/(\d{2})/(\d{2})）$")
FILE_DATE_RE = re.compile(r"talent_mgmt_weekly_(\d{8})\.txt$")
TOPIC_COUNT_RE = re.compile(r"今週のトピック数：(\d+)件")
URL_LINE_RE = re.compile(r"^（URL:\s*(https?://[^）\s]+)\s*）$")


@dataclass
class NewsItem:
    line_no: int
    title: str
    published: date | None = None
    url: str | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a talent management weekly report before delivery."
    )
    parser.add_argument("report_file", help="Path to reports/talent_mgmt_weekly_YYYYMMDD.txt")
    return parser.parse_args()


def report_period(path: Path) -> tuple[date, date]:
    match = FILE_DATE_RE.search(path.name)
    if not match:
        raise ValueError(
            "filename must match talent_mgmt_weekly_YYYYMMDD.txt: "
            f"{path.name}"
        )

    report_date = datetime.strptime(match.group(1), "%Y%m%d").date()
    return report_date - timedelta(days=7), report_date


def host_matches_blocked(host: str) -> str | None:
    host = host.lower()
    if host.startswith("www."):
        host = host[4:]

    for blocked in BLOCKED_DOMAINS:
        if host == blocked or host.endswith(f".{blocked}"):
            return blocked
    return None


def dates_in_url(url: str) -> list[date]:
    found: list[date] = []
    patterns = [
        re.compile(r"/(20\d{2})[/-](\d{1,2})[/-](\d{1,2})(?:/|$)"),
        re.compile(r"(20\d{2})(\d{2})(\d{2})"),
    ]

    for pattern in patterns:
        for match in pattern.finditer(url):
            try:
                found.append(
                    date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
                )
            except ValueError:
                continue

    return found


def parse_news_items(content: str) -> list[NewsItem]:
    items: list[NewsItem] = []
    current: NewsItem | None = None
    in_news_section = False

    for line_no, raw_line in enumerate(content.splitlines(), 1):
        line = raw_line.strip()

        section = re.match(r"^【(.+)】$", line)
        if section:
            section_name = section.group(1)
            in_news_section = "Skillnote" not in section_name
            current = None
            continue

        if line.startswith("今週のトピック数"):
            in_news_section = False
            current = None
            continue

        if not in_news_section:
            continue

        if line.startswith("・"):
            if line != "・該当ニュースなし":
                current = NewsItem(line_no=line_no, title=line[1:].strip())
                items.append(current)
            else:
                current = None
            continue

        if current is None:
            continue

        date_match = DATE_LINE_RE.match(line)
        if date_match:
            try:
                current.published = date(
                    int(date_match.group(1)),
                    int(date_match.group(2)),
                    int(date_match.group(3)),
                )
            except ValueError:
                current.published = None
            continue

        url_match = URL_LINE_RE.match(line)
        if url_match:
            current.url = url_match.group(1)
            current = None

    return items


def extract_topic_count(content: str) -> int | None:
    match = TOPIC_COUNT_RE.search(content)
    if not match:
        return None
    return int(match.group(1))


def validate(path: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not path.exists():
        return [f"file not found: {path}"], warnings

    try:
        start_date, end_date = report_period(path)
    except ValueError as exc:
        return [str(exc)], warnings

    content = path.read_text(encoding="utf-8")
    items = parse_news_items(content)
    topic_count = extract_topic_count(content)

    if not items:
        errors.append("no news items found in category sections")

    if topic_count is None:
        errors.append("missing topic count line: 今週のトピック数：N件")
    elif topic_count != len(items):
        errors.append(
            f"topic count mismatch: footer says {topic_count}, "
            f"but found {len(items)} category news items"
        )

    if len(items) < MIN_TARGET_TOPICS:
        warnings.append(
            f"only {len(items)} verified items found; target is {MIN_TARGET_TOPICS}+"
        )

    for item in items:
        location = f"line {item.line_no}"
        if item.published is None:
            errors.append(f"{location}: missing or invalid published date")
        elif not (start_date <= item.published <= end_date):
            errors.append(
                f"{location}: published date {item.published:%Y/%m/%d} "
                f"is outside {start_date:%Y/%m/%d}-{end_date:%Y/%m/%d}"
            )

        if not item.url:
            errors.append(f"{location}: missing URL")
            continue

        parsed = urlparse(item.url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            errors.append(f"{location}: invalid URL: {item.url}")
            continue

        blocked = host_matches_blocked(parsed.netloc)
        if blocked:
            errors.append(f"{location}: blocked domain {blocked}: {item.url}")

        for url_date in dates_in_url(item.url):
            if url_date < start_date:
                errors.append(
                    f"{location}: URL contains stale date {url_date:%Y/%m/%d}: "
                    f"{item.url}"
                )
                break

    return errors, warnings


def main() -> int:
    args = parse_args()
    errors, warnings = validate(Path(args.report_file))

    for warning in warnings:
        print(f"WARN: {warning}")

    if errors:
        print("ERROR: talent management report validation failed")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("OK: talent management report validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
