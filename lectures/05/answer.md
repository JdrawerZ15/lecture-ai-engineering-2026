# 第5回 解答

> **Status:** everything that does not call Gemini (retrieval structure, Tree candidates, the new `--hybrid` retrieval, an offline retrieval check) was run and verified locally. The answer-generation runs need `GEMINI_API_KEY` in Codespaces: `bash scripts/lec05_runs.sh` saves every `--trace` output to `lectures/05/runs/`. Cells marked **未実行** are filled from those files only. No value below is estimated.

## 演習

- 回答モデル（実行時の`[model]`）：`gemini-3.5-flash-lite` (default; recorded in `lectures/05/runs/_meta.txt`) — **未実行**
- 比較した質問：Q1 「第2回の説明では、LoRAは何を固定し何を学習しますか？ QLoRAは何を加えますか？」 (evidence: 第2回・PDF p.52; p.51 also supports QLoRA = LoRA + 4bit)
- 対象資料（全文投入と他の方式で範囲が違う点も記録）：
  - Vector / Tree / Graph: `RAG_DOCUMENT_IDS = lec01-main, lec02-main, lec03-main` → 214 pages (checked: `SELECT count(*) FROM chunks` = 214).
  - Full text: all 9 documents in `lectures.json` (438 pages), **227,911 characters** of prompt (`len(get_all_materials())`). This includes `lec05-main` (基盤モデルとデータ, 79 pages) and the 4 exercise documents, which search cannot see. So full text is not a same-scope comparison.

### 各方式の結果

| 方式 | 回答の要点・正しさ | 引用ページと根拠 | 時間（秒） | 入力／出力トークン数 | モデル応答回数 | 生成API推定費用（USD） |
|---|---|---|---|---|---|---|
| 全文投入 | 未実行 | 未実行 | 未実行 | 未実行 | 未実行 | 未実行 |
| ベクトル検索 | 未実行 | 未実行 | 未実行 | 未実行 | 未実行 | 未実行 |
| Tree | 未実行 | 未実行 | 未実行 | 未実行 | 未実行 | 未実行 |
| Graph | 未実行 | 未実行 | 未実行 | 未実行 | 未実行 | 未実行 |

<!-- 未実行・算定不可の場合は、その旨を書いてください。質問を追加した場合は、質問ごとに表を分けてください。 -->

For reference only (not my runs), the instructor's slide 21 shows full text 117,025 / 247 tokens in 4.41 s (partial, p.51–52); vector 3,028 / 168 in 3.74 s; Tree 9,229 / 297 in 7.64 s; Graph 5,771 / 212 in 3.12 s.

- 検索だけを実行して見つかったページと、その本文で確認できたこと：
  - `uv run python -m app.retrieval "LoRA QLoRA 違い"` needs the query embedding (Gemini) — **未実行**.
  - Without the API I checked the evidence page itself (`lec02-main-p052` in `lectures.json`). It says the original weights W are **frozen**, only the small matrices A and B (low-rank "delta") are **trained**, and QLoRA additionally **compresses W to 4bit** (about 1/4; ~4GB for 7B). p.51 repeats this in one line each (LoRA: freeze body, update small add-on; QLoRA: also 4bit).
- `--trace`で見えたツール呼び出し（ツール名・引数・回数、Treeでたどった目次など）：
  - Model-chosen calls are **未実行**. What Tree *can* show is fixed by the data, so I checked it with `browse_tree()` directly (no API):
    - Path to the evidence: lecture list → `lec02-main` (11 children) → chapter `lec02-main-s045` 「選んだモデルを、いつ・どう直すか」 (18 pages) → `lec02-main-p052`. At least 4 `browse_tree` calls.
    - In that chapter, the "first sentence" shown for p.046–p.055 and p.058 is the progress header **「4/4 選んだモデルを、いつ・どう直すか」** for every page. The model can only choose by title.
  - I also changed `print_trace` so that the search tools list every page they returned (`[全文・入口]`, `[全文・追加]`, `[要約のみ]` + distance / hops). The default trace cut the result at 120 characters, which hid which pages Graph added.
- 取得した情報が足りなかった例、取得できたのに回答へ使えなかった例：
  - From the offline check (Homework section): for the multi-page question, **Graph misses 第3回 p.13 in 3 of 4 probes**. Graph keeps only 3 vector seeds and fills the other 7 slots with structural neighbours (p.36–p.42, p.19, p.51, p.58), so p.13 never enters the result. Plain vector top-5 kept it in 3 of 4.
  - Answer-side failures: **未実行**.
- 今回の用途に採用したい方式と、その理由・比較条件の限界：
  - Provisional (retrieval side only): plain vector search for single-page questions, and a seed + preview design (`--hybrid`, Homework) for multi-page ones. Final choice depends on the generation runs.
  - Limits: full text has a wider scope (438 vs 214 pages, incl. Lecture 5). One run per method, and temperature/order effects are not controlled.
- 気づき・疑問：
  - **Tree is only as good as its candidate text.** 102 of the 214 searchable pages give a useless preview: 62/71 in Lecture 3 just repeat the title, and 40/70 in Lecture 2 are the 「N/4 章名」 progress header. Tree navigation then degrades to choosing by title.
  - **Cross-chapter evidence breaks Tree's assumption.** Lecture 3's memory topic is split: p.13 「メモリ」 sits in *Part 2 エージェントを組み立てる*, while p.38–p.41 are in *Part 6 メモリ*. A Tree agent that opens only the 「メモリ」 chapter never sees p.13.
  - **"Related ≠ contains the answer" in numbers:** Graph returns 2.2–2.6× more text than vector search for the same probe (e.g. 8,915 vs 3,460 characters), and the extra pages did not include the missing evidence.
  - Question: the search DB does not include Lecture 5's own slides (`lec05-main`), while full text does. Is that on purpose, to show the scope effect?

## 宿題

- 取り組んだレベル：**発展** — a combined retrieval method, `--hybrid` (vector × Graph × Tree)

- やったこと（変更したファイル・設定・処理、または設計した取得方法）：
  - **Target question.** Q2 (multi-page, cross-chapter): 「第3回の例では、コンパクションとセッションをまたぐメモリはどう違いますか。日々のメモはすべて長期メモリに入りますか」. Evidence checked first in `lectures.json`:
    - 第3回 p.39: compaction (summarise old history, same session) vs memory tool / auto memory (outside store, across sessions)
    - 第3回 p.40: OpenClaw daily notes → nightly review → only items above a threshold move to `MEMORY.md`; one-off research stays in the daily notes
    - 第3回 p.13: the basic idea (write out to an external store, read back into a new context)

    Controls: Q1 (single page, p.52) and Q3 「今回作ったRAGの実測平均応答時間と正答率」 (not in the materials).
  - **Design** (`app/retrieval.py: search_hybrid`, tools `search_hybrid` + `read_page`, mode `--hybrid`):
    1. **Entry = vector search.** Top `HYBRID_SEEDS = 3` pages, full text (same as Graph's entry).
    2. **Candidates = graph neighbourhood.** `next_page` and `mentions` edges, up to `HYBRID_HOPS = 2` hops (same relations and hop count as `--graph`).
    3. **Re-rank by the question.** Each candidate's distance comes from the page embedding **already stored** in `index.sqlite3` (`vec_distance_cosine` on just those `page_id`s). No extra embedding calls; the only API cost is the one query embedding.
    4. **Return previews, not full text** (Tree's idea). The top `HYBRID_PREVIEWS = 7` candidates come back as section, title, distance, `via` (the term or page that linked them) and one informative line. `preview_line()` skips lines that repeat the title, the 「N/4」 progress header and 出典/© lines.
    5. **Fetch on demand.** The model reads a candidate's full text with `read_page(page_id)`. `HYBRID_INSTRUCTIONS` asks it to check that every part of the question has a supporting page before answering.
  - **Why this shape:**
    - Graph's weakness is that expansion ignores the question and costs 10 full pages.
    - Tree's weakness is weak candidate text and many calls.
    - Vector's weakness is that 5 full pages are chosen by distance alone, with no view of what is nearby.
    - The hybrid keeps 3 full pages and turns the rest into a cheap "map" ranked by relevance.
  - Tests: `tests/test_hybrid.py`, 4 tests, no API (stored page embeddings stand in for the query). `uv run pytest -q` → 21 passed.

- 比較した質問と、固定した条件（モデル・対象資料など）：Q1–Q3 above. Same model (`AIE_MODEL` default), same 214 pages, same index, one run each, 30 s between runs (`scripts/lec05_runs.sh`). Compared methods: vector (Basic RAG), Graph and `--hybrid`; Tree also for Q1/Q2.

- 結果（変更前後の回答・根拠、`--trace`の出力、時間・トークン数・生成API推定費用など）：

  **A. Retrieval only, offline (done).** I can't embed the real questions without the API. Instead, each probe uses a **stored page embedding** as the query vector: the evidence page itself, or the normalised mean of the pages the question is about. This tests *what each method returns around the right spot*. It does not test whether the real question lands there. Script: `uv run python -m scripts.lec05_proxy_eval`.

  | Question | Probe | Vector top-5 (full text) | Graph 3+7 (full text) | Hybrid full text | Hybrid full + preview | Returned characters V / G / H |
  |---|---|---|---|---|---|---|
  | Q1 | p.52 | 1/1 | 1/1 | 1/1 | 1/1 | 4,208 / 9,272 / 4,169 |
  | Q2 | mean(p.39, p.40) | 3/3 | 2/3 (no p.13) | 2/3 | **3/3** | 3,460 / 8,915 / 3,584 |
  | Q2 | p.13 | 3/3 | 3/3 | 2/3 | **3/3** | 3,166 / 7,227 / 3,333 |
  | Q2 | p.39 | 2/3 (no p.13) | 2/3 (no p.13) | 2/3 | **3/3** | 3,731 / 8,890 / 3,634 |
  | Q2 | p.40 | 3/3 | 2/3 (no p.13) | 2/3 | **3/3** | 3,441 / 8,896 / 3,559 |

  - The hybrid always has all evidence pages in front of the model, with about the same characters as vector and 40–45% of Graph. In every Q2 probe, the evidence page missing from the full-text seeds arrives as a preview. In 3 probes this is p.13 (「コンテキストは有限である。」, linked via the term メモリ). In the p.13 probe it is p.40 (「毎晩過去のやり取りを読み直し、残すものだけを長期メモリに移す。」, the next page after seed p.39).
  - **Caveat:** that page is only a preview, so the answer is complete only if the model calls `read_page`. That is exactly what the generation run has to show.

  **B. With the model (未実行 — fill from `lectures/05/runs/`).**

  | Q | Method | Answer correct? | Cited pages | Tool calls | Time (s) | In / out tokens | Requests | Est. USD |
  |---|---|---|---|---|---|---|---|---|
  | Q1 | vector | | | | | | | |
  | Q1 | hybrid | | | | | | | |
  | Q2 | vector | | | | | | | |
  | Q2 | tree | | | | | | | |
  | Q2 | graph | | | | | | | |
  | Q2 | hybrid | | | | | | | |
  | Q3 | vector | | | | | | | |
  | Q3 | graph | | | | | | | |
  | Q3 | hybrid | | | | | | | |

- 改善した例と、残る失敗・制約：
  - Improved (retrieval): Q2's p.13 is visible in every probe, while Graph drops it in 3/4. Output is 40–45% of Graph's size.
  - Remaining weak points I can already see:
    - **Previews of divider pages carry no content** (「Part 6」, 「演習」, 「まとめ」, 「この 15 分の芯」). They still take preview slots.
    - **High-degree terms widen the pool.** AIエージェント has 104 pages and ツール 91, so distance re-ranking does all the work. Without it, this would be Graph's noise problem again.
    - **Only one probe type.** Real questions mix two topics, and their embedding may land elsewhere. Section B decides.
    - **Two-step cost.** If the model reads previews often, it pays extra requests (latency, free-tier rate limits).
- 気づき・疑問：
  - **The cheapest improvement was reusing data I already had.** Page embeddings were stored for vector search anyway, so ranking graph neighbours by the question needed only one more SQL query. The graph decides *which pages are reachable*; the embeddings decide *which of them to show*.
  - **"Show a map, read on demand" separates finding from reading.** It is the same idea as Tree's first-sentence candidates and Lecture 3's Skills (name and description first, body only when needed). It only works if the map text is informative, which is why `preview_line()` mattered more than the ranking.
  - **Offline checks split the failure as on slide 13.** "Was the evidence retrieved?" can be measured without the model. "Was it used?" cannot. Section A only answers the first question.
  - Question: should `read_page` be limited (e.g. max 3 per question) so that a curious model doesn't turn the hybrid into full Tree-style browsing?
  - AI use: an AI assistant wrote the code, tests and draft. I ran the tests and the offline check locally. The generation results in section B come only from my own Codespaces runs (`lectures/05/runs/`).
