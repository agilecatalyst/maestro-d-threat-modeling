"""Apply threat catalog mutations and rebuild metadata."""

from __future__ import annotations

from typing import List, Literal

from pydantic import BaseModel, Field

ThreatOp = Literal["add", "update", "delete", "replace"]

STRIDE_VALUES = [
    "Spoofing",
    "Tampering",
    "Repudiation",
    "Information Disclosure",
    "Denial of Service",
    "Elevation of Privilege",
]


class ThreatItem(BaseModel):
    name: str
    stride_category: str
    description: str
    target: str
    source: str
    likelihood: str
    impact: str
    mitigations: List[str] = Field(min_length=1)
    prerequisites: List[str] = Field(default_factory=list)
    vector: str


def rebuild_meta(threats: List[dict]) -> dict:
    stride_counts: dict[str, int] = {}
    for threat in threats:
        category = threat.get("stride_category") or "Unknown"
        stride_counts[category] = stride_counts.get(category, 0) + 1
    return {"threat_count": len(threats), "stride_counts": stride_counts}


def apply_mutation(
    existing: List[dict],
    op: ThreatOp,
    threats: List[dict],
) -> List[dict]:
    if op == "replace":
        return list(threats)

    if op == "add":
        names = {row["name"] for row in existing}
        merged = list(existing)
        for row in threats:
            if row["name"] not in names:
                merged.append(row)
                names.add(row["name"])
        return merged

    if op == "update":
        updates = {row["name"]: row for row in threats}
        merged: List[dict] = []
        for row in existing:
            if row["name"] in updates:
                merged.append(updates[row["name"]])
            else:
                merged.append(row)
        for row in threats:
            if row["name"] not in {item["name"] for item in existing}:
                merged.append(row)
        return merged

    if op == "delete":
        remove = {row["name"] for row in threats}
        return [row for row in existing if row["name"] not in remove]

    raise ValueError(f"Unknown op: {op}")
