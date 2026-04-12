# 📊 Auto Research Report

Claude Code Web の定期実行を活用した、人材・スキル戦略レポート配信ツールです。

現在は人材・スキル戦略グローバル動向レポート用の構成です。Claude がニュースを検索・検証・整形したうえで、メールまたは Teams へ配信できます。

---

## 🚀 概要

本リポジトリは以下の仕組みで動作します。

1. Claude Code Web（claude.ai/code）の定期実行が毎週起動
2. `prompts/talent_mgmt_weekly.md` に従い、Claude が Web 検索でニュースを収集・公開日検証・分類・整形
3. `reports/talent_mgmt_weekly_YYYYMMDD.txt` を Git push
4. GitHub Actions がメールまたは Teams へ配信

ポイントは、ニュース収集・分析・整形は全て Claude Code Web 上で行い、リポジトリ内のスクリプトは配信のみを担当するという役割分担です。外部検索・分析 API は使用しません。

---

## 📁 ディレクトリ構成

```
auto-research-report/
├── send_talent_mgmt_email.py   # 人材・スキル戦略レポート メール送信スクリプト
├── send_report_to_teams.py     # Teams Workflows webhook 送信スクリプト
├── validate_talent_mgmt_report.py # 人材・スキル戦略レポート検証スクリプト
├── prompts/
│   └── talent_mgmt_weekly.md    # 人材・スキル戦略週次まとめ
├── .github/
│   └── workflows/               # GitHub Actions（将来拡張用）
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🔧 セットアップ

### 1. 環境変数 / GitHub Secrets の設定

GitHub Actions からメール送信する場合は、リポジトリの Settings → Secrets and variables → Actions に以下を登録してください。

| Secret 名 | 内容 | 必須 |
|---|---|---|
| `GMAIL_USER` | 送信元 Gmail アドレス | ○ |
| `GMAIL_APP_PASSWORD` | Google アプリパスワード（16 文字） | ○ |
| `RECIPIENT_EMAIL_TALENT_MGMT` | 人材・スキル戦略レポート送信先メールアドレス（カンマ区切りで複数可） | ○ |
| `RECIPIENT_EMAIL` | 互換用の既定送信先メールアドレス | △ |

Teams Workflows を使う場合は、以下の環境変数または GitHub Secret を利用します。タレントマネジメント週次レポートの Teams 送信 workflow では、`TEAMS_WORKFLOW_WEBHOOK_URL_TALENT_MGMT` を優先し、未設定の場合のみ互換用の `TEAMS_WEBHOOK_URL` を使います。

| Secret 名 | 内容 | 必須 |
|---|---|---|
| `TEAMS_WORKFLOW_WEBHOOK_URL` | Teams Workflows の既定 webhook URL | △ |
| `TEAMS_WORKFLOW_WEBHOOK_URL_TALENT_MGMT` | タレントマネジメント専用 webhook URL | ○（Teams送信時） |
| `TEAMS_WEBHOOK_URL` | 旧 workflow 互換用のタレントマネジメント webhook URL | △ |

`TEAMS_WORKFLOW_WEBHOOK_URL_TALENT_MGMT` が未設定の場合は `TEAMS_WORKFLOW_WEBHOOK_URL` を使います。

### 2. Gmail アプリパスワードの取得方法

1. https://myaccount.google.com/security で 2 段階認証を有効化
2. https://myaccount.google.com/apppasswords でアプリパスワードを生成
3. 表示された 16 文字のパスワードを `GMAIL_APP_PASSWORD` として登録

### 3. Claude Code Web での定期実行登録

1. https://claude.ai/code にアクセス
2. リポジトリ `ykato27/auto-research-report` を選択
3. スケジュール設定画面でプロンプトを登録（`prompts/` 内の内容を使用）
4. 頻度・時間を設定（例：毎週月曜 朝 8:00 JST）

---

## 📬 メール送信スクリプト

### send_talent_mgmt_email.py

Claude Code Web が生成したプレーンテキストのレポート本文をファイルから読み取り、HTML に変換して Gmail SMTP 経由で送信します。

**使い方：**

```bash
python send_talent_mgmt_email.py <テキストファイルパス>
```

**例：**

```bash
python send_talent_mgmt_email.py reports/talent_mgmt_weekly_20260412.txt
```

**処理内容：**

- テキスト本文を HTML 形式に自動変換
  - `## ` → `<h2>` 見出し
  - `──────` → `<hr>` 罫線
  - `→ URL` または `（URL: {引用元}）` → クリック可能な `<a href>` リンク
  - `・` → 箇条書き段落
- 件名は「人材・スキル戦略グローバル動向 {日付}（{件数}件）」で生成
- `GMAIL_USER` / `GMAIL_APP_PASSWORD` / `RECIPIENT_EMAIL_TALENT_MGMT` の環境変数で認証・送信

**依存関係：** Python 標準ライブラリのみ（追加パッケージ不要）

---

## ✅ レポート検証スクリプト

### validate_talent_mgmt_report.py

生成済みの人材・スキル戦略レポートを配信前に検証します。メール送信workflowとTeams送信workflowの両方で、送信前にこの検証を実行します。

**使い方：**

```bash
python validate_talent_mgmt_report.py reports/talent_mgmt_weekly_20260412.txt
```

**検証内容：**

- ファイル名 `talent_mgmt_weekly_YYYYMMDD.txt` から対象期間を算出
- 各ニュース項目に `（公開日: YYYY/MM/DD）` と `（URL: https://...）` があることを確認
- 公開日が対象期間外、未来日、不明の場合は失敗
- URL内の日付が対象期間より古い場合は失敗
- SEO統計まとめ等のblocked domainを含む場合は失敗
- フッターの `今週のトピック数：N件` とカテゴリ内ニュース項目数が一致しない場合は失敗
- 25件未満は警告扱い。古い記事で水増ししないため、検証済みニュースのみを優先します。

---

## 📣 Teams 送信スクリプト

### send_report_to_teams.py

Claude Code Web が生成したプレーンテキストのレポート本文をファイルから読み取り、Teams Workflows の webhook に JSON で送信します。

この実装は既存メール送信とは独立しており、タレントマネジメント週次レポートは GitHub Actions から送信できます。

**使い方：**

```bash
python send_report_to_teams.py <テキストファイルパス>
```

**送信前の payload 確認：**

```bash
python send_report_to_teams.py <テキストファイルパス> --dry-run
```

**送信する JSON 形式：**

```json
{
  "@type": "MessageCard",
  "@context": "https://schema.org/extensions",
  "subject": "人材・スキル戦略グローバル動向 2026/04/12（26件）",
  "summary": "人材・スキル戦略グローバル動向 2026/04/12（26件）",
  "themeColor": "0076D7",
  "title": "人材・スキル戦略グローバル動向 2026/04/12（26件）",
  "text": "Source: talent_mgmt_weekly_20260412.txt\n\n各セクションを展開して確認してください。",
  "sections": [
    {
      "activityTitle": "今週のサマリ",
      "text": "Teams投稿向けに整形したセクション本文",
      "markdown": true
    }
  ]
}
```

**想定している Teams Workflows 側の受け口：**

1. Teams の Workflows で `When a Teams webhook request is received` を作成
2. 上記 JSON を受けるスキーマを定義
3. 後続アクションで Teams のチャネル投稿や Adaptive Card 投稿を実行

Teams Workflows の「Webhook アラートをチャネルに送信する」テンプレートで扱いやすい MessageCard 形式で送ります。このスクリプトは Markdown 見出しや URL 行を Teams 投稿向けに軽く整形してから送信します。Teams 投稿の件名には `subject` を使えます。日付は `talent_mgmt_weekly_YYYYMMDD.txt` のファイル名から自動判定します。

GitHub Actions で `HTTP 202` が出る場合、webhook の受信までは成功しています。Teams に投稿されない場合は Power Automate の実行履歴を開き、チャネル投稿アクションの失敗理由を確認してください。

`HTTP 401 DirectApiAuthorizationRequired` が出る場合、設定されている URL は匿名 POST を受け付けていません。Teams/Graph 直接 API、廃止済み Office 365 Connector webhook、または Power Automate 側で OAuth 認証必須になっているトリガー URL の可能性があります。Teams Workflows で匿名 HTTP POST を受け付ける webhook URL を作り直し、GitHub Secret `TEAMS_WORKFLOW_WEBHOOK_URL_TALENT_MGMT` に設定してください。

**対応する環境変数：**

| 環境変数 | 用途 |
|---|---|
| `TEAMS_WORKFLOW_WEBHOOK_URL` | 既定の webhook URL |
| `TEAMS_WORKFLOW_WEBHOOK_URL_TALENT_MGMT` | タレントマネジメント専用 webhook URL |
| `TEAMS_WEBHOOK_URL` | GitHub Actions 互換用の旧 Secret 名 |
| `TEAMS_WORKFLOW_TIMEOUT_SECONDS` | HTTP タイムアウト秒数（既定 30） |

**依存関係：** Python 標準ライブラリのみ（追加パッケージ不要）

---

## 📋 プロンプト一覧

各テーマのプロンプトは `prompts/` ディレクトリに格納します。Claude Code Web の定期実行に登録する際は、各ファイル内のプロンプト本文をコピーして使用してください。

| ファイル | テーマ | 対象 | 頻度 | 状態 |
|---|---|---|---|---|
| `talent_mgmt_weekly.md` | 人材・スキル戦略グローバル動向（スキル＋タレント＋インテリジェンス統合） | 国内・海外 | 毎週月曜 | ✅ 完成 |

### 新しいテーマを追加するには

1. `prompts/` に新しいプロンプトファイル（`.md`）を追加
2. Claude Code Web のスケジュール設定でプロンプトを登録
3. 頻度・時間を設定

新しいテーマを追加する際は、既存のタレントマネジメント系ファイルと混ざらないよう、プロンプト、レポートファイル名、Secret 名、workflow 名にテーマ名を含めてください。

---

## ⚙️ 動作フロー

```
スケジュール起動（毎週）
    ↓
Claude Code Web が起動
    ↓
Web 検索 → 公開日検証 → 分類 → 整形（Claude が実行）
    ↓
reports/talent_mgmt_weekly_YYYYMMDD.txt に本文を保存
    ↓
python validate_talent_mgmt_report.py reports/talent_mgmt_weekly_YYYYMMDD.txt
    ↓
python send_talent_mgmt_email.py reports/talent_mgmt_weekly_YYYYMMDD.txt
または
python send_report_to_teams.py reports/talent_mgmt_weekly_YYYYMMDD.txt
    ↓
メール送信または Teams Workflows webhook 送信
```

---

## 📝 ライセンス

MIT License

---

## 👨‍💻 作成者

[@ykato27](https://github.com/ykato27)
