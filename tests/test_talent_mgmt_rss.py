import unittest
from datetime import datetime, timedelta, timezone

from src import talent_mgmt_rss as rss


class TalentMgmtRssTests(unittest.TestCase):
    def test_normalize_url_removes_tracking_params_and_fragment(self):
        url = "HTTPS://Example.COM/path?a=1&utm_source=x&fbclid=y#section"

        self.assertEqual(rss.normalize_url(url), "https://example.com/path?a=1")

    def test_should_keep_item_requires_include_keyword(self):
        keep, matched, reason = rss.should_keep_item(
            "A new skills framework for workforce planning",
            ["skills framework"],
            ["webinar only"],
        )

        self.assertTrue(keep)
        self.assertEqual(matched, ["skills framework"])
        self.assertIsNone(reason)

    def test_should_keep_item_excludes_low_signal_terms(self):
        keep, matched, reason = rss.should_keep_item(
            "skills framework webinar only",
            ["skills framework"],
            ["webinar only"],
        )

        self.assertFalse(keep)
        self.assertEqual(matched, [])
        self.assertEqual(reason, "excluded:webinar only")

    def test_should_keep_item_excludes_job_noise(self):
        keep, matched, reason = rss.should_keep_item(
            "human capital manager job in Chicago",
            ["human capital"],
            ["job in", "manager job"],
        )

        self.assertFalse(keep)
        self.assertEqual(matched, [])
        self.assertEqual(reason, "excluded:job in,manager job")

    def test_category_guess_selects_most_specific_category(self):
        categories = {
            "skills_management": {"keywords": ["skills framework", "competency"]},
            "talent_intelligence": {"keywords": ["people analytics"]},
        }

        self.assertEqual(
            rss.category_guess("New competency and skills framework released", categories),
            "skills_management",
        )

    def test_parse_pubmed_date(self):
        parsed = rss.parse_pubmed_date("2026 Apr 19")

        self.assertEqual(parsed.isoformat(), "2026-04-19T00:00:00+09:00")

    def test_pubmed_date_range(self):
        start = datetime(2026, 4, 19, 12, tzinfo=timezone.utc)
        end = datetime(2026, 4, 20, 12, tzinfo=timezone.utc)

        self.assertEqual(
            rss.pubmed_date_range(start, end),
            '("2026/04/19"[Date - Publication] : "2026/04/20"[Date - Publication])',
        )

    def test_merge_items_deduplicates_by_canonical_url(self):
        existing = [{"id": "old", "canonical_url": "https://example.com/a", "published_at": "2026-04-01T00:00:00+09:00"}]
        incoming = [{"id": "new", "canonical_url": "https://example.com/a", "published_at": "2026-04-02T00:00:00+09:00"}]

        merged, new_count = rss.merge_items(existing, incoming)

        self.assertEqual(new_count, 0)
        self.assertEqual(len(merged), 1)

    def test_prune_rows_removes_old_items(self):
        now = datetime(2026, 4, 20, tzinfo=timezone.utc)
        rows = [
            {"published_at": (now - timedelta(days=10)).isoformat()},
            {"published_at": (now - timedelta(days=1)).isoformat()},
        ]

        self.assertEqual(len(rss.prune_rows(rows, retention_days=7, now=now)), 1)

    def test_prune_rows_by_hours_keeps_only_recent_snapshot(self):
        now = datetime(2026, 4, 20, 12, tzinfo=timezone.utc)
        rows = [
            {"published_at": (now - timedelta(hours=25)).isoformat()},
            {"published_at": (now - timedelta(hours=23)).isoformat()},
        ]

        self.assertEqual(len(rss.prune_rows_by_hours(rows, retention_hours=24, now=now)), 1)


if __name__ == "__main__":
    unittest.main()
