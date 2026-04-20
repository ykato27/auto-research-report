"""RSS collection helpers for talent management monitoring."""

from __future__ import annotations

import hashlib
import html
import json
import re
import calendar
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import feedparser
import yaml

JST = timezone(timedelta(hours=9))
TRACKING_PARAM_PREFIXES = ("utm_",)
TRACKING_PARAMS = {
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
    "igshid",
    "ref",
    "ref_src",
}


@dataclass
class SourceResult:
    name: str
    url: str
    ok: bool
    item_count: int = 0
    new_count: int = 0
    error: str | None = None


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def load_config(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def normalize_url(url: str) -> str:
    if not url:
        return ""

    parts = urlsplit(url.strip())
    netloc = parts.netloc.lower()
    query = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        lower_key = key.lower()
        if lower_key in TRACKING_PARAMS:
            continue
        if any(lower_key.startswith(prefix) for prefix in TRACKING_PARAM_PREFIXES):
            continue
        query.append((key, value))

    path = parts.path or "/"
    return urlunsplit((parts.scheme.lower(), netloc, path, urlencode(query), ""))


def stable_item_id(source_name: str, entry: Any, canonical_url: str) -> str:
    raw_id = entry.get("id") or entry.get("guid") or canonical_url
    if not raw_id:
        raw_id = "|".join(
            [
                source_name,
                entry.get("title", ""),
                entry.get("published", "") or entry.get("updated", ""),
            ]
        )
    return hashlib.sha256(raw_id.encode("utf-8")).hexdigest()[:20]


def parse_entry_datetime(entry: Any) -> tuple[datetime | None, str]:
    for field, confidence in (
        ("published_parsed", "published"),
        ("updated_parsed", "updated"),
    ):
        parsed = entry.get(field)
        if parsed:
            dt = datetime.fromtimestamp(calendar.timegm(parsed), timezone.utc)
            return dt.astimezone(JST), confidence
    return None, "missing"


def strip_markup(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value or "")
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def entry_text(entry: Any) -> str:
    parts = [entry.get("title", ""), entry.get("summary", "")]
    for content in entry.get("content", []) or []:
        if isinstance(content, dict):
            parts.append(content.get("value", ""))
    return strip_markup(" ".join(parts))


def entry_tags(entry: Any) -> list[str]:
    tags = []
    for tag in entry.get("tags", []) or []:
        if isinstance(tag, dict) and tag.get("term"):
            tags.append(str(tag["term"]))
    return tags


def keyword_hits(text: str, keywords: list[str]) -> list[str]:
    lowered = text.lower()
    return [keyword for keyword in keywords if keyword.lower() in lowered]


def category_guess(text: str, categories: dict[str, Any]) -> str:
    best_category = "uncategorized"
    best_count = 0
    for category, spec in categories.items():
        hits = keyword_hits(text, spec.get("keywords", []))
        if len(hits) > best_count:
            best_category = category
            best_count = len(hits)
    return best_category


def score_item(
    source: dict[str, Any],
    matched_keywords: list[str],
    category: str,
    published_at: datetime,
    fetched_at: datetime,
) -> tuple[int, list[str]]:
    score = int(source.get("weight", 1))
    reasons = [f"source_weight={score}"]

    if matched_keywords:
        keyword_score = min(len(matched_keywords) * 3, 18)
        score += keyword_score
        reasons.append(f"keyword_hits={len(matched_keywords)}")

    if category != "uncategorized":
        score += 4
        reasons.append(f"category={category}")

    age_days = max((fetched_at.astimezone(JST) - published_at).days, 0)
    if age_days <= 1:
        score += 5
        reasons.append("recency<=1d")
    elif age_days <= 3:
        score += 3
        reasons.append("recency<=3d")
    elif age_days <= 7:
        score += 1
        reasons.append("recency<=7d")

    return score, reasons


def should_keep_item(
    text: str,
    include_keywords: list[str],
    exclude_keywords: list[str],
) -> tuple[bool, list[str], str | None]:
    excluded = keyword_hits(text, exclude_keywords)
    if excluded:
        return False, [], f"excluded:{','.join(excluded[:3])}"

    matched = keyword_hits(text, include_keywords)
    if not matched:
        return False, [], "no_keyword_match"

    return True, matched, None


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    jsonl_path = Path(path)
    if not jsonl_path.exists():
        return []

    rows = []
    with jsonl_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def write_jsonl(path: str | Path, rows: list[dict[str, Any]]) -> None:
    jsonl_path = Path(path)
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    with jsonl_path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
            handle.write("\n")


def prune_rows(
    rows: list[dict[str, Any]],
    retention_days: int,
    now: datetime,
) -> list[dict[str, Any]]:
    cutoff = now.astimezone(JST) - timedelta(days=retention_days)
    kept = []
    for row in rows:
        published = parse_iso_datetime(row.get("published_at"))
        fetched = parse_iso_datetime(row.get("fetched_at"))
        comparable = published or fetched
        if comparable and comparable >= cutoff:
            kept.append(row)
    return kept


def parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def collect_source(
    source: dict[str, Any],
    config: dict[str, Any],
    fetched_at: datetime,
) -> tuple[list[dict[str, Any]], SourceResult]:
    source_name = source["name"]
    source_url = source["url"]
    parsed_feed = feedparser.parse(source_url)

    if parsed_feed.bozo and not parsed_feed.entries:
        error = str(getattr(parsed_feed, "bozo_exception", "feed parse error"))
        return [], SourceResult(source_name, source_url, ok=False, error=error)

    include_keywords = source.get("include_keywords") or config.get("include_keywords", [])
    exclude_keywords = source.get("exclude_keywords") or config.get("exclude_keywords", [])
    categories = config.get("categories", {})
    retention_days = int(config.get("retention_days", 180))
    cutoff = fetched_at.astimezone(JST) - timedelta(days=retention_days)

    items = []
    for entry in parsed_feed.entries:
        published_at, date_confidence = parse_entry_datetime(entry)
        if not published_at:
            continue
        if published_at < cutoff:
            continue

        canonical_url = normalize_url(entry.get("link", ""))
        text = entry_text(entry)
        keep, matched, _reason = should_keep_item(text, include_keywords, exclude_keywords)
        if not keep:
            continue

        category = category_guess(text, categories)
        score, score_reasons = score_item(source, matched, category, published_at, fetched_at)
        item = {
            "id": stable_item_id(source_name, entry, canonical_url),
            "canonical_url": canonical_url,
            "raw_link": entry.get("link", ""),
            "title": strip_markup(entry.get("title", "")),
            "summary": strip_markup(entry.get("summary", "")),
            "source_name": source_name,
            "source_url": source_url,
            "source_type": source.get("source_type", "rss"),
            "country": source.get("country", ""),
            "language": source.get("language", ""),
            "published_at": published_at.isoformat(),
            "updated_at": published_at.isoformat(),
            "fetched_at": fetched_at.astimezone(JST).isoformat(),
            "date_confidence": date_confidence,
            "tags": entry_tags(entry),
            "matched_keywords": matched,
            "category_guess": category,
            "score": score,
            "score_reasons": score_reasons,
        }
        items.append(item)

    return items, SourceResult(source_name, source_url, ok=True, item_count=len(items))


def merge_items(
    existing: list[dict[str, Any]],
    incoming: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], int]:
    by_key: dict[str, dict[str, Any]] = {}
    for row in existing:
        by_key[row.get("id") or row.get("canonical_url", "")] = row
        if row.get("canonical_url"):
            by_key[f"url:{row['canonical_url']}"] = row

    merged = list(existing)
    new_count = 0
    for item in incoming:
        id_key = item.get("id")
        url_key = f"url:{item.get('canonical_url', '')}"
        if id_key in by_key or url_key in by_key:
            continue
        merged.append(item)
        by_key[id_key] = item
        by_key[url_key] = item
        new_count += 1

    merged.sort(
        key=lambda row: (
            parse_iso_datetime(row.get("published_at")) or datetime.min.replace(tzinfo=JST),
            row.get("score", 0),
        ),
        reverse=True,
    )
    return merged, new_count


def collect_all(
    config: dict[str, Any],
    existing_rows: list[dict[str, Any]],
    now: datetime | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    fetched_at = now or utc_now()
    retained_rows = prune_rows(
        existing_rows,
        int(config.get("retention_days", 180)),
        fetched_at,
    )

    all_incoming = []
    source_results = []
    existing_keys = {row.get("id") for row in retained_rows}
    existing_keys.update(f"url:{row.get('canonical_url')}" for row in retained_rows if row.get("canonical_url"))
    for source in config.get("sources", []):
        try:
            items, result = collect_source(source, config, fetched_at)
            all_incoming.extend(items)
            source_results.append(result)
        except Exception as exc:  # noqa: BLE001 - source failures should be isolated
            source_results.append(
                SourceResult(source.get("name", ""), source.get("url", ""), ok=False, error=str(exc))
            )

    merged_rows, new_count = merge_items(retained_rows, all_incoming)

    incoming_ids = {item["id"] for item in all_incoming}
    for result in source_results:
        if not result.ok:
            continue
        result.new_count = sum(
            1
            for item in all_incoming
            if item.get("source_name") == result.name
            and item.get("id") in incoming_ids
            and item.get("id") not in existing_keys
            and f"url:{item.get('canonical_url')}" not in existing_keys
        )

    ok_sources = [result for result in source_results if result.ok]
    failed_sources = [result for result in source_results if not result.ok]
    status = {
        "fetched_at": fetched_at.astimezone(JST).isoformat(),
        "theme": config.get("theme", "talent_mgmt"),
        "total_sources": len(source_results),
        "ok_sources": len(ok_sources),
        "failed_sources": len(failed_sources),
        "incoming_items": len(all_incoming),
        "new_items": new_count,
        "retained_items": len(merged_rows),
        "sources": [result.__dict__ for result in source_results],
    }
    return merged_rows, status


def write_status(path: str | Path, status: dict[str, Any]) -> None:
    status_path = Path(path)
    status_path.parent.mkdir(parents=True, exist_ok=True)
    status_path.write_text(
        json.dumps(status, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
