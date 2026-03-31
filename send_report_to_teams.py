"""
Teams Workflows webhook 送信スクリプト

Claude Code Web で生成されたニュース本文（テキストファイル）を読み込み、
Microsoft Teams Workflows の webhook に JSON で送信する。

既存のメール送信処理とは独立して動作する。

使い方:
    python send_report_to_teams.py <テキストファイルパス>
    python send_report_to_teams.py <テキストファイルパス> --dry-run

環境変数:
    TEAMS_WORKFLOW_WEBHOOK_URL                 - 既定の Teams Workflows webhook URL
    TEAMS_WORKFLOW_WEBHOOK_URL_AI_NEWS         - AI ニュース専用 webhook URL（任意）
    TEAMS_WORKFLOW_WEBHOOK_URL_TALENT_MGMT     - タレントマネジメント専用 webhook URL（任意）
    TEAMS_WORKFLOW_TIMEOUT_SECONDS             - HTTP タイムアウト秒数（任意、既定 30）
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib import error, request


def load_news_content(filepath):
    """ニュース本文ファイルを読み込む"""
    path = Path(filepath)
    if not path.exists():
        print(f"ERROR: ファイルが見つかりません: {filepath}")
        sys.exit(1)

    content = path.read_text(encoding="utf-8")
    if not content.strip():
        print("ERROR: ファイルが空です")
        sys.exit(1)

    print(f"OK: ニュース本文を読み込みました（{len(content)}文字）")
    return content


def filepath_to_report_type(filepath):
    """ファイルパスからレポートタイプを判定"""
    filename = str(filepath).lower()
    if "ai_news" in filename:
        return "ai_news"
    if "talent_mgmt" in filename:
        return "talent_mgmt"
    return "default"


def extract_topic_count(content):
    """本文からトピック数を抽出（日次・週次両対応）"""
    match = re.search(r"トピック数：(\d+)件", content)
    return match.group(1) if match else "?"


def build_report_title(report_type, topic_count, report_date):
    """Teams 投稿用のタイトルを作成する"""
    report_labels = {
        "ai_news": "AIニュース週次まとめ",
        "talent_mgmt": "人材・スキル戦略グローバル動向",
        "default": "ニュースまとめ",
    }
    label = report_labels.get(report_type, report_labels["default"])
    return f"{label} {report_date}（{topic_count}件）"


def resolve_webhook_url(report_type):
    """レポートタイプに応じた webhook URL を取得する"""
    candidates = []
    if report_type == "ai_news":
        candidates.append("TEAMS_WORKFLOW_WEBHOOK_URL_AI_NEWS")
    elif report_type == "talent_mgmt":
        candidates.append("TEAMS_WORKFLOW_WEBHOOK_URL_TALENT_MGMT")

    candidates.append("TEAMS_WORKFLOW_WEBHOOK_URL")

    for env_name in candidates:
        value = os.environ.get(env_name)
        if value:
            return env_name, value

    return None, None


def build_payload(filepath, content, topic_count, report_type):
    """Teams Workflows webhook に送る JSON を組み立てる"""
    report_date = datetime.now().strftime("%Y/%m/%d")
    source_file = Path(filepath).name
    title = build_report_title(report_type, topic_count, report_date)

    return {
        "title": title,
        "reportType": report_type,
        "reportDate": report_date,
        "topicCount": topic_count,
        "sourceFile": source_file,
        "content": content,
    }


def send_to_teams_workflow(webhook_url, payload, timeout_seconds):
    """Teams Workflows webhook に JSON を POST する"""
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        webhook_url,
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=timeout_seconds) as response:
            response_body = response.read().decode("utf-8", errors="replace")
            print(f"OK: Teams Workflows webhook 送信完了: HTTP {response.status}")
            if response_body.strip():
                print("  応答:")
                print(response_body.strip())
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        print(f"ERROR: Teams webhook 送信エラー: HTTP {exc.code}")
        if detail.strip():
            print(detail.strip())
        sys.exit(1)
    except error.URLError as exc:
        print(f"ERROR: Teams webhook 接続エラー: {exc.reason}")
        sys.exit(1)


def parse_args():
    parser = argparse.ArgumentParser(
        description="ニュース本文ファイルを Teams Workflows webhook に送信します。"
    )
    parser.add_argument("filepath", help="送信対象のテキストファイル")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="HTTP 送信は行わず、送信予定の JSON payload を表示します。",
    )
    return parser.parse_args()


def main():
    print("=" * 60)
    print("Teams Workflows webhook 送信")
    print("=" * 60 + "\n")

    args = parse_args()

    content = load_news_content(args.filepath)
    topic_count = extract_topic_count(content)
    report_type = filepath_to_report_type(args.filepath)
    payload = build_payload(args.filepath, content, topic_count, report_type)

    print(f"OK: ペイロード作成完了: reportType={report_type}, topicCount={topic_count}")

    if args.dry_run:
        print("INFO: dry-run モードのため HTTP 送信は行いません")
        print(json.dumps(payload, ensure_ascii=True, indent=2))
        print("\n" + "=" * 60)
        print("OK: 処理完了")
        print("=" * 60)
        return

    env_name, webhook_url = resolve_webhook_url(report_type)
    if not webhook_url:
        print("ERROR: Teams Workflows webhook URL が設定されていません")
        print("  以下のいずれかを設定してください:")
        print("  - TEAMS_WORKFLOW_WEBHOOK_URL")
        print("  - TEAMS_WORKFLOW_WEBHOOK_URL_AI_NEWS")
        print("  - TEAMS_WORKFLOW_WEBHOOK_URL_TALENT_MGMT")
        sys.exit(1)

    timeout_seconds = int(os.environ.get("TEAMS_WORKFLOW_TIMEOUT_SECONDS", "30"))
    print(f"OK: 送信先 webhook: {env_name}")
    print(f"OK: タイムアウト: {timeout_seconds} 秒")

    send_to_teams_workflow(webhook_url, payload, timeout_seconds)

    print("\n" + "=" * 60)
    print("OK: 処理完了")
    print("=" * 60)


if __name__ == "__main__":
    main()
