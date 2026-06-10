from __future__ import annotations

from typing import Dict, List

from threats_schema import Threat, ThreatsList


class ThreatCatalog:
    def __init__(self) -> None:
        self._by_name: Dict[str, Threat] = {}

    def add(self, threats: ThreatsList) -> int:
        added = 0
        for threat in threats.threats:
            key = threat.name.strip().lower()
            if not key or key in self._by_name:
                continue
            self._by_name[key] = threat
            added += 1
        return added

    def count(self) -> int:
        return len(self._by_name)

    def names(self) -> List[str]:
        return [threat.name for threat in self._by_name.values()]

    def to_threats_list(self) -> ThreatsList:
        return ThreatsList(threats=list(self._by_name.values()))

    def to_dicts(self) -> List[dict]:
        return [threat.model_dump() for threat in self._by_name.values()]

    def stride_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for threat in self._by_name.values():
            counts[threat.stride_category] = counts.get(threat.stride_category, 0) + 1
        return counts
