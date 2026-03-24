# 📊 Auto Research Report

Claude Code Web の定期実行を活用した、マルチテーマ対応の自動リサーチ＆レポート配信ツールです。

テーマごとにプロンプトを用意し、Claude がニュースを検索・検証・整形したうえで、SMTP 経由でメール配信します。

---

## 🚀 概要

本リポジトリは以下の仕組みで動作します。

1. Claude Code Web（claude.ai/code）の定期実行が毎日・毎週など指定スケジュールで起動
2. `prompts/` 内のプロンプトに従い、Claude が Web 検索でニュースを収集・公開日検証・分類・整形
3. 整形した本文を `send_daily_ai_news.py` に渡し、HTML 変換して Gmail SMTP 経由で配信

ポイントは、ニュース収集・分析・整形は全て Claude Code Web 上で行い、リポジトリ内のスクリプトはメール送信のみを担当するという役割分担です。外部 API（Gemini、Tavily 等）は使用しません。

---

## 📁 ディレクトリ構成

```
auto-research-report/
├── send_daily_ai_news.py       # メール送信スクリプト（全テーマ共通）
├── prompts/                     # テーマ別プロンプト
│   ├── ai_news_daily.md         # AIニュース日次まとめ（予定）
│   ├── skill_mgmt_weekly.md     # 海外スキルマネジメント週次（予定）
│   └── talent_mgmt_weekly.md    # 国内タレントマネジメント週次（予定）
├── .github/
│   └── workflows/               # GitHub Actions（将来拡張用）
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
| `GMAIL_USER` | 送信元 Gmail アドレス | ○ |
| `GMAIL_APP_PASSWORD` | Google アプリパスワード（16 文字） | ○ |
| `RECIPIENT_EMAIL` | 送信先メールアドレス（カンマ区切りで複数可） | ○ |

### 2. Gmail アプリパスワードの取得方法

1. https://myaccount.google.com/security で 2 段階認証を有効化
2. https://myaccount.google.com/apppasswords でアプリパスワードを生成
3. 表示された 16 文字のパスワードを `GMAIL_APP_PASSWORD` として登録

### 3. Claude Code Web での定期実行登録

1. https://claude.ai/code にアクセス
2. リポジトリ `ykato27/auto-research-report` を選択
3. スケジュール設定画面でプロンプトを登録（`prompts/` 内の内容を使用）
4. 頻度・時間を設定（例：毎日 朝 8:00 JST）

---

## 📬 メール送信スクリプト

### send_daily_ai_news.py

Claude Code Web が生成したプレーンテキストのレポート本文をファイルから読み取り、HTML に変換して Gmail SMTP 経由で送信します。

**使い方：**

```bash
python send_daily_ai_news.py <テキストファイルパス>
```

**例：**

```bash
python send_daily_ai_news.py /tmp/ai_news_today.txt
```

**処理内容：**

- テキスト本文を HTML 形式に自動変換
  - `## ` → `<h2>` 見出し
  - `──────` → `<hr>` 罫線
  - `→ URL` または `（URL: {引用元}）` → クリック可能な `<a href>` リンク
  - `・` → 箇条書き段落
- 件名をファイル名から自動判定して生成
  - `ai_news_*.txt` → 「📰 AIニュース週次まとめ {日付}（{件数}件）」
  - `talent_mgmt_*.txt` → 「👥 人材・スキル戦略グローバル動向 {日付}（{件数}件）」
- `GMAIL_USER` / `GMAIL_APP_PASSWORD` / `RECIPIENT_EMAIL` の環境変数で認証・送信

**依存関係：** Python 標準ライブラリのみ（追加パッケージ不要）

---

## 📋 プロンプト一覧

各テーマのプロンプトは `prompts/` ディレクトリに格納します。Claude Code Web の定期実行に登録する際は、各ファイル内のプロンプト本文をコピーして使用してください。

| ファイル | テーマ | 対象 | 頻度 | 状態 |
|---|---|---|---|---|
| `ai_news_daily.md` | AIニュース日次 | - | 毎日 | 準備中 |
| `ai_news_weekly.md` | AIニュース週次 | グローバル | 毎週月曜 | ✅ 完成 |
| `talent_mgmt_weekly.md` | 人材・スキル戦略グローバル動向（スキル＋タレント＋インテリジェンス統合） | 国内・海外 | 毎週月曜 | ✅ 完成 |

### 新しいテーマを追加するには

1. `prompts/` に新しいプロンプトファイル（`.md`）を追加
2. Claude Code Web のスケジュール設定でプロンプトを登録
3. 頻度・時間を設定

メール送信スクリプトは全テーマで共通のため、新規追加の際にコードの変更は不要です。

---

## ⚙️ 動作フロー

```
スケジュール起動（毎日 / 毎週）
    ↓
Claude Code Web が起動
    ↓
Web 検索 → 公開日検証 → 分類 → 整形（Claude が実行）
    ↓
/tmp/report.txt に本文を保存
    ↓
python send_daily_ai_news.py /tmp/report.txt
    ↓
HTML 変換 → SMTP 送信 → 指定アドレスに到着
```

---

## 📝 ライセンス

MIT License

---

## 👨‍💻 作成者

[@ykato27](https://github.com/ykato27)