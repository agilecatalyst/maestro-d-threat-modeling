"""Unit tests for threat mutation helpers."""

import sys
from pathlib import Path

API_DIR = Path(__file__).resolve().parent.parent / "backend" / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from services.threat_mutations import apply_mutation, rebuild_meta


def test_rebuild_meta_stride_counts():
    meta = rebuild_meta(
        [
            {"stride_category": "Tampering"},
            {"stride_category": "Tampering"},
            {"stride_category": "Spoofing"},
        ]
    )
    assert meta["threat_count"] == 3
    assert meta["stride_counts"]["Tampering"] == 2


def test_apply_mutation_add_update_delete():
    base = [{"name": "A", "stride_category": "Tampering"}]
    added = apply_mutation(base, "add", [{"name": "B", "stride_category": "Spoofing"}])
    assert len(added) == 2

    updated = apply_mutation(
        added,
        "update",
        [{"name": "A", "stride_category": "Information Disclosure"}],
    )
    assert updated[0]["stride_category"] == "Information Disclosure"

    deleted = apply_mutation(updated, "delete", [{"name": "B"}])
    assert len(deleted) == 1
    assert deleted[0]["name"] == "A"
