"""
Phase 1: RSS ニュース収集スクリプト（トークン消費ゼロ）

判断ロジックは一切持たない。固定ロジックのみ：
  - 30以上のRSSフィードを巡回
  - 直近7日以内の記事を抽出（正確な日付フィルタ）
  - キーワードマッチングで8カテゴリに仮分類
  - URL照合で重複排除
  - data/raw_news.json に保存 → Claude Code が読む

使い方:
    python src/collect_news.py [--days 7] [--output data/raw_news.json]
"""

import argparse
import json
import os
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

import feedparser
import requests

# ── RSS フィード一覧 ──────────────────────────────────────────
RSS_FEEDS = [
    # 海外 - HR/Talent/Skills
    {"url": "https://www.hrdive.com/feeds/news/", "source": "HR Dive", "lang": "en"},
    {"url": "https://joshbersin.com/feed/", "source": "Josh Bersin", "lang": "en"},
    {"url": "https://hrexecutive.com/feed/", "source": "HR Executive", "lang": "en"},
    {"url": "https://trainingmag.com/feed/", "source": "Training Magazine", "lang": "en"},
    {"url": "https://www.tlnt.com/feed/", "source": "TLNT", "lang": "en"},
    {"url": "https://www.aihr.com/blog/feed/", "source": "AIHR", "lang": "en"},
    {"url": "https://www.personneltoday.com/feed/", "source": "Personnel Today", "lang": "en"},
    {"url": "https://hrnews.co.uk/feed/", "source": "HR News UK", "lang": "en"},
    {"url": "https://www.hrdconnect.com/feed/", "source": "HRD Connect", "lang": "en"},
    {"url": "https://www.shrm.org/rss/pages/rss.aspx", "source": "SHRM", "lang": "en"},
    # 海外 - コンサル/リサーチ
    {"url": "https://hbr.org/topic/human-resource-management.rss", "source": "HBR", "lang": "en"},
    {"url": "https://www.mckinsey.com/capabilities/people-and-organizational-performance/our-insights/rss", "source": "McKinsey", "lang": "en"},
    {"url": "https://www2.deloitte.com/us/en/insights/topics/talent/rss.xml", "source": "Deloitte", "lang": "en"},
    {"url": "https://sloanreview.mit.edu/topic/talent-management/feed/", "source": "MIT Sloan", "lang": "en"},
    {"url": "https://www.weforum.org/feed/", "source": "WEF", "lang": "en"},
    # 海外 - L&D/Skills
    {"url": "https://www.td.org/rss", "source": "ATD", "lang": "en"},
    {"url": "https://elearningindustry.com/feed", "source": "eLearning Industry", "lang": "en"},
    {"url": "https://www.chieflearningofficer.com/feed/", "source": "CLO", "lang": "en"},
    # 海外 - Tech/AI/HR Tech
    {"url": "https://techcrunch.com/tag/hr-tech/feed/", "source": "TechCrunch HR", "lang": "en"},
    {"url": "https://venturebeat.com/category/ai/feed/", "source": "VentureBeat AI", "lang": "en"},
    # 国内
    {"url": "https://hrnote.jp/feed/", "source": "HR NOTE", "lang": "ja"},
    {"url": "https://hrpro.co.jp/rss.php", "source": "HRプロ", "lang": "ja"},
    {"url": "https://www.recruit-ms.co.jp/issue/rss/", "source": "リクルートMS", "lang": "ja"},
    {"url": "https://prtimes.jp/rss20.xml", "source": "PR Times", "lang": "ja"},
    {"url": "https://ledge.ai/feed/", "source": "Ledge.ai", "lang": "ja"},
    {"url": "https://japan.zdnet.com/rss/index.rdf", "source": "ZDNet Japan", "lang": "ja"},
]

# ── カテゴリ別キーワード（仮分類用） ──────────────────────────
CATEGORY_KEYWORDS = {
    "スキルフレームワーク・タレント戦略": [
        "skill framework", "competency model", "talent strategy", "workforce planning",
        "skills-based", "skill taxonomy", "job architecture", "talent management",
        "スキルフレームワーク", "コンピテンシー", "タレントマネジメント", "人材戦略", "スキルマップ",
    ],
    "スキル分析・タレントインテリジェンス": [
        "talent intelligence", "people analytics", "workforce analytics", "skill gap analysis",
        "talent data", "HR analytics", "workforce insight",
        "タレントインテリジェンス", "ピープルアナリティクス", "人材データ", "人材分析",
    ],
    "学習支援・採用・オンボーディング": [
        "learning", "training", "recruitment", "hiring", "talent acquisition", "onboarding",
        "L&D", "learning development", "reskilling", "upskilling",
        "採用", "研修", "育成", "リスキリング", "アップスキリング", "オンボーディング", "学習",
    ],
    "AI活用・スキル開発": [
        "AI", "artificial intelligence", "machine learning", "generative AI", "GenAI",
        "automation", "LLM", "AI skills", "digital skills",
        "人工知能", "生成AI", "DX", "デジタルスキル", "AI活用",
    ],
    "従業員エンゲージメント・配置・保持": [
        "employee engagement", "retention", "turnover", "wellbeing", "employee experience",
        "workforce mobility", "internal mobility", "talent retention",
        "エンゲージメント", "定着", "離職", "従業員体験", "配置転換",
    ],
    "報酬・キャリアパス": [
        "compensation", "salary", "pay", "reward", "career path", "career development",
        "total rewards", "pay equity", "skill-based pay",
        "報酬", "給与", "キャリア", "賃金",
    ],
    "グローバル・ダイバーシティ・DEI": [
        "diversity", "equity", "inclusion", "DEI", "global workforce", "international talent",
        "gender pay gap", "belonging",
        "ダイバーシティ", "DEI", "グローバル人材", "外国人材", "女性活躍",
    ],
    "企業導入事例・ベストプラクティス": [
        "case study", "best practice", "success story", "implementation", "pilot program",
        "enterprise", "deployment", "rollout",
        "導入事例", "ベストプラクティス", "成功事例",
    ],
}

# 収集対象の最低限キーワード（これが1つも含まれない記事は除外）
RELEVANCE_KEYWORDS = {
    "en": [
        "talent", "skill", "workforce", "HR", "employee", "learning", "training",
        "recruitment", "hiring", "engagement", "DEI", "people", "AI", "reskilling",
        "upskilling", "career", "competency", "performance", "retention",
    ],
    "ja": [
        "人材", "スキル", "採用", "育成", "タレント", "研修", "エンゲージメント",
        "労働", "従業員", "キャリア", "AI", "DX", "リスキリング",
    ],
}


def parse_date(entry) -> datetime | None:
    """feedparserエントリから公開日時をパース"""
    for field in ("published_parsed", "updated_parsed", "created_parsed"):
        t = getattr(entry, field, None)
        if t:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc)
            except Exception:
                continue
    return None


def is_within_days(dt: datetime, days: int) -> bool:
    """dt が現在から days 日以内かどうか"""
    if dt is None:
        return False
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    return dt >= cutoff


def classify_category(text: str) -> str:
    """キーワードマッチングでカテゴリを仮分類"""
    text_lower = text.lower()
    scores = {cat: 0 for cat in CATEGORY_KEYWORDS}
    for cat, kws in CATEGORY_KEYWORDS.items():
        for kw in kws:
            if kw.lower() in text_lower:
                scores[cat] += 1
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "未分類"


def is_relevant(text: str, lang: str) -> bool:
    """関連性キーワードが最低1つ含まれるか"""
    text_lower = text.lower()
    kws = RELEVANCE_KEYWORDS.get(lang, RELEVANCE_KEYWORDS["en"])
    return any(kw.lower() in text_lower for kw in kws)


def fetch_feed(feed_info: dict, days: int) -> list[dict]:
    """1つのRSSフィードを取得して記事リストを返す"""
    url = feed_info["url"]
    source = feed_info["source"]
    lang = feed_info.get("lang", "en")
    articles = []

    try:
        parsed = feedparser.parse(url, request_headers={"User-Agent": "Mozilla/5.0"})
        if parsed.bozo and not parsed.entries:
            return []

        for entry in parsed.entries:
            pub_dt = parse_date(entry)
            if not is_within_days(pub_dt, days):
                continue

            title = getattr(entry, "title", "") or ""
            summary = getattr(entry, "summary", "") or ""
            link = getattr(entry, "link", "") or ""

            # タグ除去
            summary_clean = re.sub(r"<[^>]+>", "", summary).strip()
            summary_short = summary_clean[:300]

            combined_text = f"{title} {summary_short}"
            if not is_relevant(combined_text, lang):
                continue

            category = classify_category(combined_text)
            articles.append({
                "title": title,
                "url": link,
                "source": source,
                "lang": lang,
                "published": pub_dt.isoformat() if pub_dt else None,
                "summary": summary_short,
                "category_hint": category,
            })

    except Exception as e:
        print(f"  WARN: {source} の取得に失敗: {e}")

    return articles


def deduplicate(articles: list[dict]) -> list[dict]:
    """URLで重複排除（正規化後）"""
    seen = set()
    result = []
    for a in articles:
        url = a.get("url", "")
        # クエリ文字列・フラグメント除去して正規化
        parsed = urlparse(url)
        normalized = f"{parsed.netloc}{parsed.path}".rstrip("/")
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(a)
    return result


def collect(days: int = 7, output_path: str = "data/raw_news.json") -> dict:
    """全フィードを巡回してJSONに保存"""
    print(f"=== RSS ニュース収集開始（直近{days}日間） ===\n")
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y/%m/%d")
    today = datetime.now(timezone.utc).strftime("%Y/%m/%d")

    all_articles = []
    for i, feed_info in enumerate(RSS_FEEDS, 1):
        print(f"[{i:02d}/{len(RSS_FEEDS)}] {feed_info['source']} を取得中...")
        articles = fetch_feed(feed_info, days)
        print(f"      → {len(articles)} 件（関連記事）")
        all_articles.extend(articles)
        time.sleep(0.5)  # サーバー負荷軽減

    all_articles = deduplicate(all_articles)

    # カテゴリ別集計
    by_category = {}
    for a in all_articles:
        cat = a["category_hint"]
        by_category[cat] = by_category.get(cat, 0) + 1

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "period": {"start": cutoff, "end": today},
        "days": days,
        "total_count": len(all_articles),
        "by_category": by_category,
        "articles": sorted(all_articles, key=lambda x: x.get("published") or "", reverse=True),
    }

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n=== 収集完了 ===")
    print(f"  合計: {len(all_articles)} 件（重複排除済み）")
    print(f"  期間: {cutoff} 〜 {today}")
    print(f"  カテゴリ別内訳:")
    for cat, count in sorted(by_category.items(), key=lambda x: -x[1]):
        print(f"    {cat}: {count}件")
    print(f"  出力: {output_path}")

    return result


def main():
    parser = argparse.ArgumentParser(description="RSS ニュース収集（Phase 1）")
    parser.add_argument("--days", type=int, default=7, help="収集対象の日数（デフォルト: 7）")
    parser.add_argument("--output", default="data/raw_news.json", help="出力JSONパス")
    args = parser.parse_args()

    result = collect(days=args.days, output_path=args.output)

    if result["total_count"] == 0:
        print("\nINFO: 収集記事数が0件のため、後続フェーズをスキップします。")
        raise SystemExit(0)


if __name__ == "__main__":
    main()
