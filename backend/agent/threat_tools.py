from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set

from threat_catalog import ThreatCatalog
from threats_schema import STRIDE_VALUES


@dataclass
class GapResult:
    stop: bool
    findings: List[str] = field(default_factory=list)


def add_threats(catalog: ThreatCatalog, threats_list) -> str:
    added = catalog.add(threats_list)
    return f"Added {added} threats; catalog now has {catalog.count()} threats."


def gap_analysis(
    catalog: ThreatCatalog,
    *,
    asset_names: List[str],
    min_threats: int = 8,
    min_stride_categories: int = 3,
) -> GapResult:
    findings: List[str] = []
    count = catalog.count()
    stride_counts = catalog.stride_counts()
    covered_stride: Set[str] = set(stride_counts.keys())

    if count < min_threats:
        findings.append(f"Need at least {min_threats} threats; catalog has {count}.")

    missing_stride = [value for value in STRIDE_VALUES if value not in covered_stride]
    if len(covered_stride) < min_stride_categories:
        findings.append(
            f"Need at least {min_stride_categories} STRIDE categories; "
            f"missing examples for: {', '.join(missing_stride[:4])}."
        )

    targeted = {threat.target for threat in catalog.to_threats_list().threats}
    for asset in asset_names:
        if asset and asset not in targeted:
            findings.append(f"No threats target asset '{asset}'.")

    if not findings:
        return GapResult(stop=True)

    return GapResult(stop=False, findings=findings)


def build_meta(catalog: ThreatCatalog) -> Dict[str, object]:
    return {
        "threat_count": catalog.count(),
        "stride_counts": catalog.stride_counts(),
    }
