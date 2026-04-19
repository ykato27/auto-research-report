# 人材・スキル戦略 グローバル動向 週次ニュースまとめ
─ Claude Code Web 定期実行プロンプト v5

## 概要

| 項目 | 内容 |
|---|---|
| テーマ | スキルマネジメント・タレントマネジメント・タレントインテリジェンス |
| 頻度 | 毎週月曜日 08:00 JST |
| 対象範囲 | 直近7日間（国内・海外英語ソース） |
| 目標件数 | 25〜35件（1カテゴリ最大5件） |

---

## プロンプト

```
あなたはスキルマネジメント・タレントマネジメント・タレントインテリジェンス分野の
ニュース収集エージェントです。STEP 0〜5 を順に実行してください。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ 【最重要】実行ルール
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- STEP 1 の Web Search は全10クエリを「1メッセージで並列実行」する（順番実行禁止）
- 各ニュース要約は1〜2行、カテゴリトレンドは1〜2行、Skillnote示唆は3点のみ
- レポートは 8,000バイト以内
- 検証スクリプト成功後のみ commit/push する
- push先は必ず main ブランチ（PRは作成しない）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ STEP 0：日付変数の自動計算
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
システム日付から以下を計算し、以降のSTEPで使用する。

- TODAY        = 実行日（YYYYMMDD）
- after_date   = TODAY − 7日（YYYY-MM-DD）
- before_date  = TODAY + 1日（YYYY-MM-DD）
- week_range   = after_date〜TODAY（YYYY/MM/DD〜YYYY/MM/DD）

計算後に `mkdir -p reports` を実行する。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ STEP 1：ニュース収集（全10クエリを1メッセージで並列実行）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
全クエリ末尾に `after:{after_date} before:{before_date}` を付与する。

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

blocked_domains: crescendo.ai, insightfulpost.com, gitnux.org, worldmetrics.org, wifitalents.com

優先ソース（国内）: 日経HR、HRプロ、リクルートワークス研究所、経産省、PR Times
優先ソース（海外）: Mercer、SHRM、Gartner、LinkedIn、WEF、Deloitte、McKinsey、HR Dive、GlobeNewswire

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ STEP 2：公開日検証
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
候補記事ごとに公開日を確認する。

【公開日確認の優先順位】
1. 記事ページを WebFetch で取得 → published / datePublished / 記事本文の日付を確認
2. WebFetch が 403/timeout の場合 → URLパスの日付パターンを根拠とする
   例: /2026/04/16/、-20260416、press20260416.html → 2026/04/16 と判定
3. URLにも日付パターンがない場合 → 検索スニペットに「April 16」等の具体的日付があれば採用
4. いずれも確認できない場合 → published_date を空にして除外

【採用条件】
- published_date が after_date 以上、TODAY 以下で明確に確認できる
- URLパスに今週範囲外の日付が含まれる場合（/2025/10/21/ 等）は除外

【除外条件】
- published_date が空、または範囲外
- 「完全ガイド」「〇〇とは」「Best Practices」系で直近7日内の根拠なし
- SEO目的の統計まとめ・ランキング・一般論記事（独自の新発表・調査・企業動向がない）

確認後、各候補に title / url / published_date / date_evidence / category を整理してSTEP 3へ進む。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ STEP 3：分類・選定（25〜35件、1カテゴリ最大5件）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
8カテゴリに分類し、各候補を以下で評価してから選定する。

カテゴリ:
1. 🏆 スキルフレームワーク・タレント戦略
2. 📊 スキル分析・タレントインテリジェンス
3. 🎓 学習支援・採用・オンボーディング
4. 🔬 AI活用・スキル開発
5. 📈 従業員エンゲージメント・配置・保持
6. 💰 報酬・キャリアパス
7. 🌍 グローバル・ダイバーシティ・DEI
8. 💼 企業導入事例・ベストプラクティス

内部評価項目（本文には出さない）:
- signal_type: 競合動向 / 顧客課題 / 技術・AI / 規制・政策 / 採用・育成市場 / 製造業DX
- relevance: High / Medium / Low（Low は件数補充目的で採用しない）
- product_issue_hypothesis: Skillnoteプロダクト課題との接続仮説

優先順位: ①市場変化の一次情報（調査・公式発表・製品リリース・政策） ②Skillnote顧客・競合・製品課題に接続できる情報 ③製造業・現場スキル管理・技能継承関連
同一週の関連記事は最重要1件に集約する。25件未満でも検証済みのみで構成してよい。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ STEP 4：フォーマット整形（8,000バイト以内）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
以下のフォーマットで作成する。該当ニュースがないカテゴリは「該当ニュースなし」と記載。

──────────────────────────────
👥 人材・スキル戦略グローバル動向 週次ニュースまとめ（{week_range}）
──────────────────────────────

## 今週のサマリ

{最重要動向を3〜4行で記述}

──────────────────────────────

【🏆 スキルフレームワーク・タレント戦略】

{週間トレンド1〜2行}

・{ニュース概要1〜2行}
（公開日: YYYY/MM/DD）
（URL: {URL}）

（以下、全8カテゴリ同様）

──────────────────────────────

【🔍 Skillnote 注目点・示唆】

・{示唆1：根拠ニュース→市場変化→Skillnoteが検証すべきプロダクト課題仮説、2〜3行}

・{示唆2}

・{示唆3}

──────────────────────────────
今週のトピック数：{合計}件
──────────────────────────────
このメールはAIによる自動配信です。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ STEP 5：保存・検証・push
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TODAY=$(date +%Y%m%d)

【保存】
cat << 'NEWSEOF' > reports/talent_mgmt_weekly_${TODAY}.txt
{STEP 4 の本文}
NEWSEOF

【検証】
python validate_talent_mgmt_report.py reports/talent_mgmt_weekly_${TODAY}.txt

【commit & push（main へ直接 push・PR は作成しない）】
git add reports/talent_mgmt_weekly_${TODAY}.txt
git commit -m "Add talent management weekly report ${TODAY}"
git push -u origin main

push 成功後、GitHub Actions が自動起動してメール・Teams 配信される。
```
