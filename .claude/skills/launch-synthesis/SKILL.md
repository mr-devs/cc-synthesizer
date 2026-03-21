---
name: launch-synthesis
description: Use when the user wants to view or interact with synthesis.html after running /create-synthesis — builds the HTML, verifies Claude Code auth, starts the local server, and opens the page in the browser
allowed-tools: Bash, Read, Edit
---

# Launch Synthesis

Builds `synthesis/synthesis.html`, starts the local FastAPI server, and opens the page in the browser so the "Ask Claude" side panel works immediately.

## Instructions

Run the following steps in order. Stop and report clearly if any step fails.

### Step 1 — Build the HTML (iterative warning-fix loop)

Run the build script and capture its full output:

```bash
uv run python scripts/build_html.py
```

**If the build fails** (non-zero exit code or error output), report the error and stop.

**If the build succeeds**, inspect the output for lines beginning with `WARNING:`.

Classify each warning:
- **Fixable warnings**: heading level jumps (e.g., "Heading level jump from h2 to h4") and multiple H1 headings. These indicate structural problems in `synthesis/synthesis.md` that can be corrected by editing the file.
- **Non-fixable warnings**: missing citation keys (e.g., "Missing citation keys:" followed by `[@Key]` entries). These require re-running `/summarize-documents` and cannot be fixed by editing the synthesis.

**If there are fixable warnings**:
1. Read `synthesis/synthesis.md` using the Read tool.
2. Understand the specific warning (which heading, which level jump, or which extra H1).
3. Edit `synthesis/synthesis.md` using the Edit tool to fix the structural issue:
   - For heading level jumps: change the offending heading's `#` count to the correct sequential level (e.g., change `#####` to `###` if jumping from h2 to h5).
   - For multiple H1s: demote the second and subsequent H1s to H2 (change `# Heading` to `## Heading`).
4. Re-run `uv run python scripts/build_html.py` and re-inspect output.
5. Repeat up to **3 total iterations**. If fixable warnings persist after 3 iterations, report them to the user and stop.

**If only non-fixable (citation) warnings remain** after all fixable warnings are resolved (or if there were never any fixable warnings): proceed with the launch but note the citation warnings in your final report to the user.

**If there are no warnings**: proceed immediately.

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
