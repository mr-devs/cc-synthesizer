---
name: launch-synthesis
description: Use when the user wants to view or interact with synthesis.html after running /create-synthesis — builds the HTML, verifies Claude Code auth, starts the local server, and opens the page in the browser
allowed-tools: Bash, Read, Edit, Agent
---

# Launch Synthesis

Builds `synthesis/synthesis.html`, starts the local FastAPI server, and opens the page in the browser so the "Ask Claude" side panel works immediately.

## Instructions

Run the following steps in order. Stop and report clearly if any step fails.

### Step 1 — Build the HTML

Dispatch a single subagent with `subagent_type: html-build-fixer`. It runs `uv run python scripts/build_html.py`, classifies the warnings, edits heading-structure problems in `synthesis/synthesis.md`, and re-builds — up to 3 iterations. The agent definition at `.claude/agents/html-build-fixer.md` carries the full loop and return format, so the dispatch prompt needs no detail beyond "build the synthesis HTML and fix any structural warnings."

Act on its status line:

- **`BUILD: clean`** or **`BUILD: fixed (n edits)`** — proceed to Step 2.
- **`BUILD: unresolved`** — report the remaining warnings to the user and stop.
- **`BUILD: failed`** — report the build error and stop.

If the agent returns a `CITATION_WARNINGS:` block, the build still succeeded — these are missing citation keys, which cannot be fixed by editing the synthesis. Proceed with the launch and surface them in Step 5.

### Step 2 — Check Claude Code auth

```bash
claude auth status
```

If the output does not indicate the user is logged in, tell them to run `claude auth login` and stop.

### Step 3 — Open the HTML page

```bash
open "$(pwd)/synthesis/synthesis.html"
```

On Linux, use `xdg-open` instead of `open`.

### Step 4 — Get the project root path

Run:

```bash
pwd
```

Capture the output as `{PROJECT_ROOT}`.

### Step 5 — Report to the user

Tell the user the page has been opened, then instruct them to start the server by running this command in a **new terminal window** (substituting the actual path for `{PROJECT_ROOT}`):

```
PYTHONPATH={PROJECT_ROOT} uv run uvicorn server.main:app --reload
```

Show the command with the real path filled in, not the placeholder. Explain that the "Ask Claude" side panel requires this server to be running, and that closing the terminal window will automatically stop the server — no cleanup needed.

If there were any non-fixable citation warnings, mention them here and suggest re-running `/summarize-documents` so citations have full metadata.
