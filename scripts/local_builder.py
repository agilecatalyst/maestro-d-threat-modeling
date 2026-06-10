#!/usr/bin/env python3
"""
Local Builder for Maestro'D ThreatModeling.

Calls oMLX (OpenAI-compatible) directly on the host — bypasses Cursor localhost routing.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

from openai import OpenAI

FILE_BLOCK_RE = re.compile(
    r"===FILE:\s*(?P<path>[^\n=]+?)===\s*\n(?P<content>.*?)(?=\n===END===|\n===FILE:|\Z)",
    re.DOTALL,
)

DEFAULT_BASE_URL = "http://127.0.0.1:8002/v1"
DEFAULT_API_KEY = "Mikey"  # Maestro'D oMLX — old-fashioned hardcoded
DEFAULT_MODEL = "mlx-community/gemma-4-12B-it-8bit"
DEFAULT_MAX_TOKENS = 4500  # ~5 min @ 15 tok/s — Maestro'D builder budget

# Caveman-lite — default builder mode (verified @ slice 004a).
# Inspired by https://github.com/JuliusBrussee/caveman — human specs stay readable.
CAVEMAN_LITE = True
CAVEMAN_SPEC_MAX_CHARS = 5000
CAVEMAN_SOURCE_MAX_PER_FILE = 3500
CAVEMAN_SOURCE_MAX_TOTAL = 14000

SYSTEM_PROMPT = """You are Local Builder (Dev) for Maestro'D ThreatModeling (Gemma 4 12B).
Maestro Data = tech lead. Specs + BLOCKERS bind. You code.

Caveman-lite (binding):
- Zero filler. No spec restate. No architecture essays.
- First output char: ===FILE: (no preamble).
- Between files: 0–6 words OR nothing.
- MODIFY = keep all unrelated code. APPEND routes/handlers. Never replace whole file unless spec says CREATE.
- Flat imports in backend/agent (uvicorn main:app) — never from .module.
- Follow SHALL/MUST. Respect MUST NOT touch.
- job_id etc. echo caller input — never hardcode UUIDs.
- Update slicedworkload.md checklist; BUILDER_CLAIMS_DONE when all [x]. Never VERIFIED.

Output format — every file:

===FILE: relative/path/from/repo/root===
<file contents>
===END===

No binary/base64 — use test/fixtures/sample.png if needed."""


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parent.parent


def read_text(path: Path, max_chars: int | None = None) -> str:
    text = path.read_text(encoding="utf-8")
    if max_chars and len(text) > max_chars:
        return text[:max_chars] + "\n\n[... truncated for context ...]\n"
    return text


def load_active_slice(repo: Path) -> tuple[str, Path]:
    workload = repo / "slicedworkload.md"
    if not workload.exists():
        raise FileNotFoundError(f"Missing {workload}")

    text = workload.read_text(encoding="utf-8")
    match = re.search(r"\*\*Slice\*\*\s*\|\s*`([^`]+)`", text)
    if not match:
        raise ValueError("Could not parse active slice from slicedworkload.md")
    slice_id = match.group(1)

    spec_glob = list((repo / "docs" / "specs").glob(f"slice-{slice_id}*.md"))
    if not spec_glob:
        raise FileNotFoundError(f"No spec found for slice {slice_id!r} in docs/specs/")
    return slice_id, spec_glob[0]


def extract_blockers(workload_text: str) -> str | None:
    match = re.search(
        r"## BLOCKERS[^\n]*\n(.*?)(?=\n---\n|\n## Review|\Z)",
        workload_text,
        re.DOTALL,
    )
    if not match:
        return None
    body = match.group(1).strip()
    return body if body and "(none)" not in body.lower() else None


def extract_deps_slice(deps_text: str, slice_id: str) -> str:
    slug = slice_id.split("-", 1)[0]  # "002" from "002-diagram-upload"
    pattern = rf"## Slice {slug}[^\n]*\n(.*?)(?=\n---\n|\n## |\Z)"
    match = re.search(pattern, deps_text, re.DOTALL)
    if match:
        return f"## Slice {slug} pins\n{match.group(1).strip()}"
    return read_text_from_str(deps_text, max_chars=2000)


def read_text_from_str(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n[... truncated ...]\n"


def existing_source_paths(repo: Path) -> list[str]:
    paths = [
        "backend/api/main.py",
        "backend/api/database.py",
        "backend/api/models.py",
        "backend/api/storage.py",
        "backend/api/routes/diagrams.py",
        "backend/api/requirements.txt",
        "backend/agent/main.py",
        "backend/agent/inference.py",
        "backend/agent/diagram_loader.py",
        "backend/agent/llm.py",
        "backend/agent/assets_schema.py",
        "backend/agent/asset_text_parser.py",
        "backend/agent/asset_text_blocks.py",
        "backend/agent/pipeline_worker.py",
        "backend/agent/summary_worker.py",
        "backend/agent/db.py",
        "backend/agent/schemas.py",
        "backend/agent/routes/invocations.py",
        "backend/agent/requirements.txt",
        "test/test_upload.py",
        "test/test_health.py",
        "test/test_inference.py",
    ]
    routes_dir = repo / "backend/agent/routes"
    if routes_dir.is_dir():
        for route_file in sorted(routes_dir.glob("*.py")):
            rel = route_file.relative_to(repo).as_posix()
            if rel not in paths:
                paths.append(rel)
    return paths


def list_existing_deliverables(repo: Path) -> str:
    lines = []
    for rel in existing_source_paths(repo):
        p = repo / rel
        if p.exists():
            lines.append(f"- {rel} ({p.stat().st_size} bytes)")
    return "\n".join(lines) if lines else "(none yet)"


def format_existing_sources(repo: Path) -> str:
    """Full source for files on disk — append-only guard for Gemma."""
    if not CAVEMAN_LITE:
        return list_existing_deliverables(repo)

    blocks: list[str] = []
    total = 0
    for rel in existing_source_paths(repo):
        path = repo / rel
        if not path.is_file():
            continue
        text = read_text(path, max_chars=CAVEMAN_SOURCE_MAX_PER_FILE)
        block = f"### {rel}\n```\n{text}\n```"
        if total + len(block) > CAVEMAN_SOURCE_MAX_TOTAL:
            blocks.append("[... more files omitted — budget cap ...]")
            break
        blocks.append(block)
        total += len(block)
    return "\n\n".join(blocks) if blocks else "(none yet)"


def build_user_prompt(repo: Path, slice_id: str, spec_path: Path, *, slim: bool) -> str:
    workload_path = repo / "slicedworkload.md"
    workload = read_text(workload_path)
    blockers = extract_blockers(workload)
    deps_doc = repo / "docs" / "dev" / "dependencies.md"
    spec_text = read_text(
        spec_path,
        max_chars=CAVEMAN_SPEC_MAX_CHARS if CAVEMAN_LITE else None,
    )
    sources = format_existing_sources(repo)

    parts = [f"Slice: {slice_id}", ""]

    if slim and blockers:
        parts.extend(
            [
                "## BLOCKERS (fix first; telegram format)",
                blockers,
                "",
                "## Existing sources (APPEND — keep working code)",
                sources,
                "",
                f"## Spec {spec_path.relative_to(repo)}",
                spec_text,
                "",
                "## slicedworkload.md",
                workload,
            ]
        )
    else:
        parts.extend(
            [
                "## Existing sources (APPEND — keep working code)",
                sources,
                "",
                f"## Spec {spec_path.relative_to(repo)}",
                spec_text,
                "",
                "## slicedworkload.md",
                workload,
            ]
        )
        if blockers:
            parts.extend(["", "## BLOCKERS", blockers])

    if deps_doc.exists():
        deps = read_text(deps_doc)
        parts.extend(["", extract_deps_slice(deps, slice_id)])

    parts.extend(
        [
            "",
            "===FILE: blocks only. Changed files + slicedworkload.md.",
        ]
    )
    return "\n".join(parts)


def parse_file_blocks(response: str) -> list[tuple[str, str]]:
    blocks: list[tuple[str, str]] = []
    for match in FILE_BLOCK_RE.finditer(response):
        path = match.group("path").strip()
        content = match.group("content")
        if content.endswith("\n"):
            content = content[:-1]
        blocks.append((path, content))
    return blocks


def resolve_target(repo: Path, rel_path: str) -> Path:
    rel_path = rel_path.strip().replace("\\", "/")
    while rel_path.startswith("../"):
        rel_path = rel_path[3:]
    if rel_path.startswith("./"):
        rel_path = rel_path[2:]
    target = (repo / rel_path).resolve()
    if not str(target).startswith(str(repo.resolve())):
        raise ValueError(f"Refusing path outside repo: {rel_path}")
    return target


def apply_files(repo: Path, blocks: list[tuple[str, str]], dry_run: bool) -> list[str]:
    written: list[str] = []
    for rel_path, content in blocks:
        target = resolve_target(repo, rel_path)
        if dry_run:
            print(f"[dry-run] would write {rel_path} ({len(content)} bytes)")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            print(f"Wrote {rel_path}")
        written.append(rel_path)
    return written


def pick_model(client: OpenAI, explicit: str | None) -> str:
    if explicit:
        return explicit
    env_model = os.environ.get("OMLX_MODEL")
    if env_model:
        return env_model
    models = client.models.list()
    ids = [m.id for m in models.data]
    if not ids:
        raise RuntimeError("No models returned from /v1/models — load a model in oMLX first.")
    preferred = [m for m in ids if "gemma" in m.lower() and "12" in m.lower()]
    return preferred[0] if preferred else ids[0]


def call_builder(
    client: OpenAI,
    model: str,
    user_prompt: str,
    temperature: float,
    max_tokens: int,
    log_path: Path | None = None,
) -> str:
    stream = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True,
    )
    chunks: list[str] = []
    for event in stream:
        delta = event.choices[0].delta.content or ""
        if delta:
            chunks.append(delta)
            if log_path is not None:
                with log_path.open("a", encoding="utf-8") as f:
                    f.write(delta)
    return "".join(chunks)


def verify_connection(base_url: str, api_key: str) -> None:
    client = OpenAI(base_url=base_url, api_key=api_key)
    models = client.models.list()
    ids = [m.id for m in models.data]
    print(f"oMLX OK @ {base_url}")
    print(f"Models: {', '.join(ids) if ids else '(none — load a model in oMLX)'}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Maestro'D Local Builder — oMLX direct")
    parser.add_argument("--repo", type=Path, default=None, help="Repo root (default: parent of scripts/)")
    parser.add_argument("--base-url", default=os.environ.get("OMLX_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument(
        "--api-key",
        default=DEFAULT_API_KEY,
        help=f"oMLX API key (default: {DEFAULT_API_KEY})",
    )
    parser.add_argument("--model", default=None, help="Model id (default: auto from /v1/models)")
    parser.add_argument("--dry-run", action="store_true", help="Parse blocks but do not write files")
    parser.add_argument("--verify", action="store_true", help="Only test oMLX connection")
    parser.add_argument("--max-turns", type=int, default=1, help="LLM turns (1 = single shot)")
    parser.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS, help="Output token cap (~5 min)")
    parser.add_argument("--full-prompt", action="store_true", help="Include full specsrebuild (default: slim if BLOCKERS)")
    parser.add_argument("--temperature", type=float, default=0.2)
    args = parser.parse_args()

    if args.verify:
        try:
            verify_connection(args.base_url, args.api_key)
        except Exception as exc:
            print(f"Connection failed: {exc}", file=sys.stderr)
            return 1
        return 0

    repo = args.repo or repo_root_from_script()
    if not (repo / "slicedworkload.md").exists():
        print(f"Not a Maestro'D repo: {repo}", file=sys.stderr)
        return 1

    client = OpenAI(base_url=args.base_url, api_key=args.api_key)
    try:
        model = pick_model(client, args.model)
    except Exception as exc:
        print(f"Model discovery failed: {exc}", file=sys.stderr)
        print("Start oMLX on :8002 and load Gemma 4 12B, then: python scripts/local_builder.py --verify")
        return 1

    print(f"Repo: {repo}")
    print(f"Endpoint: {args.base_url}")
    print(f"Model: {model}")

    try:
        slice_id, spec_path = load_active_slice(repo)
    except (FileNotFoundError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 1

    workload_text = (repo / "slicedworkload.md").read_text(encoding="utf-8")
    slim = not args.full_prompt and extract_blockers(workload_text) is not None
    user_prompt = build_user_prompt(repo, slice_id, spec_path, slim=slim)

    mode = "slim+BLOCKERS" if slim else "full"
    if CAVEMAN_LITE:
        mode += " · caveman-lite"
    print(f"Prompt mode: {mode}")
    print(f"Prompt size: {len(user_prompt)} chars")
    print(f"Max output tokens: {args.max_tokens}")

    all_written: list[str] = []
    content = ""
    for turn in range(1, args.max_turns + 1):
        print(f"\n--- Turn {turn}/{args.max_turns} ---")
        print("Calling oMLX (budget ~5 min)...")

        log_path = repo / "scripts" / f"last_builder_response_turn{turn}.md"
        if not args.dry_run:
            log_path.write_text("", encoding="utf-8")

        try:
            if turn == 1:
                content = call_builder(
                    client, model, user_prompt, args.temperature, args.max_tokens,
                    log_path=None if args.dry_run else log_path,
                )
            else:
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                        {"role": "assistant", "content": content},
                        {
                            "role": "user",
                            "content": (
                                "Continue. BLOCKERS only. ===FILE: first. "
                                "Append — do not replace whole files. Zero filler."
                            ),
                        },
                    ],
                    temperature=args.temperature,
                    max_tokens=args.max_tokens,
                )
                content = response.choices[0].message.content or ""
                if not args.dry_run:
                    log_path.write_text(content, encoding="utf-8")
        except Exception as exc:
            print(f"LLM call failed: {exc}", file=sys.stderr)
            return 1

        if not args.dry_run:
            print(f"Response logged: {log_path.relative_to(repo)} ({len(content)} chars)")
            if CAVEMAN_LITE:
                prose = FILE_BLOCK_RE.sub("", content)
                prose = re.sub(r"===END===", "", prose).strip()
                print(f"Caveman prose (non-file): {len(prose)} chars")

        blocks = parse_file_blocks(content)
        if not blocks:
            print("No ===FILE=== blocks found in response.", file=sys.stderr)
            print("Tip: retry with --max-turns 2 or use oMLX Admin Chat with the same prompt.")
            if turn == args.max_turns:
                return 1
            continue

        written = apply_files(repo, blocks, args.dry_run)
        all_written.extend(written)

        if turn < args.max_turns:
            user_prompt = build_user_prompt(repo, slice_id, spec_path)

    print(f"\nDone. {len(all_written)} file(s) {'would be ' if args.dry_run else ''}written.")
    if not args.dry_run:
        print("\nNext steps:")
        print("  1. Review changes: git diff")
        print("  2. Run DoD from active slice spec in docs/specs/")
        print("  3. Switch to Maestro in Cursor for review → VERIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
