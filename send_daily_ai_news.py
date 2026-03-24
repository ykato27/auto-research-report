"""
AIニュース日次まとめ メール送信スクリプト

Claude Code Webの定期実行で生成されたニュース本文（テキストファイル）を読み込み、
HTML形式に変換してGmail SMTP経由で送信する。

既存の email_report.py とは独立して動作する。

使い方:
    python send_daily_ai_news.py <テキストファイルパス>

環境変数（必須）:
    GMAIL_USER          - 送信元Gmailアドレス
    GMAIL_APP_PASSWORD  - Googleアプリパスワード
    RECIPIENT_EMAIL     - 送信先メールアドレス（カンマ区切りで複数可）
"""

import os
import sys
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


def load_news_content(filepath):
    """ニュース本文ファイルを読み込む"""
    if not os.path.exists(filepath):
        print(f"❌ エラー: ファイルが見つかりません: {filepath}")
        sys.exit(1)

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    if not content.strip():
        print("❌ エラー: ファイルが空です")
        sys.exit(1)

    print(f"✓ ニュース本文を読み込みました（{len(content)}文字）")
    return content


def filepath_to_report_type(filepath):
    """ファイルパスからレポートタイプを判定"""
    filename = filepath.lower()
    if "ai_news" in filename:
        return "ai_news"
    elif "skill_mgmt" in filename:
        return "skill_mgmt"
    elif "talent_mgmt" in filename:
        return "talent_mgmt"
    else:
        return "default"


def extract_topic_count(content):
    """本文からトピック数を抽出（日次・週次両対応）"""
    match = re.search(r"トピック数：(\d+)件", content)
    return match.group(1) if match else "?"


def text_to_html(content):
    """プレーンテキストのニュース本文をHTML形式に変換する"""

    lines = content.split("\n")
    html_lines = []

    for line in lines:
        stripped = line.strip()

        # 罫線
        if stripped.startswith("──"):
            html_lines.append('<hr style="border: none; border-top: 2px solid #4a90d9; margin: 20px 0;">')
            continue

        # h2 見出し（## で始まる行）
        if stripped.startswith("## "):
            heading = stripped[3:]
            html_lines.append(
                f'<h2 style="color: #2c3e50; border-bottom: 1px solid #eee; '
                f'padding-bottom: 8px; margin-top: 28px;">{heading}</h2>'
            )
            continue

        # URL行（→ で始まる）
        if stripped.startswith("→ "):
            url = stripped[2:].strip()
            html_lines.append(
                f'<p style="margin: 2px 0 16px 16px; font-size: 13px;">'
                f'→ <a href="{url}" style="color: #4a90d9;">{url}</a></p>'
            )
            continue

        # 箇条書き（・で始まる）
        if stripped.startswith("・"):
            text = stripped[1:]
            html_lines.append(
                f'<p style="margin: 4px 0 2px 8px;">・{text}</p>'
            )
            continue

        # 空行
        if not stripped:
            html_lines.append("<br>")
            continue

        # その他のテキスト
        html_lines.append(f"<p style='margin: 4px 0;'>{stripped}</p>")

    body_content = "\n".join(html_lines)

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: 'Helvetica Neue', Arial, 'Hiragino Kaku Gothic ProN', sans-serif;
             line-height: 1.8; color: #333; max-width: 800px; margin: 0 auto; padding: 20px;">
{body_content}
</body>
</html>
"""
    return html


def send_email(html_body, topic_count, report_type="default"):
    """Gmail SMTP経由でメールを送信"""
    print("📧 メール送信準備中...")

    gmail_user = os.environ.get("GMAIL_USER")
    gmail_password = os.environ.get("GMAIL_APP_PASSWORD")
    recipient = os.environ.get("RECIPIENT_EMAIL")

    if not all([gmail_user, gmail_password, recipient]):
        print("❌ エラー: メール送信に必要な環境変数が設定されていません")
        print(f"  GMAIL_USER:         {'✓' if gmail_user else '✗ 未設定'}")
        print(f"  GMAIL_APP_PASSWORD: {'✓' if gmail_password else '✗ 未設定'}")
        print(f"  RECIPIENT_EMAIL:    {'✓' if recipient else '✗ 未設定'}")
        sys.exit(1)

    # カンマ区切りで複数の受信者に対応
    recipients = [email.strip() for email in recipient.split(",")]

    # 今日の日付
    today = datetime.now().strftime("%Y/%m/%d")

    # メール作成
    msg = MIMEMultipart()
    msg["From"] = gmail_user
    msg["To"] = ", ".join(recipients)
    # レポートタイプ別の件名を生成
    report_labels = {
        "ai_news": "📰 AIニュース週次まとめ",
        "skill_mgmt": "📚 スキルマネジメント週次まとめ",
        "talent_mgmt": "👥 タレントマネジメント週次まとめ",
        "default": "📊 ニュースまとめ"
    }
    label = report_labels.get(report_type, report_labels["default"])
    msg["Subject"] = f"{label} {today}（{topic_count}件）"

    msg.attach(MIMEText(html_body, "html", "utf-8"))

    # Gmail SMTP経由で送信
    try:
        print("📤 メール送信中...")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, gmail_password)
            server.send_message(msg)
        print("✓ メール送信完了")
        print(f"  送信先: {', '.join(recipients)}")
        print(f"  件名: {msg['Subject']}")
    except Exception as e:
        print(f"❌ メール送信エラー: {str(e)}")
        sys.exit(1)


def main():
    """メイン処理"""
    print("=" * 60)
    print("📰 AIニュース日次まとめ メール送信")
    print("=" * 60 + "\n")

    # 引数チェック
    if len(sys.argv) < 2:
        print("使い方: python send_daily_ai_news.py <ニュース本文ファイルパス>")
        print("例: python send_daily_ai_news.py /tmp/ai_news_today.txt")
        sys.exit(1)

    filepath = sys.argv[1]

    # 1. ニュース本文を読み込み
    content = load_news_content(filepath)

    # 2. トピック数を抽出
    topic_count = extract_topic_count(content)

    # 3. HTML変換
    html_body = text_to_html(content)
    print(f"✓ HTML変換完了")

    # 4. メール送信（ファイル名から自動判定）
    report_type = filepath_to_report_type(filepath)
    send_email(html_body, topic_count, report_type)

    print("\n" + "=" * 60)
    print("✓ 処理完了")
    print("=" * 60)


if __name__ == "__main__":
    main()
