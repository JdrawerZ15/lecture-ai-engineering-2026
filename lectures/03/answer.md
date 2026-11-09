# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：
- `--trace` で見えたツール呼び出し（ツール名と引数）：
- 1つの質問での LLM 呼び出し回数（`requests`）：
- 追加したツールと、docstring に書いた説明：

## 宿題

- 取り組んだレベル：発展（b）— Run Pi in Codespaces and compare its system prompt with my `INSTRUCTIONS`

- やったこと：
  1. Installed Pi in Codespaces: `npm install -g --ignore-scripts @earendil-works/pi-coding-agent`
  2. Launched it with `pi`, typed `/model` and chose a Gemini model (the `GEMINI_API_KEY` secret was picked up automatically).
  3. Asked Pi a question about this repo (see 結果 → "Run in Codespaces").
  4. Read `packages/coding-agent/src/core/system-prompt.ts` in github.com/earendil-works/pi (commit `7d07332`), plus the tool files that feed text into it (`core/tools/read.ts`, `bash.ts`, `edit.ts`, `write.ts`) and `core/resource-loader.ts`, and compared them with `INSTRUCTIONS` in `app/agent.py`.

- 結果：

  **Run in Codespaces** *(fill in from your own run)*
  - Model chosen with `/model`: `<e.g. gemini-3.5-flash>`
  - Question asked: `What does search_glossary in app/tools.py do, and what tools does app/agent.py register?`
  - What Pi did: `<e.g. ran bash "ls", read app/tools.py and app/agent.py, then answered>` — it ran commands / read files **without asking for confirmation**, as the slides warn.
  - Answer quality: `<one line>`

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
