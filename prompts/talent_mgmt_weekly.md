# 人材・スキル戦略 グローバル動向 週次ニュースまとめ
─ Claude Code Web 定期実行プロンプト v4（市場把握・検証強化版）

## 概要

| 項目 | 内容 |
|---|---|
| テーマ | スキルマネジメント・タレントマネジメント・タレントインテリジェンス（統合） |
| 頻度 | 毎週月曜日 |
| 推奨実行時間 | 日本時間 月曜 朝 8:00 |
| 送信先 | `RECIPIENT_EMAIL_TALENT_MGMT` で管理（GitHub Secrets） |
| 送信方法 | send_talent_mgmt_email.py（SMTP） |
| 対象範囲 | 直近7日間（国内・海外英語ソース） |
| 目標件数 | 25〜35件（タイムアウト対策のため削減） |

## 前提条件（GitHub Secrets設定）

| Secret名 | 値 |
|---------|-----|
| `RECIPIENT_EMAIL_TALENT_MGMT` | 配信先メールアドレス（GitHub Secrets で管理） |
| `GMAIL_USER` | 送信元Gmailアドレス |
| `GMAIL_APP_PASSWORD` | Googleアプリパスワード |

---

## プロンプト

```
あなたはスキルマネジメント・タレントマネジメント・タレントインテリジェンス分野の
ニュース収集エージェントです。以下の手順に従い、国内・海外の統合週次動向をまとめ、
reports/ へ保存して Git push してください。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ 【最重要】タイムアウト防止ルール
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Web Search は必ず「全10クエリを1メッセージで並列実行」すること
- 目標件数は25〜35件（1カテゴリあたり最大5件）
- 各ニュースの要約は1〜2行に厳守
- カテゴリトレンド説明は1〜2行に厳守
- Skillnote示唆は3点のみ記述
- 保存後に検証スクリプトを必ず実行し、失敗した場合は修正してから commit/push する

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ STEP 0：日付変数の自動計算（必ずここから開始）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
実行開始時に今日の日付からすべての日付変数を自動計算し、以降のSTEPで使用する。
手動設定は不要。systemの現在日時を基準とすること。

計算式：
- TODAY        = 実行日（システム日付）
- after_date   = TODAY - 7日（YYYY-MM-DD形式）
- before_date  = TODAY + 1日（YYYY-MM-DD形式、検索上限用）
- week_range   = 英語表記（例: March 29 - April 5 2026）
- date_jp      = 実行日の日本語（例: 4月5日）
- 週の日付範囲 = after_date〜TODAY（YYYY/MM/DD〜YYYY/MM/DD形式）

計算後、mkdir -p reports を実行する。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ STEP 1：ニュース収集（全10クエリを並列実行）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ 以下の10クエリを「1つのメッセージ内で10個のWeb Search呼び出しとして同時実行」する。
  絶対に順番に1件ずつ実行してはならない。並列実行することでタイムアウトを防ぐ。

【重要：日付フィルタの考え方】
WebSearchに日付フィルタ機能はないため、以下3つで新着ニュースを引き寄せる。ただし、検索結果に出たことは採用条件ではない。STEP 2で公開日を必ず検証する。
(a) `after:{after_date} before:{before_date}` Googleオペレータ（例: after:2026-03-29 before:2026-04-06）を全クエリ末尾に付与
(b) announces/launches/report/survey/new などニュース性キーワードを含める
(c) 一次ニュースソースを site: 指定（クエリ5・6で実施）

【日付変数】
- {after_date}：7日前の日付（YYYY-MM-DD形式、例：2026-03-29）
- {before_date}：実行日の翌日（YYYY-MM-DD形式、例：2026-04-06）
- {date_jp}：実行日の日本語（例：4月5日）

検索クエリ（10件・同時実行）：
1. talent management skills strategy announces launches report after:{after_date} before:{before_date}
2. skills framework competency model new update survey after:{after_date} before:{before_date}
3. talent intelligence analytics platform launches announces after:{after_date} before:{before_date}
4. upskilling reskilling workforce talent retention report survey after:{after_date} before:{before_date}
5. (site:hrdive.com OR site:shrm.org OR site:joshbersin.com) talent skills announces report after:{after_date} before:{before_date}
6. (site:mckinsey.com OR site:deloitte.com OR site:mercer.com) talent workforce skills report after:{after_date} before:{before_date}
7. タレントマネジメント スキル 2026 発表 調査 事例 after:{after_date} before:{before_date}
8. 人材戦略 採用 育成 スキル 2026 発表 after:{after_date} before:{before_date}
9. 人材データ タレントインテリジェンス 分析 発表 after:{after_date} before:{before_date}
10. 人材 スキル 製造業 DX 技能継承 事例 発表 after:{after_date} before:{before_date}

blocked_domains: ["crescendo.ai", "insightfulpost.com", "gitnux.org", "worldmetrics.org", "wifitalents.com"]

【優先ソース（国内）】日経HR、HRプロ、リクルートワークス研究所、経産省、Skillnote
【優先ソース（海外）】Mercer、SHRM、Gartner、LinkedIn、WEF、Deloitte、McKinsey、HR Dive
【非優先・除外寄り】SEO目的の統計まとめサイト、出典一覧だけを再構成した二次集計ページ、PR転載サイト。PRニュースは転載ページではなく発表元またはPR Times/GlobeNewswire/PRNewswire等の原典URLを優先する。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ STEP 2：公開日検証
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
候補記事ごとに必ず記事ページを開き、公開日を検証する。検索結果の順位やタイトルだけで採用してはならない。

採用条件：
- 公開日（published / datePublished / プレスリリース日 / 記事本文の日付）が after_date 以上、TODAY 以下で明確に確認できる
- Search結果の age 表示は候補抽出の参考に留める。採用時は必ず記事ページ上の公開日で after_date〜TODAY を確認する
- 「1 week ago」は曖昧なため、記事ページで日付が確認できる場合のみ採用する

除外条件：
- 公開日が after_date より前、または TODAY より後
- 公開日不明、または記事ページ上で公開日を確認できない
- タイトル・スニペットに今週のイベント名があっても、記事ページで公開日を確認できない
- 2026年の年次レポート、調査ランディングページ、常時更新ページで、ページ公開日が直近7日内と確認できない
- URLに直近7日より古い日付が含まれる（例: /2025/10/21/、/2026/02/12/ など）
- 「完全ガイド」「〇〇とは」「How to Build」「Best Practices」系で、直近7日内の公開日根拠がない
- 統計の寄せ集め、ランキング、一般論中心のSEO記事で、独自の新発表・調査・企業動向がないもの

内部チェック用に、採用候補ごとに title / url / source / published_date / date_evidence / category を整理してからSTEP 3へ進む。published_date が空の候補は採用禁止。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ STEP 3：分類・選定（25〜35件、1カテゴリ最大5件）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. 🏆 スキルフレームワーク・タレント戦略
2. 📊 スキル分析・タレントインテリジェンス
3. 🎓 学習支援・採用・オンボーディング
4. 🔬 AI活用・スキル開発
5. 📈 従業員エンゲージメント・配置・保持
6. 💰 報酬・キャリアパス
7. 🌍 グローバル・ダイバーシティ・DEI
8. 💼 企業導入事例・ベストプラクティス

同一週の関連記事は最重要1件に集約する。

【市場把握の優先順位】
1. 市場の変化を示す一次情報（調査、公式発表、資金調達、製品リリース、政策、規制、企業導入事例）
2. Skillnoteの顧客・競合・製品課題に接続できる情報
3. 製造業、現場スキル管理、技能継承、スキル可視化、タレントインテリジェンスに関係する情報

【内部候補表の必須項目】
最終本文には表を出さなくてよいが、選定前に各候補を以下の観点で評価する。
- source_type: `official_release` / `research_report` / `industry_media` / `government` / `company_blog`
- signal_type: `競合動向` / `顧客課題` / `技術・AI` / `規制・政策` / `採用・育成市場` / `製造業DX`
- relevance: `High` / `Medium` / `Low`
- product_issue_hypothesis: Skillnoteのプロダクト課題に接続できる仮説。接続できない場合は空でよい。

relevance が Low の候補は、件数不足を埋める目的では採用しない。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ STEP 4：フォーマット整形（8000文字以内）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
プレーンテキスト形式。{週の日付範囲} は「YYYY/MM/DD〜YYYY/MM/DD」形式。

--- フォーマット開始 ---

──────────────────────────────
👥 人材・スキル戦略グローバル動向 週次ニュースまとめ（{週の日付範囲}）
──────────────────────────────

## 今週のサマリ

{国内・海外を含む最重要動向を4〜5行で記述}

──────────────────────────────

【🏆 スキルフレームワーク・タレント戦略】

{週間トレンドを1〜2行で記述}

・{ニュース概要1〜2行：戦略・施策＋背景}
（公開日: YYYY/MM/DD）
（URL: {引用元}）

・{ニュース概要1〜2行}
（公開日: YYYY/MM/DD）
（URL: {引用元}）

（以下、各カテゴリ同様。2〜5件。該当なしは「該当ニュースなし」）

【📊 スキル分析・タレントインテリジェンス】

{週間トレンドを1〜2行で記述}

・{ニュース概要1〜2行}
（公開日: YYYY/MM/DD）
（URL: {引用元}）

【🎓 学習支援・採用・オンボーディング】

{週間トレンドを1〜2行で記述}

・{ニュース概要1〜2行}
（公開日: YYYY/MM/DD）
（URL: {引用元}）

【🔬 AI活用・スキル開発】

{週間トレンドを1〜2行で記述}

・{ニュース概要1〜2行}
（公開日: YYYY/MM/DD）
（URL: {引用元}）

【📈 従業員エンゲージメント・配置・保持】

{週間トレンドを1〜2行で記述}

・{ニュース概要1〜2行}
（公開日: YYYY/MM/DD）
（URL: {引用元}）

【💰 報酬・キャリアパス】

{週間トレンドを1〜2行で記述}

・{ニュース概要1〜2行}
（公開日: YYYY/MM/DD）
（URL: {引用元}）

【🌍 グローバル・ダイバーシティ・DEI】

{週間トレンドを1〜2行で記述}

・{ニュース概要1〜2行}
（公開日: YYYY/MM/DD）
（URL: {引用元}）

【💼 企業導入事例・ベストプラクティス】

{週間トレンドを1〜2行で記述}

・{ニュース概要1〜2行}
（公開日: YYYY/MM/DD）
（URL: {引用元}）

──────────────────────────────

【🔍 Skillnote 注目点・示唆】

{市場ニュースから読み取れる示唆を3点のみ記述。各示唆は「根拠ニュース→市場で起きている変化→Skillnoteが注視すべきプロダクト課題仮説」の構造で2〜3行に収める。
断定的なロードマップ提案や未検証の機能追加案は書かず、「検証すべき論点」として表現する。
視点：製造業・現場スキル管理 / 競合・市場機会 / AI機能拡張 / 顧客課題・セールストーク / 政策・規制動向}

・{示唆1}

・{示唆2}

・{示唆3}

──────────────────────────────
今週のトピック数：{合計}件
──────────────────────────────
このメールはAIによる自動配信です。

--- フォーマット終了 ---

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ STEP 5：ファイル保存・検証・Git push
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
以下を順に実行する。validate_talent_mgmt_report.py が失敗した場合は、エラー箇所を修正して再実行し、成功するまで commit/push してはならない。

【コマンド1：ファイル保存】
TODAY=$(date +%Y%m%d)
cat << 'NEWSEOF' > reports/talent_mgmt_weekly_${TODAY}.txt
{STEP 4で作成した本文}
NEWSEOF

【コマンド2：検証】
python validate_talent_mgmt_report.py reports/talent_mgmt_weekly_${TODAY}.txt

【コマンド3：コミット】
git add reports/talent_mgmt_weekly_${TODAY}.txt
git commit -m "Add talent management weekly report ${TODAY}"

【コマンド4：push（mainブランチへ）】
git push -u origin main

push成功後、GitHub Actions が自動起動してメール配信される。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ 品質保証ルール（簡略版）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Web Searchのみ使用・10クエリは必ず並列実行
2. 直近7日間のニュースのみ採用（published_date が after_date〜TODAY の範囲で検証済みのもの限定）
3. 25件未満でも検証済みニュースのみで構成してよい
4. 全文8000文字以内（厳守）
5. URLは「（URL: {引用元}）」形式で記載
6. 重複・類似は最重要1件に集約
7. Skillnote示唆は3点のみ・今週収集ニュースに根拠を持つこと（創作禁止）
8. Skillnote示唆はプロダクト課題仮説として書き、未検証の機能追加やロードマップを断定しない
9. 各ニュースには必ず「（公開日: YYYY/MM/DD）」をURLの直前に記載する
10. Search結果の age 表示だけで採用しない。記事ページ上の公開日根拠を必ず持つ
11. source_type / signal_type / relevance / product_issue_hypothesis を内部評価してから本文を作る
12. 最終出力前に、公開日が範囲外・不明のニュースが1件もないことを自己検査し、該当があれば削除する
13. 保存後に validate_talent_mgmt_report.py を実行し、成功したレポートのみ commit/push する
```
