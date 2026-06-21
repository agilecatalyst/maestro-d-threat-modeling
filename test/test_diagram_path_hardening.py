import sys
from pathlib import Path

API_DIR = Path(__file__).resolve().parent.parent / "backend" / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

import pytest

from storage import assert_safe_diagram_relative_path, resolve_diagram_path


def test_api_rejects_path_traversal():
    with pytest.raises(ValueError):
        assert_safe_diagram_relative_path("../../etc/passwd")


def test_api_rejects_absolute_path():
    with pytest.raises(ValueError):
        assert_safe_diagram_relative_path("/etc/passwd")


def test_api_accepts_nested_relative_path():
    assert_safe_diagram_relative_path("diagrams/sample.png")


def test_resolve_rejects_escape():
    with pytest.raises(ValueError):
        resolve_diagram_path("../outside.png")
