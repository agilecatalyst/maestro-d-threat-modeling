"""Validate uploaded diagram bytes (magic numbers, not just Content-Type)."""

from typing import Optional

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
JPEG_SIGNATURE = b"\xff\xd8\xff"


def detect_image_extension(content: bytes) -> Optional[str]:
    if content.startswith(PNG_SIGNATURE):
        return "png"
    if content.startswith(JPEG_SIGNATURE):
        return "jpg"
    return None
