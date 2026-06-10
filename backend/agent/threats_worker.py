import json
import logging
from typing import List, Optional

from sqlalchemy import text

from db import SessionLocal, merge_job_detail
from threat_catalog import ThreatCatalog
from threat_tools import build_meta
from threats_subgraph import run_threats_subgraph
from threats_schema import Threat, ThreatsList

logger = logging.getLogger(__name__)


def _load_detail(job_id: str) -> dict:
    db = SessionLocal()
    try:
        row = db.execute(
            text("SELECT detail FROM job_status WHERE id = :id"),
            {"id": str(job_id)},
        ).fetchone()
        return json.loads(row[0]) if row and row[0] else {}
    finally:
        db.close()


def _default_source(flows: dict) -> str:
    sources = flows.get("threat_sources") or []
    if sources:
        return sources[0].get("category", "External Threat Actors")
    return "External Threat Actors"


def _fallback_threats(summary: str, assets: list, flows: dict) -> ThreatsList:
    source = _default_source(flows)
    names = [item.get("name") for item in assets if item.get("name")] or ["System"]
    while len(names) < 3:
        names.append(names[-1])
    stride_cycle = ["Tampering", "Information Disclosure", "Denial of Service"]
    threats: List[Threat] = []
    for index, name in enumerate(names[:3]):
        stride = stride_cycle[index % len(stride_cycle)]
        suffix = "" if index == 0 else f" ({stride})"
        threats.append(
            Threat(
                name=f"Unauthorized access to {name}{suffix}",
                stride_category=stride,
                description=(
                    f"[{source}] [network access] can compromise {name} which leads to "
                    f"data or service impact, negatively impacting {name}."
                ),
                target=name,
                source=source,
                likelihood="Medium",
                impact=f"Compromise of {name} affects confidentiality, integrity, or availability.",
                mitigations=["Apply least privilege access controls", "Enable monitoring and alerting"],
                prerequisites=["Network reachability to the component"],
                vector="Application or network interface",
            )
        )
    if not threats:
        threats.append(
            Threat(
                name="Generic application compromise",
                stride_category="Tampering",
                description=(
                    f"[{source}] [exposed interface] can alter application behavior which "
                    "leads to integrity loss, negatively impacting the system."
                ),
                target="System",
                source=source,
                likelihood="Medium",
                impact="Integrity and availability degradation.",
                mitigations=["Harden exposed interfaces", "Apply input validation"],
                prerequisites=["Reachable application endpoint"],
                vector="Public application interface",
            )
        )
    return ThreatsList(threats=threats)


def run_threats(job_id: str, description: Optional[str] = None):
    try:
        detail = _load_detail(job_id)
        summary = detail.get("summary", description or "")
        assets = detail.get("assets", [])
        flows = detail.get("flows", {})

        catalog = run_threats_subgraph(summary, assets, flows)
        if catalog.count() < 3:
            logger.warning("Threats agent produced %s threats; using fallback", catalog.count())
            catalog = ThreatCatalog()
            catalog.add(_fallback_threats(summary, assets, flows))

        merge_job_detail(
            job_id,
            "THREATS_DONE",
            threats=catalog.to_dicts(),
        )
    except Exception as exc:
        logger.error("Threats worker failed for job %s: %s", job_id, exc)
        merge_job_detail(job_id, "FAILED", error=str(exc))


def run_finalize(job_id: str):
    detail = _load_detail(job_id)
    threats = detail.get("threats", [])
    catalog = ThreatCatalog()
    if threats:
        try:
            catalog.add(ThreatsList(threats=[Threat(**row) for row in threats]))
        except Exception:
            pass

    merge_job_detail(
        job_id,
        "COMPLETE",
        meta=build_meta(catalog) if catalog.count() else {"threat_count": len(threats)},
    )
