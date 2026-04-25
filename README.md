# 📊 Auto Research Report

Claude Code Web の定期実行を活用した、人材・スキル戦略レポート配信ツールです。

現在は人材・スキル戦略グローバル動向レポート用の構成です。Claude がニュースを検索・検証・整形したうえで、Teams へ配信します。

---

## 🚀 概要

本リポジトリは以下の仕組みで動作します。

1. Claude Code Web（claude.ai/code）の定期実行が毎週起動
2. `prompts/talent_mgmt_weekly.md` に従い、Claude が Web 検索でニュースを収集・公開日検証・分類・整形
3. `reports/talent_mgmt_weekly_YYYYMMDD.txt` を Git push
4. GitHub Actions が Teams へ配信

ポイントは、ニュース収集・分析・整形は全て Claude Code Web 上で行い、リポジトリ内のスクリプトは配信のみを担当するという役割分担です。外部検索・分析 API は使用しません。

---

## 📁 ディレクトリ構成

```
auto-research-report/
├── send_report_to_teams.py        # Teams Workflows webhook 送信スクリプト
├── validate_talent_mgmt_report.py # 人材・スキル戦略レポート検証スクリプト
├── feeds/                         # RSS / Google News RSS ソース設定
│   └── talent_mgmt.yaml           # タレントマネジメント日次収集ソース
├── src/                           # RSS収集・候補生成スクリプト
│   ├── collect_talent_mgmt_rss.py
│   ├── build_talent_mgmt_candidates.py
│   └── talent_mgmt_rss.py
├── data/                          # 日次収集した候補データ（GitHub Actionsが更新）
├── prompts/
│   └── talent_mgmt_weekly.md      # 人材・スキル戦略週次まとめ
├── .github/
│   └── workflows/
│       ├── collect_talent_mgmt_rss.yml   # RSS日次収集
│       └── send_talent_mgmt_teams.yml    # Teams配信
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🔧 セットアップ

### 1. GitHub Secrets の設定

リポジトリの Settings → Secrets and variables → Actions に以下を登録してください。

| Secret 名 | 内容 | 必須 |
|---|---|---|
| `TEAMS_WORKFLOW_WEBHOOK_URL_TALENT_MGMT` | タレントマネジメント専用 webhook URL | ○ |
| `TEAMS_WORKFLOW_WEBHOOK_URL` | フォールバック用 webhook URL | △ |

`TEAMS_WORKFLOW_WEBHOOK_URL_TALENT_MGMT` が未設定の場合は `TEAMS_WORKFLOW_WEBHOOK_URL` を使います。

### 2. Claude Code Web での定期実行登録

1. https://claude.ai/code にアクセス
2. リポジトリ `ykato27/auto-research-report` を選択
3. スケジュール設定画面でプロンプトを登録（`prompts/` 内の内容を使用）
4. 頻度・時間を設定（例：毎週月曜 朝 8:00 JST）

---

## ✅ レポート検証スクリプト

### validate_talent_mgmt_report.py

生成済みの人材・スキル戦略レポートを配信前に検証します。Teams 送信 workflow で送信前にこの検証を実行します。

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

## 🗞️ タレントマネジメント RSS 日次収集

`feeds/talent_mgmt.yaml` に定義した国内・海外の信頼ソースから、スキルマネジメント、タレントマネジメント、タレントインテリジェンス関連の候補記事を毎日収集します。PubMed は NCBI E-utilities をAPIキーなしで利用し、学術寄りの人材育成・コンピテンシー・トレーニング研究を補助的に取得します。

毎日の収集結果は通知せず、`data/talent_mgmt_items.jsonl` に保存します。このファイルは実行時点から24時間以内に公開・更新された候補だけを保持する日次スナップショットです。週次レポートの作成方法は別途検討できるよう、候補Markdown生成までをPythonで行います。

**日次収集：**

```bash
python src/collect_talent_mgmt_rss.py \
  --config feeds/talent_mgmt.yaml \
  --store data/talent_mgmt_items.jsonl \
  --status data/talent_mgmt_source_status.json
```

**保存前の確認：**

```bash
python src/collect_talent_mgmt_rss.py --dry-run
```

**週次候補Markdownの生成：**

```bash
python src/build_talent_mgmt_candidates.py --since-days 7 --limit 80
```

**処理内容：**

- RSS / Google News RSS / PubMed E-utilities の取得
- 実行時点から24時間以内に公開・更新された候補のみ抽出
- 公開日・更新日のJST正規化
- URL正規化とトラッキングパラメータ除去
- `id` / `guid` / URL による重複排除
- キーワード一致、カテゴリ仮分類、ソース信頼度、鮮度によるスコアリング
- 実行時点から24時間を超えた保存済み候補の整理
- ソース別の成功/失敗状況を `data/talent_mgmt_source_status.json` に保存

**GitHub Actions：**

`.github/workflows/collect_talent_mgmt_rss.yml` が毎日 7:00 JST に実行され、`data/` の差分がある場合のみ自動コミットします。`reports/` は更新しないため、週次 Teams 送信 workflow は起動しません。

---

## 📣 Teams 送信スクリプト

### send_report_to_teams.py

Claude Code Web が生成したプレーンテキストのレポート本文をファイルから読み取り、Teams Workflows の webhook に JSON で送信します。

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
| `TEAMS_WORKFLOW_WEBHOOK_URL_TALENT_MGMT` | タレントマネジメント専用 webhook URL |
| `TEAMS_WORKFLOW_WEBHOOK_URL` | フォールバック用 webhook URL |
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
スケジュール起動（毎週月曜 08:00 JST）
    ↓
Claude Code Web が起動
    ↓
Web 検索 → 公開日検証 → 分類 → 整形（Claude が実行）
    ↓
reports/talent_mgmt_weekly_YYYYMMDD.txt を main へ push
    ↓
GitHub Actions (send_talent_mgmt_teams.yml) が起動
    ↓
validate_talent_mgmt_report.py で検証
    ↓
send_report_to_teams.py で Teams へ配信
```

---

## 📝 ライセンス

MIT License

---

## 👨‍💻 作成者

[@ykato27](https://github.com/ykato27)
