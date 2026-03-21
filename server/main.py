#!/usr/bin/env python3
"""
server/main.py — FastAPI server for cc-synthesizer.

Receives context payload from synthesis.html, reads local summary files,
and streams a Claude response as SSE via the Claude Code CLI.

Start: PYTHONPATH=/path/to/cc-synthesizer uv run uvicorn server.main:app --reload
Prereq: claude CLI must be installed and authenticated (claude auth status)
"""

import asyncio
import json
import subprocess
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator, List, Optional
from urllib.parse import urlparse

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

MANIFEST: dict = {}


@asynccontextmanager
async def lifespan(app):
    global MANIFEST
    try:
        MANIFEST = json.loads(
            Path("summaries/manifest.json").read_text(encoding="utf-8")
        )
    except Exception:
        MANIFEST = {}
    yield


app = FastAPI(title="cc-synthesizer server", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type"],
    allow_credentials=False,
)


class Citation(BaseModel):
    key: str
    title: str = ""
    authors: str = ""
    year: str = ""
    venue: str = ""
    doi: str = ""
    pdf: str = ""
    summary: str = ""


class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatContext(BaseModel):
    selectedText: str = ""
    citations: List[Citation] = Field(default_factory=list)
    synthesisTopic: str = ""
    memoryDoc: Optional[str] = None


class ChatPayload(BaseModel):
    messages: List[Message]
    context: ChatContext = Field(default_factory=ChatContext)


def _resolve_file_url(url: str) -> Optional[str]:
    if not url:
        return None
    if url.startswith("file://"):
        path = Path(urlparse(url).path)
    else:
        path = Path(url)
    return str(path) if path.is_file() else None


SYSTEM_PROMPT = """\
You are a research assistant helping a user explore a document synthesis. \
You have access to the synthesis text, relevant citation metadata, and document summaries. \
Be concise, direct, and grounded in the provided sources. \
When referencing specific papers use the citation key in brackets, e.g. [AuthorYear]. \
If you cannot find something in the provided context, say so clearly.

You can also edit the synthesis document when the user explicitly asks you to make changes. \
When the user explicitly requests a change to the synthesis (e.g. "update the synthesis", \
"add a section on X", "rewrite the introduction"), respond ONLY with a JSON object in this format:
{"text": "Your conversational response here...", "action": {"type": "edit_synthesis", "content": "...full new synthesis.md content..."}}

For all other responses (questions, explanations, analysis), respond with plain text only — \
do NOT use JSON format.

You have access to Bash and Read tools to explore source documents directly.
To search a PDF:   bash -c "pdftotext -layout '/path/to/file.pdf' - | grep -in 'search term' | head -40"
To read pages:     bash -c "pdftotext -layout -f 3 -l 6 '/path/to/file.pdf' -"
To read a summary: use the Read tool on the summary path.
File paths for relevant documents are listed in the Document directory section of your context.
Prefer searching before reading full page ranges to minimize token use."""


def build_prompt(payload: ChatPayload) -> str:
    ctx = payload.context

    cit_lines = (
        "\n".join(
            f"- [{c.key}] {c.title or '(no title)'} — {c.authors or 'unknown'}, {c.year or 'n.d.'}"
            for c in ctx.citations
        )
        or "(none)"
    )

    # Build a file-path directory for the relevant citations
    dir_lines = []
    for c in ctx.citations:
        entry = MANIFEST.get(c.key, {})
        pdf = _resolve_file_url(entry.get("pdf", ""))
        summary = _resolve_file_url(entry.get("summary", ""))
        parts = [f"- [{c.key}]"]
        if pdf:
            parts.append(f"PDF: {pdf}")
        if summary:
            parts.append(f"Summary: {summary}")
        if len(parts) > 1:
            dir_lines.append("  ".join(parts))

    dir_block = (
        (
            "\n## Document directory (use Bash/Read to access)\n"
            + "\n".join(dir_lines)
            + "\n"
        )
        if dir_lines
        else ""
    )

    memory_block = f"\n## Synthesis memory\n{ctx.memoryDoc}\n" if ctx.memoryDoc else ""

    # Build conversation history (all but the last message, which is the current user turn)
    history_parts = []
    for msg in payload.messages[:-1]:
        prefix = "User" if msg.role == "user" else "Assistant"
        history_parts.append(f"{prefix}: {msg.content}")

    history_block = "\n\n".join(history_parts)

    # The final user message
    last_message = payload.messages[-1].content if payload.messages else ""

    return (
        f"{SYSTEM_PROMPT}\n\n---\n\n"
        f"## Context\n"
        f"You are helping me understand a synthesis about: {ctx.synthesisTopic}\n"
        f"\n## Relevant citations\n{cit_lines}\n"
        f"{dir_block}"
        f"{memory_block}\n\n"
        + (f"## Conversation history\n{history_block}\n\n" if history_block else "")
        + f"## Current message\n{last_message}"
    )


def _sse(obj: dict) -> str:
    return f"data: {json.dumps(obj)}\n\n"


def _error_events(msg: str) -> list[str]:
    return [_sse({"error": msg}), "data: [DONE]\n\n"]


async def stream_chat_response(payload: ChatPayload) -> AsyncIterator[str]:
    if not payload.messages:
        for event in _error_events("No messages provided."):
            yield event
        return

    prompt = build_prompt(payload)

    try:
        proc = await asyncio.create_subprocess_exec(
            "claude",
            "--print",
            "--output-format=stream-json",
            "--include-partial-messages",
            "--verbose",
            "--allowedTools",
            "Bash,Read",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        proc.stdin.write(prompt.encode("utf-8"))
        await proc.stdin.drain()
        proc.stdin.close()

        # Collect the full response (needed to detect JSON action envelopes)
        full_text = ""

        while True:
            line = await proc.stdout.readline()
            if not line:
                break
            text_line = line.decode("utf-8").strip()
            if not text_line:
                continue
            try:
                event = json.loads(text_line)
            except json.JSONDecodeError:
                continue

            if event.get("type") == "stream_event":
                inner = event.get("event", {})
                if inner.get("type") == "content_block_delta":
                    delta = inner.get("delta", {})
                    if delta.get("type") == "text_delta" and delta.get("text"):
                        full_text += delta["text"]
            elif event.get("type") == "result" and event.get("is_error"):
                err = event.get("result", "Claude CLI returned an error.")
                for e in _error_events(err):
                    yield e
                await proc.wait()
                return

        await proc.wait()

        # Check if the response is a JSON action envelope
        stripped = full_text.strip()
        if stripped.startswith("{"):
            try:
                envelope = json.loads(stripped)
                if "action" in envelope and "text" in envelope:
                    action = envelope["action"]
                    if action.get("type") == "edit_synthesis":
                        Path("synthesis/synthesis.md").write_text(
                            action.get("content", ""), encoding="utf-8"
                        )
                        await asyncio.to_thread(
                            subprocess.run,
                            ["uv", "run", "python", "scripts/build_html.py"],
                            check=False,
                        )
                        yield _sse({"text": envelope["text"]})
                        yield _sse({"reload": True})
                        yield "data: [DONE]\n\n"
                        return
            except (json.JSONDecodeError, KeyError):
                pass

        # Plain text response — emit as a single event
        if full_text:
            yield _sse({"text": full_text})
        yield "data: [DONE]\n\n"

    except FileNotFoundError:
        for e in _error_events(
            "claude CLI not found. Ensure Claude Code is installed and on PATH."
        ):
            yield e
    except Exception as exc:
        for e in _error_events(str(exc)):
            yield e


@app.post("/chat")
async def chat(payload: ChatPayload):
    return StreamingResponse(
        stream_chat_response(payload),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/health")
async def health():
    return {"status": "ok", "backend": "claude-code-cli"}
