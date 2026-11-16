# 第4回 解答

## 演習

- 基準別の一致率（直す前）：根拠　/　、範囲　/　、ヒント　/　、分かりやすさ　/　、回の表示　/　
- 要確認の件数（直す前）：
- 直した基準と、書き足した方針：
- 基準別の一致率と要確認の件数（直した後）：
- 講師のラベルと自分のラベルで判定が違った項目と、そう判定した理由：
- 気づき・疑問：

## 宿題

- 取り組んだレベル：発展 — one benchmark dataset: **SWE-bench Verified**

- やったこと：
  1. Picked SWE-bench Verified because it evaluates the same kind of system we built in Lecture 3 (a model + loop + tools), only for code: the agent gets a real repository and a GitHub issue and must edit files until hidden tests pass.
  2. Read 4 items in the Hugging Face Dataset Viewer (instance id, issue text, hints, gold patch, `FAIL_TO_PASS` tests, difficulty label). I picked them so the difficulty labels differ: `<15 min fix`, `15 min - 1 hour`, `1-4 hours`.
  3. Read how it was built and checked:
     - the original SWE-bench paper (arXiv 2310.06770)
     - OpenAI's "Introducing SWE-bench Verified" post (Aug 2024)
     - OpenAI's follow-up audit "Why SWE-bench Verified no longer measures frontier coding capabilities" (Feb 2026)
  4. Compared it with today's evaluation set (`data/eval/lec04_cases.jsonl` + `data/eval/rubric.md`).
  - No code written. Items are summarized, not pasted.

- 結果：

  **Dataset**
  - Name: SWE-bench Verified — 500 task instances, taken from SWE-bench's 12 open-source Python repositories
  - Data: https://huggingface.co/datasets/princeton-nlp/SWE-bench_Verified
  - Construction / validation: https://openai.com/index/introducing-swe-bench-verified/
  - Original benchmark: https://arxiv.org/abs/2310.06770
  - Later audit: https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/

  **Fields of one item:** `repo`, `instance_id`, `base_commit` (repo state before the fix), `problem_statement` (the issue title + body, the only task text the model sees), `hints_text` (issue comments posted before the fix), `patch` (gold fix), `test_patch`, `FAIL_TO_PASS` (tests that fail before and pass after the fix), `PASS_TO_PASS` (regression tests), `version`, `environment_setup_commit`, and a human `difficulty` estimate.

  **The 4 items I read**

  | Item | Difficulty label | What it asks (summary) | Size of the reference fix | Could I solve it? / what is hard for an LLM |
  |---|---|---|---|---|
  | `django__django-11099` | — (not shown where I read it) | The username validators use a regex ending in `$`, and in Python `$` also matches just before a trailing newline, so `"alice\n"` is accepted. The issue even says what to change (anchor with `\A`…`\Z`). | Change the regex in 2 validators | **Yes, quickly** — the issue gives the fix. For an LLM it's mostly finding the file. Here the issue text is almost a specification. |
  | `astropy__astropy-14309` | `<15 min fix` | `identify_format("write", Table, "x.ecsv", None, [], {})` crashes with `IndexError` inside `is_fits()`. A recent change made the function check `args[0]` even when `args` is empty. | Small change in `is_fits` in `io/fits/connect.py` | **Yes** — the traceback points at the line. But the hidden test checks one specific behaviour, and other fixes might fail it. |
  | `astropy__astropy-12907` | `15 min - 1 hour` | `separability_matrix` is right for `Linear1D & Linear1D` but wrong when that compound model is **nested** inside another one: outputs that should be independent are reported as coupled. | One-line change in `_cstack` in `modeling/separable.py` | **Probably, with time.** The fix is one line, but finding it means understanding how the matrices of sub-models are stacked. An LLM has to read the code and reproduce the bug instead of pattern-matching the error text. |
  | `astropy__astropy-13398` | `1-4 hours` | A feature request, not a bug: add direct ITRS ↔ AltAz/HADec transforms that stay within ITRS (for satellites and other nearby objects). The issue includes a code sketch. The hints show maintainers asking for safeguards (use it only when relevant, e.g. nearby objects with a distance), which the author says aren't added yet. | New transform module + about 110 lines of new tests; several new `FAIL_TO_PASS` tests (e.g. `test_itrs_topo_to_altaz_with_refraction`) | **No, not without astronomy background.** It needs domain knowledge (aberration, topocentric vs geocentric frames). The hidden tests also check more than the issue's sketch, so the agent must guess the "right" design. That is exactly the "underspecified issue / tests reject valid solutions" problem that Verified tried to filter out. |

  **Who built it and how**

  *Original SWE-bench (2023)* — 7 authors (Princeton / U. Chicago: Jimenez, Yang, Wettig, Yao, Pei, Press, Narasimhan). Built mostly **automatically**, with a 3-stage pipeline:
  1. Scrape ~90,000 PRs from 12 popular Python repos.
  2. Keep merged PRs that resolve an issue **and** change test files.
  3. Keep only instances that install and have at least one test that goes fail → pass.

  Result: 2,294 tasks, with no human check of each item.

  *SWE-bench Verified (2024)* — OpenAI with the SWE-bench authors added a **human validation** step:
  - **Annotators: 93** software developers experienced in Python. They weren't necessarily experts in each codebase but had time to learn it.
  - **Onboarding:** OpenAI engineers first labeled 50 samples very carefully. Every annotator had to pass a test on these and got feedback.
  - **Scale:** 1,699 random samples from the test set, **3 annotators per sample**.
  - **Questions** (each scored 0–3; 2–3 = severe):
    - (a) Is the issue underspecified?
    - (b) Do the `FAIL_TO_PASS` tests reject valid solutions?
    - Also recorded: estimated fix time, and a free-text field for other major problems.
  - **Drop rule:** the ensemble label is the **maximum** severity of the 3. One annotator flagging a severe problem (or any other major issue) was enough to drop the sample.
  - **What was dropped:** 38.3% flagged as underspecified, 61.1% for unfair tests, **68.3% filtered out overall**. The authors say this filter is probably too strict and accept losing some good samples in exchange for confidence.
  - **Final 500:** all samples estimated at 1–4 h and >4 h were included where possible, the rest sampled randomly. Difficulty slices: 196 "easy" (<15 min), 45 "hard" (>1 h).

  *How it is graded* — **by code, not by people or an LLM:**
  - The agent's patch is applied in a Docker container (a harness built together with the SWE-bench authors).
  - The task is "resolved" only if all `FAIL_TO_PASS` **and** all `PASS_TO_PASS` tests pass. The model never sees the tests.
  - Reported as % resolved. At launch, GPT-4o + the Agentless scaffold got 33.2%, against 16% on the original SWE-bench.

  *What happened later (Feb 2026)*
  - OpenAI audited 138 Verified problems (27.6%) that o3 did not consistently solve over 64 runs. **At least 6 experienced engineers** reviewed each one, and every flagged issue was re-checked by another team.
  - Result: 59.4% of the audited problems had material flaws:
    - 35.5% tests too narrow (enforce one implementation)
    - 18.8% tests too wide (check behaviour the issue never asks for)
    - 5.1% other
  - Contamination: frontier models (GPT-5.2, Claude Opus 4.5, Gemini 3 Flash Preview) could reproduce gold patches or exact issue details for some tasks.
  - OpenAI stopped reporting Verified scores, because the top score had flattened (74.9% → 80.9% in 6 months) and gains now reflect exposure to the data more than skill. It recommended SWE-bench Pro instead.

  **Comparison with today's evaluation set**

  | | Today's set (Lecture 4) | SWE-bench Verified |
  |---|---|---|
  | Size | 10 items | 500 (picked from 1,699 annotated, from 2,294 original, from ~90k PRs) |
  | Where items come from | Written by **1 instructor**, answers generated in advance by the Lecture 3 agent | Real GitHub issues and the PRs that fixed them (real users and maintainers) |
  | Who validated | The instructor (`labels_instructor.jsonl`) + each student's own labels | 93 developers, 3 independent reviewers per item, all passed an onboarding test. Later audit: ≥6 engineers per item |
  | How items were dropped / fixed | No items dropped. Instead the **rubric** was fixed (the instructor's README lists 4 rubric changes after test runs), and open questions are kept under 「まだ決めていないこと」 → `unsure` | Items dropped with a strict rule: one severe flag out of 3 removes the item (68% removed). The rubric (task text + tests) is never edited |
  | What is judged | One **answer text** against 4 criteria (根拠・範囲・ヒント・分かりやすさ) + 回の表示 | Whether a **code change** makes the hidden tests pass |
  | Grading method | Humans + LLM-as-a-judge (T / F / unsure with reasons) for 4 criteria. Code only for 「第N回」 | Code only (unit tests in Docker). No LLM, no human at grading time |
  | Output | Agreement rate human vs LLM per criterion, coverage, needs-review list | One number: % resolved |
  | What we measure | Whether the **grader** can be trusted | The **model / agent**. The grader (tests) is assumed correct |
  | Subjective criteria | Yes, on purpose (分かりやすさ) | None. Pass/fail is deterministic, but "correct" is defined by one PR's tests |

- 気づき・疑問：
  - **Grading by tests still has a reference problem.** On the surface SWE-bench avoids today's issue: no LLM judge, so no agreement rate to worry about. But the tests play the role of our `labels.jsonl` and rubric, and they can be wrong too:
    - "too narrow" tests = valid answers marked fail (like a **false alarm**, the reverse of a miss)
    - "too wide" tests = checking things the question never asked
    - Even 3 trained reviewers per item still left ~59% of the hard audited items flawed. So "judged by code" is only as good as whoever wrote the check. The same is true for our 回の表示 criterion (a string check is reliable only because the rule is simple).
  - **Two designs for ambiguous items.** Today we keep ambiguous items and mark them `unsure` until the rubric decides. SWE-bench Verified did the reverse: an item any reviewer found ambiguous was **deleted**. Deleting is safe for a public benchmark (no human review loop at grading time), but it shifts the set toward easy, well-specified tasks. Our set is tiny, so we can't afford to delete — we fix the rubric instead.
  - **Scale vs. reviewers.** Our 10 items have 1 author and effectively 2 labelers (instructor + me). SWE-bench Verified spent 3 × 1,699 ≈ 5,100 annotations to keep 500 items, and that still wasn't enough. One review per item is clearly not enough to call an eval set "verified".
  - **Contamination is a matter of time.** Our cases are new and written for this course, so today's models can't have memorized them. But they live in a public GitHub repo, just like SWE-bench's source repos, so future models may train on them. Any public eval set slowly gets less trustworthy; the only fix is new or private items (SWE-bench Pro's held-out split is the same idea).
  - **Question:** For our own agent, would it be better to delete the items humans disagree on (like Verified) or to keep them as `unsure` (like today)? I think it depends on whether a human will look at the needs-review list every time we grade.
  - Note on AI use: I used an AI assistant to collect the sources and draft this section. I checked the numbers (93 annotators, 3 per sample, 1,699 annotated, 68.3% dropped, 500 kept, 138 audited, 59.4% flawed) against the two OpenAI posts and the SWE-bench paper linked above.
