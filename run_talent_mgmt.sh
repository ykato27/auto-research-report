#!/usr/bin/env bash
# タレントマネジメント週次レポート生成スクリプト
# Phase 1（Python）→ Phase 2+3（Claude Code）の橋渡し役

set -e

DAYS=${1:-7}
OUTPUT="data/raw_news.json"

echo "============================================================"
echo " タレントマネジメント週次レポート生成"
echo " 対象期間: 直近${DAYS}日間"
echo "============================================================"
echo ""

# ── Phase 1: Python でニュース収集（トークン消費ゼロ） ──────────
echo "[Phase 1] RSS ニュース収集（Python）..."
python src/collect_news.py --days "$DAYS" --output "$OUTPUT"

# ニュースが0件なら Claude Code を起動しない（コスト0で終了）
NEWS_COUNT=$(python -c "import json; d=json.load(open('$OUTPUT')); print(d['total_count'])")
if [ "$NEWS_COUNT" -eq 0 ]; then
    echo ""
    echo "INFO: 収集記事数が0件のため処理を終了します（Claude Code 未起動）"
    exit 0
fi

echo ""
echo "✓ ${NEWS_COUNT} 件収集完了 → ${OUTPUT}"
echo ""

# ── Phase 2+3: Claude Code でレポート生成（判断・整形・push） ───
echo "[Phase 2+3] Claude Code でレポート生成..."
claude \
    --print \
    --allowedTools "Read,Bash,Write,Glob" \
    "$(cat prompts/talent_mgmt_phase2.md)"

echo ""
echo "============================================================"
echo " 完了"
echo "============================================================"
