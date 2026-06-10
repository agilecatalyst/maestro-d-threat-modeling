"""PDF and JSON export for threat models."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
COLOPHON_PATH = Path(__file__).resolve().parent.parent / "colophon.txt"
NOTICE_PATH = Path(__file__).resolve().parent.parent.parent.parent / "NOTICE"


def _notice_lines() -> list[str]:
    for path in (COLOPHON_PATH, NOTICE_PATH):
        if path.is_file():
            return [line.rstrip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return ["Maestro'D ThreatModeling"]


def render_json_export(document: dict) -> bytes:
    payload = {
        **document,
        "exported_at": datetime.now(timezone.utc).isoformat(),
    }
    return json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")


def render_pdf_export(document: dict) -> bytes:
    from weasyprint import HTML

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("report.html")
    html = template.render(
        doc=document,
        exported_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        notice_lines=_notice_lines(),
    )
    return HTML(string=html, base_url=str(TEMPLATES_DIR)).write_pdf()
