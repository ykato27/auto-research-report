# 人材・スキル戦略グローバル動向 週次ニュースまとめ自動作成プロンプト

## 📌 プロンプト概要

スキルマネジメント・タレントマネジメント・タレントインテリジェンス分野のニュース収集エージェント。直近7日間に公開された国内・海外の動向を40～60件まとめ、GitHub Actions経由でメール配信する。

---

## ⚠️ 重要：Git操作の対象ブランチ

**このスクリプトは `main` ブランチへ push します。**

- ❌ ~~master~~ （使用しないこと）
- ✅ **main** （正式なブランチ）

---

## 📧 送信先アドレス確定（2026年3月24日版）

```
yuki.kato@skillnote.co.jp
keita.kawase@skillnote.co.jp
atsuhiko.okita@skillnote.co.jp
kotaro.kusunoki@skillnote.co.jp
```

**環境変数**: `RECIPIENT_EMAIL_TALENT_MGMT` に上記4名をカンマ区切りで設定

---

## STEP 0：事前準備

```bash
mkdir -p reports
```

---

## STEP 1：ニュース収集（Web Search × 10回実行）

### 検索対象期間の設定

- **対象期間**：直近7日間
- **実行日**：{date}（例：2026年3月24日）
- **期間表記**：{week_range}（例：March 18-24 2026）

### 検索クエリ（10回実行）

| # | クエリ | 備考 |
|---|--------|------|
| 1 | `"talent management skills strategy {week_range}"` | グローバル・スキル戦略 |
| 2 | `"skills framework competency model {week_range}"` | スキルフレームワーク |
| 3 | `"talent intelligence analytics platform {week_range}"` | タレント分析プラットフォーム |
| 4 | `"upskilling reskilling talent retention {week_range}"` | リスキリング・保持 |
| 5 | `"talent acquisition recruitment {week_range}"` | 採用トレンド |
| 6 | `"AI skills development learning {week_range}"` | AI活用・学習 |
| 7 | `"タレントマネジメント スキル {date_jp}"` | 国内トレンド（日本語） |
| 8 | `"人材戦略 採用 育成 {date_jp}"` | 人材戦略（日本語） |
| 9 | `"人材データ インテリジェンス 分析"` | 人材データ分析（日本語） |
| 10 | `"人材 スキル グローバル動向"` | グローバル人材（日本語） |

### 優先ソース一覧

#### 【国内】
- 日経新聞、日経HR、HRプロ、人事実務、人材関連企業ブログ
- 矢野経済研究所、リクルートワークス研究所
- カオナビ、Skillnote（製造業向け）

#### 【海外】
- **コンサルティング**：Mercer、Willis Towers Watson、Deloitte、Aon、McKinsey、BCG
- **HR業界**：SHRM、HR.com、HR Dive、Paychex、PeopleScout
- **タレント分析**：Eightfold AI、Metaview、TalentGuard、LinkedIn
- **ニュース**：TechCrunch、VentureBeat、World Economic Forum

#### 【除外すべきソース】
- ❌ crescendo.ai
- ❌ insightfulpost.com
- ❌ 常時更新型まとめサイト（公開日が判定不可）
- ❌ 公開日が明記されていないコンテンツ

---

## STEP 2：公開日検証（重要）

### 採用判定基準（週次版）

| 判定 | 条件 |
|------|------|
| ✅ **採用** | 「X hours ago」「1～6 days ago」「1 week ago」「this week」 |
| ✅ **採用（補助）** | URL内に直近7日の日付が含まれる（例：2026-03-18）|
| ❌ **除外** | 「2 weeks ago」以上、age不明かつURL判定不可 |

---

## STEP 3：分類と選定

### 記事分類カテゴリ（8分類）

各カテゴリあたり最大8件、合計40～60件を選定。同一週内の関連記事は最も重要な1件にまとめる。

| カテゴリ | 説明 | 件数目安 |
|---------|------|---------|
| 🏆 | スキルフレームワーク・タレント戦略 | 4～8件 |
| 📊 | スキル分析・タレントインテリジェンス | 4～8件 |
| 🎓 | 学習支援・採用・オンボーディング | 4～8件 |
| 🔬 | AI活用・スキル開発 | 4～8件 |
| 📈 | 従業員エンゲージメント・配置・保持 | 4～8件 |
| 💰 | 報酬・キャリアパス | 0～8件 |
| 🌍 | グローバル・ダイバーシティ・DEI | 4～8件 |
| 💼 | 企業導入事例・ベストプラクティス | 2～5件 |

---

## STEP 4：フォーマット整形

### プレーンテキスト形式（10,000文字以内）

```
──────────────────────────────
👥 人材・スキル戦略グローバル動向 週次ニュースまとめ（{YYYY/MM/DD}～{YYYY/MM/DD}）
──────────────────────────────

## 今週のサマリ

{スキル・タレント・人材戦略全体の週間トレンド・最重要動向を5～7行で記述。
国内・海外の動きを含める}

──────────────────────────────

【🏆 スキルフレームワーク・タレント戦略】

{スキル・タレント戦略の週間トレンドを3行で記述}

・{ニュース概要1～2行：戦略・施策＋背景}
（URL: {引用元}）

・{ニュース概要1～2行}
（URL: {引用元}）

【📊 スキル分析・タレントインテリジェンス】

{スキル・タレント分析・インテリジェンス技術の週間トレンドを3行で記述}

...（以下、他カテゴリも同様）

【🔍 Skillnote 注目点・示唆】

・{示唆1：今週の根拠トレンド → Skillnoteとの関連性 → 具体的アクション・示唆}

・{示唆2：今週の根拠トレンド → Skillnoteとの関連性 → 具体的アクション・示唆}

・{示唆3：今週の根拠トレンド → Skillnoteとの関連性 → 具体的アクション・示唆}

（最低3点、最大5点。必ず今週収集したニュースに根拠を持つ示唆のみ記載）

──────────────────────────────
今週のトピック数：{合計}件
──────────────────────────────
このメールはAIによる自動配信です。
```

### 記事要約の構造

各記事は **2行で「動き」「含意」を含める**：

```
・{企業/組織名：具体的なアクション・発表}。{背景・業界への含意}
（URL: {引用元}）
```

**例：**
```
・Talent Connects（300社以上が利用）がFusemachinesの Interview Agent を統合(3/18)。
AIによる構造化面接データ取得で、スキル客観評価と採用品質向上を実現。
（URL: https://www.globenewswire.com/news-release/2026/03/18/...）
```

---

## STEP 5：ファイル保存 & Git push

### 【重要】ブランチ確認チェックリスト

```bash
# ステップ5-1：ブランチ状態確認
git status
git branch -a

# 確認項目：
# ✓ 現在いるブランチは？
# ✓ 対象ブランチ「main」が存在するか？
# ✓ 「master」ブランチは不要か？
```

### 手順1：本文をファイルに保存

```bash
TODAY=$(date +%Y%m%d)
cat << 'NEWSEOF' > reports/talent_mgmt_weekly_${TODAY}.txt
{STEP 4で作成した本文をここに展開}
NEWSEOF
```

### 手順2：Git add & commit

```bash
TODAY=$(date +%Y%m%d)
git add reports/talent_mgmt_weekly_${TODAY}.txt
git commit -m "Add talent management weekly report ${TODAY}"
```

### 手順3：Git push to main（要確認）

```bash
# ⚠️ 重要：push前に必ず以下を確認

# 確認1：対象ブランチの確認
git log --oneline -3

# 確認2：変更ファイルの確認
git diff --cached --name-only

# 確認3：push実行（mainブランチへ）
git push origin HEAD:refs/heads/main
```

**エラーが発生した場合：**

```bash
# カレントブランチを確認
git branch -a
git status

# masterに誤ってpushしてしまった場合
git log --oneline -5  # 確認
git push origin :master  # リモートのmasterブランチを削除（要注意）
```

### 手順4：結果確認

```bash
# push成功の確認
git push が成功したことを確認する。
GitHub Actions が自動起動し、メール配信される。

# ログ確認
git log --oneline -3
```

---

## 品質保証ルール（17項目）

| # | ルール | 確認 |
|----|--------|------|
| 1 | Web Search機能のみ使用する | ✓ |
| 2 | 国内・海外英語ソースを対象 | ✓ |
| 3 | 直近7日間以内のニュースのみ対象 | ✓ |
| 4 | 信頼性の高い公式・報道ソースを優先 | ✓ |
| 5 | 各ニュースは固有名詞・日付・数値を明示 | ✓ |
| 6 | 重複や類似内容を排除 | ✓ |
| 7 | 全文は10,000文字以内 | ✓ |
| 8 | 日本語で記述 | ✓ |
| 9 | URLは「（URL: {引用元}）」形式で同じ行に記載 | ✓ |
| 10 | 「常時更新型まとめページ」のURLは使わない | ✓ |
| 11 | 40件に満たなくても検証済みのニュースだけで構成 | ✓ |
| 12 | 各記事要約は2行で「動き」「含意」を含める | ✓ |
| 13 | カテゴリサマリは3行で週間トレンドを記述 | ✓ |
| 14 | 同一週内の関連記事は最も重要な1件にまとめる | ✓ |
| 15 | Skillnote注目点は今週収集したニュースに根拠を持つ示唆のみ記述（創作禁止） | ✓ |
| 16 | Skillnote注目点は「製造業」「現場」「スキル管理」「デジタル化・技能継承」視点を含める | ✓ |
| 17 | Skillnote注目点の各示唆は「根拠トレンド→関連性→アクション」の構造で記述 | ✓ |

---

## 🔴 よくある失敗パターン（回避方法）

### ❌ パターン1：ブランチ指定の誤り

```bash
# 間違い
git push origin HEAD:refs/heads/master

# 正しい
git push origin HEAD:refs/heads/main
```

**防止方法**：
```bash
# push前に必ずブランチを確認
TARGET_BRANCH="main"
echo "Push target: ${TARGET_BRANCH}"
git push origin HEAD:refs/heads/${TARGET_BRANCH}
```

---

### ❌ パターン2：古いニュースを混在させる

**確認方法**：
- WebSearchのage情報で「2 weeks ago」以上を除外
- URL内の日付パターンで検証（例：2026-03-17以前は除外）

---

### ❌ パターン3：Skillnote示唆が今週ニュースに根拠がない

**チェック**：
- 各示唆について「どのニュース」が根拠か明記
- 推測・創作は絶対禁止
- 必ず「根拠トレンド→関連性→アクション」の3段構造

---

## 実行手順サマリ

```
1. mkdir -p reports
2. Web Search × 10回クエリ実行
3. 公開日検証（直近7日間のみ採用）
4. 8カテゴリに分類（40～60件選定）
5. プレーンテキスト形式で整形（10,000文字以内）
6. ブランチ確認 ← 重要！
7. git add & commit
8. git push origin HEAD:refs/heads/main ← mainを指定
9. GitHub Actionsトリガー確認
```

---

## 注記

- **このプロンプトは毎週実行される自動化タスク用**
- **STEP 5 の Git push は必ず `main` ブランチを対象にする**
- **不要な `master` ブランチは作成しない**
- **すべてのニュースは公開日を検証してから採用すること**
