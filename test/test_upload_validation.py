import sys
from pathlib import Path

API_DIR = Path(__file__).resolve().parent.parent / "backend" / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from upload_validation import detect_image_extension


def test_detect_png():
    assert detect_image_extension(b"\x89PNG\r\n\x1a\n\x00") == "png"


def test_detect_jpeg():
    assert detect_image_extension(b"\xff\xd8\xff\xe0") == "jpg"


def test_reject_non_image():
    assert detect_image_extension(b"not-an-image") is None
