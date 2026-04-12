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
from urllib import error, parse, request


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


def format_for_teams(content):
    """Teams投稿向けにテキストを整形する

    主な変換:
    - 「## 見出し」→「■ 見出し」（Teams では ## がそのまま表示される）
    - 「──────...」の罫線行 → 空行に置換（冗長な区切りを除去）
    - 「（URL: https://...）」→「  🔗 https://...」（字下げ＋アイコン付き）
    - 「このメールは〜」→「このレポートは〜」
    """
    import re

    lines = content.splitlines()
    result = []
    prev_blank = False

    for line in lines:
        # 罫線行（── を3文字以上含む行）を空行に変換
        if re.fullmatch(r"[─\-]{3,}", line.strip()):
            if not prev_blank:
                result.append("")
                prev_blank = True
            continue

        # Markdown 見出しを「■ 」形式に変換
        m = re.match(r"^#{1,3}\s+(.+)", line)
        if m:
            result.append(f"■ {m.group(1)}")
            prev_blank = False
            continue

        # URL を字下げ＋アイコン付きに変換
        m = re.match(r"^（URL:\s*(https?://\S+?)）\s*$", line)
        if m:
            result.append(f"  🔗 {m.group(1)}")
            prev_blank = False
            continue

        # フッターのメール文言をTeams向けに変更
        if "このメールはAIによる自動配信" in line:
            result.append("このレポートはAIによる自動生成です。")
            prev_blank = False
            continue

        result.append(line)
        prev_blank = (line.strip() == "")

    # 末尾の余分な空行を除去
    while result and result[-1].strip() == "":
        result.pop()

    return "\n".join(result)


def build_payload(filepath, content, topic_count, report_type):
    """Teams Workflows webhook に送る JSON を組み立てる

    Teams Workflows の「Webhook アラートをチャネルに送信する」
    テンプレートで扱いやすい MessageCard 形式で送る。
    """
    report_date = datetime.now().strftime("%Y/%m/%d")
    source_file = Path(filepath).name
    title = build_report_title(report_type, topic_count, report_date)
    teams_content = format_for_teams(content)

    return {
        "@type": "MessageCard",
        "@context": "https://schema.org/extensions",
        "summary": title,
        "themeColor": "0076D7",
        "title": title,
        "text": teams_content,
        "sections": [
            {
                "facts": [
                    {"name": "Report type", "value": report_type},
                    {"name": "Report date", "value": report_date},
                    {"name": "Topic count", "value": str(topic_count)},
                    {"name": "Source file", "value": source_file},
                ],
                "markdown": True,
            }
        ],
    }


def validate_webhook_url(webhook_url, env_name):
    """webhook URL が Power Automate Workflow 形式かを検証する。

    旧 Office 365 Connector URL（outlook.office.com/webhook/ など）や
    Microsoft Graph API URL は 401 DirectApiAuthorizationRequired を返すため、
    事前に検出して分かりやすいエラーメッセージを出す。
    """
    parsed = parse.urlparse(webhook_url)
    host = (parsed.netloc or "").lower()
    normalized_url = webhook_url.lower()

    if parsed.scheme != "https" or not host:
        print(f"ERROR: {env_name} に設定された URL が不正です。")
        print("  Power Automate Workflow が発行した https の webhook URL を設定してください。")
        sys.exit(1)

    deprecated_patterns = [
        "outlook.office.com/webhook",
        "outlook.office365.com/webhook",
        ".webhook.office.com/webhookb2",
        "webhook.office.com/webhookb2",
    ]
    graph_patterns = [
        "graph.microsoft.com",
        "api.teams.microsoft.com",
        "teams.microsoft.com",
    ]

    for pattern in deprecated_patterns:
        if pattern in normalized_url:
            print(
                f"ERROR: {env_name} に設定された URL は廃止済みの Office 365 Connector webhook です。"
            )
            print("  Microsoft は 2024〜2025 年にかけて旧 Connector webhook を段階的に廃止しました。")
            print("  【対処法】Teams チャンネルで「ワークフロー」から新しい webhook を作成してください:")
            print("  1. Teams のチャンネルを開く")
            print("  2. チャンネル名の右の「…」→「ワークフロー」をクリック")
            print("  3. 「チャネルへの投稿」テンプレートを選択")
            print("  4. 表示された webhook URL を GitHub Secrets の TEAMS_WEBHOOK_URL に設定")
            sys.exit(1)

    for pattern in graph_patterns:
        if pattern in host:
            print(
                f"ERROR: {env_name} に設定された URL は Microsoft Graph/Teams 直接 API の URL です。"
            )
            print("  この URL は OAuth 認証が必要なため webhook としては使用できません。")
            print("  【対処法】Power Automate Workflow が発行した匿名 webhook URL を設定してください。")
            sys.exit(1)

    print(f"OK: webhook host: {host}")


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
        if exc.code == 401 and "DirectApiAuthorizationRequired" in detail:
            print()
            print("  【原因】設定された webhook URL は匿名 POST を受け付けていません。")
            print("          Teams/Graph 直接 API、廃止済み Connector webhook、または")
            print("          Power Automate 側で OAuth 認証必須になっているトリガー URL の可能性があります。")
            print("  【対処法】以下の手順で匿名 webhook URL を取得・設定してください:")
            print("  1. Teams のチャンネルを開く")
            print("  2. チャンネル名の右の「…」→「ワークフロー」をクリック")
            print("  3. webhook request を受信してチャネル投稿するワークフローを作成")
            print("  4. トリガーが匿名 HTTP POST を許可する設定になっていることを確認")
            print("  5. GitHub Secrets の TEAMS_WORKFLOW_WEBHOOK_URL_TALENT_MGMT を新しい URL に更新")
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

    validate_webhook_url(webhook_url, env_name)
    send_to_teams_workflow(webhook_url, payload, timeout_seconds)

    print("\n" + "=" * 60)
    print("OK: 処理完了")
    print("=" * 60)


if __name__ == "__main__":
    main()
