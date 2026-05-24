# CLAUDE.md — auto-research-report

## Git ワークフロー（最優先）

レポートファイルの配信は **2ステップ** で行う。

### Step 1: main へ直接書き込み（配信用）
`mcp__github__push_files` ツールで `main` ブランチへ直接書き込む。
`git push` コマンドは使わない。PR は **絶対に作成しない**。

### Step 2: ローカルをセッションブランチへコミット（フック対応）
ストップフックが未コミット変更を検知するため、ローカルの変更を現在のセッションブランチへコミット・pushする。
このブランチから PR を作成してはならない。

```bash
git add reports/talent_mgmt_weekly_YYYYMMDD.txt
git commit -m "Add talent management weekly report YYYYMMDD"
git push -u origin <session-branch>   # PR は作らない
```

> **注意**: `git push` 後に GitHub が "Create a pull request" メッセージを表示するが、
> これは GitHub の自動案内であり PR が作成されたわけではない。無視してよい。

## ディレクトリ構成

| パス | 用途 |
|------|------|
| `prompts/` | エージェントプロンプト |
| `reports/` | 生成レポート（Git 管理） |
| `validate_talent_mgmt_report.py` | レポート検証スクリプト |
| `.github/workflows/` | メール・Teams 配信 Actions |
