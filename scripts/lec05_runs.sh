#!/usr/bin/env bash
# 第5回: 演習と宿題（発展）の実行をまとめて行い、出力を lectures/05/runs/ に保存する。
# 使い方（Codespaces で）: bash scripts/lec05_runs.sh
#   一部だけやり直す: bash scripts/lec05_runs.sh q2_hybrid q3_vector
# 無料枠のレート制限を避けるため、実行の間に WAIT 秒待つ（既定 30 秒）。
set -u
cd "$(dirname "$0")/.."
OUT=lectures/05/runs
WAIT="${WAIT:-30}"
mkdir -p "$OUT"

Q1='第2回の説明では、LoRAは何を固定し何を学習しますか？ QLoRAは何を加えますか？'
Q2='第3回の例では、コンパクションとセッションをまたぐメモリはどう違いますか。日々のメモはすべて長期メモリに入りますか'
Q3='今回作ったRAGの実測平均応答時間と正答率を教えてください'

# 名前 / 質問 / 方式（空 = 通常のベクトル検索）
RUNS=(
  "q1_full|$Q1|--full-context"
  "q1_vector|$Q1|"
  "q1_tree|$Q1|--tree"
  "q1_graph|$Q1|--graph"
  "q1_hybrid|$Q1|--hybrid"
  "q2_vector|$Q2|"
  "q2_tree|$Q2|--tree"
  "q2_graph|$Q2|--graph"
  "q2_hybrid|$Q2|--hybrid"
  "q3_vector|$Q3|"
  "q3_graph|$Q3|--graph"
  "q3_hybrid|$Q3|--hybrid"
)

{ echo "date: $(date -Is)"; echo "commit: $(git rev-parse --short HEAD)"; echo "model: ${AIE_MODEL:-gemini-3.5-flash-lite (default)}"; } > "$OUT/_meta.txt"

first=1
for run in "${RUNS[@]}"; do
  IFS='|' read -r name question mode <<< "$run"
  if [ "$#" -gt 0 ] && [[ ! " $* " =~ " $name " ]]; then continue; fi
  [ "$first" -eq 1 ] || sleep "$WAIT"
  first=0
  echo "=== $name ${mode:-(vector)}"
  # shellcheck disable=SC2086
  uv run python -m app.agent $mode --trace "$question" > "$OUT/$name.txt" 2>&1
  tail -3 "$OUT/$name.txt"
done
echo "保存先: $OUT/  →  git add $OUT && git commit -m 'Lecture 5 runs' && git push"
