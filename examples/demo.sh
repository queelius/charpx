#!/bin/bash
# csvcat and datacat demo script
# Run from the repo root: bash examples/demo.sh

set -e
DIR="$(cd "$(dirname "$0")" && pwd)"

section() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  $1"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
}

# ── csvcat examples ──────────────────────────────────────────

section "csvcat: Pretty-print CSV"
csvcat "$DIR/sample.csv"

section "csvcat: Select columns + sort"
csvcat "$DIR/sample.csv" --cols name,score,department --sort score --desc

section "csvcat: First 5 rows"
csvcat "$DIR/sample.csv" --head 5

section "csvcat: TSV file"
csvcat "$DIR/sales.tsv"

section "csvcat: Cycle-color mode"
csvcat "$DIR/sample.csv" --cycle-color

section "csvcat: Sparkline of scores"
csvcat "$DIR/sample.csv" --spark score -H 8

section "csvcat: Bar chart of departments"
csvcat "$DIR/sample.csv" --bar department -H 6

section "csvcat: Histogram of ages"
csvcat "$DIR/sample.csv" --histogram age -H 8

# ── datacat examples ─────────────────────────────────────────

section "datacat: Pretty-print JSON"
datacat "$DIR/config.json"

section "datacat: Tree view"
datacat "$DIR/config.json" --tree

section "datacat: JSONL as table"
datacat "$DIR/metrics.jsonl" --table

section "datacat: JSONL table with cycle-color"
datacat "$DIR/metrics.jsonl" --table --cycle-color

section "datacat: Head 5 records"
datacat "$DIR/metrics.jsonl" --head 5 --table

section "datacat: Sparkline of latency"
datacat "$DIR/metrics.jsonl" --spark .latency -H 8

section "datacat: Bar chart of status"
datacat "$DIR/metrics.jsonl" --bar .status -H 6

section "datacat: Bar chart of regions"
datacat "$DIR/metrics.jsonl" --bar .region -H 6

section "datacat: Histogram of latency"
datacat "$DIR/metrics.jsonl" --histogram .latency -H 8

echo ""
echo "Done!"
