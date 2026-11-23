# 第5回 解答

> All generation results come from one run per method in Codespaces with `bash scripts/lec05_runs.sh` (2026-11-23 04:06 UTC, commit `2f42e2f`). The full `--trace` outputs are in `lectures/05/runs/`. The offline retrieval check (no API) is `uv run python -m scripts.lec05_proxy_eval`.

## 演習

- 回答モデル（実行時の`[model]`）：`gemini-3.5-flash-lite`
- 比較した質問：Q1 「第2回の説明では、LoRAは何を固定し何を学習しますか？ QLoRAは何を加えますか？」 (evidence: 第2回・PDF p.52; p.51 also supports "QLoRA = LoRA + 4bit")
- 対象資料（全文投入と他の方式で範囲が違う点も記録）：
  - Vector / Tree / Graph: `RAG_DOCUMENT_IDS = lec01-main, lec02-main, lec03-main` → 214 pages (`SELECT count(*) FROM chunks` = 214).
  - Full text: all 9 documents in `lectures.json` (438 pages). The prompt was 227,971 characters. This includes `lec05-main` (基盤モデルとデータ, 79 pages) and the 4 exercise documents, which search cannot see, so full text is not a same-scope comparison.

### 各方式の結果

| 方式 | 回答の要点・正しさ | 引用ページと根拠 | 時間（秒） | 入力／出力トークン数 | モデル応答回数 | 生成API推定費用（USD） |
|---|---|---|---|---|---|---|
| 全文投入 | **Partial.** Found the right pages but gave only hints, not the answer ("the original weights stay fixed… what shape of parameters is added?"). It treated the question as homework. | 第2回 p.52 (LoRA), p.51 + p.52 (QLoRA) — correct pages | 3.12 | 117,025 / 309 | 1 | $0.035880 |
| ベクトル検索 | **Correct.** W frozen; only the two small low-rank matrices A, B trained; QLoRA adds 4bit compression of W | p.52, p.51 — both support it | 2.18 | 3,027 / 215 | 2 | $0.001446 |
| Tree | **Correct**, plus the 「付箋」 analogy, <1% trained, ~1/4 memory | p.52 only — supports everything | 4.93 | 9,214 / 332 | 5 | $0.003594 |
| Graph | **Correct** | p.52 — supports it (p.51 was also returned) | 3.45 | 5,771 / 181 | 2 | $0.001636 |

Same question, same model. Vector search was the fastest and cheapest correct answer. Full text cost **~25×** more ($0.0359 vs $0.0014) and used 39× more input tokens for a worse answer. My vector/Graph input tokens are almost identical to the instructor's slide 21 (3,028 and 5,771). Full text matches exactly (117,025), but my full-text run took 3.12 s against 4.41 s on the slide.

- 検索だけを実行して見つかったページと、その本文で確認できたこと：
  - The agent's own `search_materials('LoRA QLoRA 固定 学習')` returned p.52 (d=0.230), p.51 (0.244), p.60 (0.267), p.61 (0.293), p.47 (0.293). **Only p.52 and p.51 support the answer.** p.60/p.61 are the QLoRA exercise pages (they share the word "QLoRA"), and p.47 is about RAG vs FT.
  - The text of p.52 says the original weights W are **frozen**, only the small matrices A and B (the low-rank "delta") are **trained**, and QLoRA **compresses W to 4bit** (about 1/4; ~4GB for 7B). p.51 says the same in one line each.
- `--trace`で見えたツール呼び出し（ツール名・引数・回数、Treeでたどった目次など）：
  - **Vector:** 1 call, `search_materials({'query': 'LoRA QLoRA 固定 学習'})`. The model shortened the question into keywords.
  - **Graph:** 1 call with the same query. 3 seeds (p.52, p.51, p.60) + 7 added pages (p.53, p.50, p.59, p.61 at 1 hop; p.49, p.62, p.47 at 2 hops). All 7 added pages were in the same chapter, and none were needed.
  - **Tree:** 4 calls: lecture list → `lec02-main` → chapter `lec02-main-s045` 「選んだモデルを、いつ・どう直すか」 (18 pages) → `lec02-main-p052` (717 characters). It read only one page in full.
    - In that chapter, the "first sentence" for p.46–p.55 and p.58 is the same progress header, 「4/4 選んだモデルを、いつ・どう直すか」. The model picked p.52 **by title alone**, which works here because the title says 「LoRA と QLoRA」.
  - I changed `print_trace` so the search tools list every page they returned (`[全文]`, `[全文・追加]`, `[要約のみ]` + distance/hops). The original trace cut results at 120 characters, which hid which pages Graph added.
- 取得した情報が足りなかった例、取得できたのに回答へ使えなかった例：
  - **Retrieved but not used — full text.** The evidence was in the prompt, and the model even cited p.51/p.52. But `FULL_CONTEXT_INSTRUCTIONS` says 「宿題の答えそのものは書かず」, and it turned a factual question into a hint-only reply. The failure is in the instructions, not in retrieval (slide 13: "evidence present, answer incomplete → revisit instructions").
  - **Retrieved too much — Graph.** 10 pages of full text when 1–2 were needed (5,771 vs 3,027 input tokens). The answer was the same as vector's.
  - **Missing evidence (Q2, homework):** Graph and Tree never fetched 第3回 p.13 for the memory question. The answers were still correct because p.39/p.40 are enough.
- 今回の用途に採用したい方式と、その理由・比較条件の限界：
  - **Plain vector search** for a course Q&A bot: correct on all three questions (see Homework), fastest (2.1–2.8 s) and cheapest (~$0.0014–0.0019). Graph and Tree reached the same answers with 1.7–4.4× the input tokens. Full text is ~25× the cost and its scope is different.
  - Limits: one run per method, one model, three questions. Full text covers a different scope (438 vs 214 pages). Q1 is easy for every method because one page holds the whole answer.
- 気づき・疑問：
  - **More context did not give a better answer.** Full text had everything and produced the worst answer of the four. Its failure came from a general rule in its instructions (no homework answers), not from the 117k tokens.
  - **Tree is only as good as its candidate text.** 102 of the 214 searchable pages give a useless preview: 62/71 in Lecture 3 just repeat the title, and 40/70 in Lecture 2 are the 「N/4 章名」 progress header. Q1 worked only because the slide title is explicit.
  - **Tree costs requests.** 5 model requests on Q1 (vs 2) and 7 on Q2. On the free tier, the number of requests per question matters as much as tokens (rate limits).
  - **"Related ≠ contains the answer" in numbers.** Graph's 7 added pages for Q1 were all neighbours in the same chapter, and none was used.
  - Question: the search DB does not include Lecture 5's own slides (`lec05-main`), while full text does. Is that on purpose, to show the scope effect?

## 宿題

- 取り組んだレベル：**発展** — a combined retrieval method, `--hybrid` (vector × Graph × Tree)

- やったこと（変更したファイル・設定・処理、または設計した取得方法）：
  - **Target question.** Q2 (multi-page, cross-chapter): 「第3回の例では、コンパクションとセッションをまたぐメモリはどう違いますか。日々のメモはすべて長期メモリに入りますか」. I checked the evidence first in `lectures.json`:
    - 第3回 p.39: compaction (summarise old history, same session) vs memory tool / auto memory (outside store, across sessions)
    - 第3回 p.40: OpenClaw daily notes → nightly review → only items above a threshold move to `MEMORY.md`; one-off research stays in the daily notes
    - 第3回 p.13: the basic idea (write out to an external store, read back into a new context). It is in *Part 2*, not in *Part 6 メモリ*.

    Controls: Q1 (single page, p.52) and Q3 「今回作ったRAGの実測平均応答時間と正答率を教えてください」 (not in the materials).
  - **Design** (`app/retrieval.py: search_hybrid`, tools `search_hybrid` + `read_page`, mode `--hybrid`):
    1. **Entry = vector search.** The top `HYBRID_SEEDS = 3` pages come back with full text (same entry as Graph).
    2. **Candidates = graph neighbourhood.** `next_page` and `mentions` edges, up to `HYBRID_HOPS = 2` hops (same relations and hop count as `--graph`).
    3. **Re-rank by the question.** Each candidate's distance comes from the page embedding **already stored** in `index.sqlite3`, using `vec_distance_cosine` on just those `page_id`s. No extra embedding calls: the only API cost for retrieval is the one query embedding.
    4. **Return previews, not full text** (Tree's idea). The top `HYBRID_PREVIEWS = 7` candidates come back as section, title, distance, `via` (the term or page that linked them) and one line of content. `preview_line()` skips lines that repeat the title, the 「N/4」 progress header and 出典/© lines.
    5. **Fetch on demand.** The model reads a candidate's full text with `read_page(page_id)`. `HYBRID_INSTRUCTIONS` tells it to check that every part of the question has a supporting page before answering.
  - **Why this shape:**
    - Graph's weakness is that its expansion ignores the question and costs 10 full pages.
    - Tree's weakness is weak candidate text and many calls.
    - Vector's weakness is that it picks 5 full pages by distance alone, with no view of what is nearby.
    - The hybrid keeps 3 full pages and turns the rest into a cheap, relevance-ranked "map".
  - Also: `scripts/lec05_runs.sh` (all runs with `--trace`, saved to `lectures/05/runs/`), `scripts/lec05_proxy_eval.py` (offline check), `tests/test_hybrid.py` (4 tests, no API). `uv run pytest -q` → 21 passed.

- 比較した質問と、固定した条件（モデル・対象資料など）：Q1–Q3. Fixed conditions:
  - Model `gemini-3.5-flash-lite`, same 214 pages, same index (commit `2f42e2f`).
  - One run each, 30 s apart, in this order: Q1 full/vector/tree/graph/hybrid, Q2 vector/tree/graph/hybrid, Q3 vector/graph/hybrid.
  - Basic RAG (vector) is the baseline. Graph and Tree are references.

- 結果（変更前後の回答・根拠、`--trace`の出力、時間・トークン数・生成API推定費用など）：

  **A. Retrieval only, offline (no API).** Each probe uses a **stored page embedding** as the query vector (an evidence page, or the normalised mean of p.39 and p.40). This checks what each method returns *around the right spot*, not whether the real question lands there.

  | Question | Probe | Vector top-5 (full) | Graph 3+7 (full) | Hybrid full | Hybrid full + preview | Characters V / G / H |
  |---|---|---|---|---|---|---|
  | Q1 | p.52 | 1/1 | 1/1 | 1/1 | 1/1 | 4,208 / 9,272 / 4,169 |
  | Q2 | mean(p.39, p.40) | 3/3 | 2/3 (no p.13) | 2/3 | **3/3** | 3,460 / 8,915 / 3,584 |
  | Q2 | p.13 | 3/3 | 3/3 | 2/3 | **3/3** | 3,166 / 7,227 / 3,333 |
  | Q2 | p.39 | 2/3 (no p.13) | 2/3 (no p.13) | 2/3 | **3/3** | 3,731 / 8,890 / 3,634 |
  | Q2 | p.40 | 3/3 | 2/3 (no p.13) | 2/3 | **3/3** | 3,441 / 8,896 / 3,559 |

  **B. With the model (real questions).**

  | Q | Method | Answer | Evidence pages returned (full text) | Cited | Tool calls | Time (s) | In / out tokens | Req. | Est. USD |
  |---|---|---|---|---|---|---|---|---|---|
  | Q1 | vector | Correct | p.52, 51, 60, 61, 47 | 51, 52 | 1 search | 2.18 | 3,027 / 215 | 2 | 0.001446 |
  | Q1 | hybrid | Correct | p.52, 51, 60 (+7 previews) | 51, 52 | 1 search | 2.53 | 3,136 / 217 | 2 | 0.001483 |
  | Q2 | vector | Correct, complete | p.39, 65, 38, **13**, **40** | 13, 39, 40, 65 | 1 search | 2.77 | **2,502** / 452 | 2 | **0.001881** |
  | Q2 | tree | Correct | p.39, 40, 41 (Part 6 only) | 39, 40 | 6 browse | 7.22 | 11,045 / 658 | 7 | 0.004958 |
  | Q2 | graph | Correct (+1 unsupported line) | p.39, 65, 38 + 40, 64, 66, 37, 41, 63, 67 | 38, 39, 40, 65 | 1 search | 3.65 | 5,301 / 489 | 2 | 0.002813 |
  | Q2 | hybrid | Correct, complete | p.65, 39, 38; previews **40 (#1)**, **13 (#2)** → `read_page(p040)` | 39, 40, 65 | 1 search + 1 read | 3.30 | 5,597 / 587 | 3 | 0.003147 |
  | Q3 | vector | Says not in materials ✓ | p.13 (第2回), 64, 19, 24, 47 | 第2回 p.13 | 1 search | 2.13 | 3,120 / 169 | 2 | 0.001358 |
  | Q3 | graph | Says not in materials ✓ (+1 weak citation) | 第2回 p.13, 第3回 p.64, 19 + 7 | 第2回 p.13, 14 | 1 search | 3.75 | 5,335 / 273 | 2 | 0.002283 |
  | Q3 | hybrid | Says not in materials ✓ | 第2回 p.13, 第3回 p.64, 19 (+7 previews) | 第2回 p.13 | 1 search | 2.41 | 3,161 / 183 | 2 | 0.001406 |

  What the Q2 hybrid trace shows (`lectures/05/runs/q2_hybrid.txt`):
  - The real query embedding put **p.65, p.39, p.38** in the seeds. The two key pages arrived as the top two previews: **p.40** (d=0.275, 「毎晩過去のやり取りを読み直し…」) and **p.13** (d=0.280).
  - The model then called `read_page('lec03-main-p040')` and answered the daily-notes part from it. **The "map, then read" step worked as designed.**
  - It did not read p.13. It didn't need it, since p.39 covers the session distinction.

- 改善した例と、残る失敗・制約：
  - **Improved vs Graph** (the method it is built from), on the same question:
    - Q1: 3,136 vs 5,771 input tokens (−46%), with the same answer.
    - Q3: 3,161 vs 5,335 tokens (−41%). The answer is equally correct and has no weak citation.
    - Q2: both found p.40. Graph's full-text expansion never contained p.13. The hybrid ranked p.13 #2 and could have read it.
  - **Improved vs Tree** on Q2: Tree only opened *Part 6 メモリ* and never saw p.13, as predicted from the TOC. It used 7 requests / 11,045 tokens; the hybrid used 3 / 5,597.
  - **Not improved vs Basic RAG — the honest result.**
    - On Q2, plain vector top-5 already contained **all three** evidence pages (p.13 rank 4, p.40 rank 5). It answered completely with **2,502 tokens, 2 requests, $0.0019**.
    - The hybrid needed 5,597 tokens, 3 requests and $0.0031, about **2.2× the tokens and 1.7× the cost** for the same answer. The extra request (`read_page`) re-sends the whole conversation, so "read on demand" costs a full round trip.
    - On Q1/Q3 the hybrid is on par with vector (+1–4% input tokens).
  - **Other failures and limits:**
    - **Previews of divider pages carry no content** (「演習」, 「Part 6」, 「この 15 分の芯」) but still take preview slots (Q1: p.61 「演習」).
    - **Hub terms widen the pool.** AIエージェント has 104 pages and ツール 91, so the distance ranking does all the work.
    - **Offline vs real query.** The offline probes predicted that the evidence p.39/p.40 would be seeds. The real question's embedding put p.65 (補足：メモリと Context Engineering) and p.38 on top instead. Probes with page embeddings are optimistic.
    - **One run per method.** Q2 vector getting p.13 at rank 4 (d=0.259, tied with p.40) is a close call, and another phrasing could push it out of the top 5.
  - **Would I adopt it?** Not as the default. For this course bot, questions are mostly answerable from 1–3 neighbouring pages, and Basic RAG was correct, fastest and cheapest on all three. I would keep the hybrid's two cheap parts:
    - `preview_line()`, as a fix for Tree's candidate text
    - re-ranking graph candidates by stored embeddings, as a fix for Graph's noise

    And I would add the "read more" step only when the question names more parts than the top-k pages cover.

- 気づき・疑問：
  - **Measuring changed my conclusion.** The offline check said "the hybrid always shows all evidence, Graph misses p.13", which looked like a win. The real runs showed that vector top-5 *also* had p.13. The hybrid's real cost (an extra request) only appears with the model in the loop. This is the lecture's "measure, then decide" in practice.
  - **Every tool call is a full model request.** `[usage]` counts input tokens over *all* requests, and each new request re-sends the conversation including earlier tool results. Tree's 7 requests and the hybrid's 3 cost more than one larger search result, so fewer, well-filled calls beat many small ones.
  - **Citation ≠ support** (Lecture 4 again).
    - Q3 vector "quoted" a RAG definition from 第2回 p.13, but that text is answer #1 of five *sample LLM answers* on the slide, not the slide's own explanation. The instruction 「資料に記載された例・誤答…を区別する」 exists for exactly this.
    - Graph added two lines its pages don't support: on Q2, 「セッションが終われば原則として保持されません」 (not on p.39 or p.65); on Q3, a citation of p.14 for "evaluation sets" (p.14 is about hallucination).
    - More pages in context gave more chances to blend sources.
  - **The same rule produced opposite behaviour in two modes.** 「宿題の答えそのものは書かず」 is in every mode's instructions. Only full text treated a factual question as homework. With retrieval, the tool results seem to anchor the model to "explain what the material says".
  - Question: should `read_page` be limited (e.g. max 2 per question), or should previews be shown only when the seeds clearly don't cover the question? That would keep the hybrid's cost at vector level on easy questions.
  - AI use: an AI assistant wrote the code, tests, scripts and this draft. I ran the 12 generation runs in my Codespace (`lectures/05/runs/`). Every number above was copied from those files and the offline script output.
