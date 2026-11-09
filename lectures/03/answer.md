# 第3回 解答

## 演習

All runs with `gemini-3.5-flash-lite`.

- 第1回（素のLLM）とエージェントの回答の違い：Same question "AIE2026の講座の宿題にある「3レベル」とは何ですか？".
  - Lecture 1 (`app.ask`, plain LLM): didn't know the course and guessed three generic meanings (difficulty levels, Bloom's taxonomy, must/stretch/geek); none matched, 733 output tokens.
  - Lecture 3 (`app.agent`): answered correctly and briefly — 基礎（講義内容の確認）/ 実装（自分でコードを書く）/ 発展（調査や試行）, completing any one finishes that lecture's homework, and in principle it isn't graded — which matches `homework-levels` in `data/glossary.json` almost word for word. It ended with "関連する回：第1回", as `INSTRUCTIONS` asks.
- `--trace` で見えたツール呼び出し（ツール名と引数）：
  - `--trace "第2回の内容から確認問題を1問出して"`:
    ```text
    [tool call]   make_quiz({'lecture': 2})
    [tool return] make_quiz -> {"question": "「Hugging Face Hub」の意味は？", "answer": "公開されたモデルやデータセットを共有・ダウンロードできるプラットフォーム。…
    ```
  - `--trace "LoRAとQLoRAの違いは？"` failed with 503 (model overloaded) when I ran it, so I have no trace for that question.
- 1つの質問での LLM 呼び出し回数（`requests`）：**2** for the review-question run: `RunUsage(input_tokens=1000, output_tokens=63, requests=2, tool_calls=1)` — one request where the model chose `make_quiz`, and one after the tool result came back to write the answer.
- 追加したツールと、docstring に書いた説明：
  - `make_quiz(lecture: int) -> str` in `app/tools.py`, registered with `agent.tool_plain(tools.make_quiz)` in `app/agent.py`. I also added "確認問題（復習問題）を求められたら make_quiz を使う" to `INSTRUCTIONS`.
  - Docstring: picks one term of the given lecture from the glossary and returns a review question and its answer; use it when asked for a review question / quiz such as "第2回の確認問題を出して". Returns `{"question": ..., "answer": ...}` as JSON.
  - If the lecture has no terms (e.g. `lecture=0`) it returns a message listing the lectures that have terms instead of raising an error.
  - Verified without an API key: `uv run pytest -q` → 11 passed; `--list-tools` shows `make_quiz` with its docstring; `make_quiz(2)` returned `{"question": "「事前学習」の意味は？", "answer": "大量の汎用テキストで、次のトークンを予測するように…"}`.
  - With the API: the model called `make_quiz({'lecture': 2})` (trace above), so the docstring + INSTRUCTIONS line were enough for it to pick the tool and the right argument.
  - Observation: the tool returned both the question and the answer, but the agent showed **only the question** ("考えてみてくださいね。答えは「第2回」にあります！") and ended with "関係する回：第2回". This matches the INSTRUCTIONS line "宿題の答えそのものは書かず、考え方のヒントで導く" — the model treated the quiz answer like a homework answer. Good for learning, but the user has no way to check their answer unless they ask again; if I wanted the answer shown on request, I'd need to say so in the docstring or INSTRUCTIONS.

## 宿題

- 取り組んだレベル：発展（b）— Run Pi in Codespaces and compare its system prompt with my `INSTRUCTIONS`

- やったこと：
  1. Installed Pi in Codespaces: `npm install -g --ignore-scripts @earendil-works/pi-coding-agent`
  2. Launched it with `pi`, typed `/model` and chose a Gemini model (the `GEMINI_API_KEY` secret was picked up automatically).
  3. Asked Pi a question about this repo (see 結果 → "Run in Codespaces").
  4. Read `packages/coding-agent/src/core/system-prompt.ts` in github.com/earendil-works/pi (commit `7d07332`), plus the tool files that feed text into it (`core/tools/read.ts`, `bash.ts`, `edit.ts`, `write.ts`) and `core/resource-loader.ts`, and compared them with `INSTRUCTIONS` in `app/agent.py`.

- 結果：

  **Run in Codespaces**
  - Model chosen with `/model`: `gemini-3.6-flash`
  - Question asked: `What does search_glossary in app/tools.py do, and what tools does app/agent.py register?`
  - At startup Pi tried to download `fd` and `ripgrep` from GitHub on its own; both downloads failed (HTTP 504) and Pi kept running without them.
  - What Pi did (all **without asking for confirmation**, as the slides warn):
    1. `read app/tools.py` → failed with ENOENT, because I had launched `pi` from `lectures/03/`, and Pi resolves paths from its working directory (the `<cwd>` section of its prompt).
    2. Recovered by itself: ran `find . -name "*.py"` (no output), `ls -la`, then `find /workspaces/lecture-ai-engineering-2026 -name "tools.py" -o -name "agent.py"`.
    3. Found the right path and called `read /workspaces/lecture-ai-engineering-2026/app/tools.py`.
  - Result: it did not reach a final answer. The model first returned **503** (high demand), then **429 RESOURCE_EXHAUSTED**: the free tier allows only **5 requests per minute** for `gemini-3.6-flash`, and every tool step (each read / find / ls) is a separate LLM request, so 4–5 steps used up the minute's quota.
  - Takeaways: (1) a coding agent explores with many small tool calls, so it hits rate limits much faster than our glossary agent (the exercise example shows `requests=2` for one question); (2) the working directory matters — it's part of Pi's system prompt, and launching from the repo root would have avoided the failed read and three extra commands.

  **Pi's system prompt is assembled, not written as one string.** `buildSystemPromptSections()` builds sections and wraps each one in an XML tag. With the default tools (`read`, `bash`, `edit`, `write`) the rendered prompt is roughly:

  ```text
  You are a coding assistant running inside pi, a coding agent harness. Help users inspect files, run commands, and modify code.
  <tools>
  - read: Read file contents
  - bash: Execute bash commands (ls, grep, find, etc.)
  - edit: Make precise file edits with exact text replacement, including multiple disjoint edits in one call
  - write: Create or overwrite files

  Additional tools may be available.
  </tools>
  <rules>
  - Use bash for file operations like ls, rg, find
  - Use read to examine files instead of cat or sed.
  - Use edit for targeted changes. Batch changes to one file in a single call.
  - Each edits[].oldText must exactly and uniquely match the original file. ...
  - Use write only for new files or complete rewrites.
  - Be concise in your responses
  - Show file paths clearly when working with files
  </rules>
  <docs> paths to Pi's own README/docs/examples, "read only when the user asks about the harness itself" </docs>
  <project_context> AGENTS.md / CLAUDE.md found in the project, if any </project_context>
  <skills> ... </skills>
  <cwd>/workspaces/lecture-ai-engineering-2026</cwd>
  ```

  **Comparison**

  | Aspect | My `INSTRUCTIONS` (app/agent.py) | Pi's system prompt |
  |---|---|---|
  | Role | "Learning support agent for AIE2026" | "Coding assistant running inside pi" — one line, same idea |
  | How it is built | One fixed string in Japanese | Assembled at runtime from sections; English; each section in an XML tag so it can be updated later in the session |
  | Tool list | Not listed; the model sees tools only through docstrings. INSTRUCTIONS mentions tools by name | Tools listed in the prompt with a one-line snippet each, *only for tools that are enabled*, plus "Additional tools may be available" |
  | When to use a tool | Mandatory: "always check search_glossary before answering"; "use get_lecture_summary when asked about a session" | Preferences between tools, not obligations: "read instead of cat/sed", "edit for targeted changes, write only for new files" |
  | Where tool rules live | Mixed: some in INSTRUCTIONS, some in docstrings ("only one term in query") | Each tool file contributes its own `guidelines`; they appear only when that tool is enabled, and duplicates are removed |
  | Unknowns / honesty | "If it's not in the glossary, don't guess; say so" | **Not written** |
  | Answer format | "End with the relevant lecture (Lecture N)" | "Be concise", "show file paths clearly" |
  | Domain policy | "Don't write homework answers; guide with hints" | **Not written** (no teaching policy, it's a coding tool) |
  | Safety / confirmation | Nothing (our tools are read-only, so it matters less) | **Not written**, and the harness itself doesn't ask before bash/edit/write — hence "run it in Codespaces" |
  | Environment context | None | Injects working directory, project files (AGENTS.md, CLAUDE.md), skills, paths to its own docs |
  | Customization | Edit the Python source | Without touching code: `.pi/SYSTEM.md` replaces the prompt, `.pi/APPEND_SYSTEM.md` adds to it, AGENTS.md adds project rules |

- 気づき・疑問：
  - **Pi's prompt is short and general on purpose.** It describes the tools and a few style rules, then lets the user add domain rules via AGENTS.md / APPEND_SYSTEM.md. My INSTRUCTIONS is the opposite: it *is* the domain rules (glossary first, cite the lecture, no homework answers). Pi is a general harness; my agent is a specialized app.
  - **What my INSTRUCTIONS has that Pi lacks:** "don't guess when it's not in the glossary". For a learning agent, a wrong confident answer is the main failure mode (this is exactly what Lecture 2's LoRA model got wrong). For a coding agent, the model can check facts by reading files/running code, so the prompt relies on tools instead of a rule.
  - **What Pi has that my INSTRUCTIONS lacks:** tool rules that travel with the tool. In my agent the "one term per query" rule is in the docstring but "always search first" is in INSTRUCTIONS; if I removed `search_glossary`, INSTRUCTIONS would still mention it. Pi avoids that because a tool's guidelines appear only when the tool is enabled. Moving "Use make_quiz for review questions" into make_quiz's docstring (instead of INSTRUCTIONS) would follow the same idea.
  - **No safety rule in Pi's prompt.** Pi doesn't tell the model to ask before destructive commands, and the harness doesn't ask either. Safety is left to the environment (Codespaces / a container) rather than to the prompt — consistent with the Implementation homework, where confirmation is enforced in code (`requires_approval=True`) rather than by asking the model nicely.
  - **Question:** Pi wraps sections in XML tags so it can update just one section mid-session (`diffSystemPromptSections`). Does sending only the changed section actually keep the prompt cache valid with Gemini, or is that mainly useful for providers with explicit prompt caching?
