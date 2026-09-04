import json
from pathlib import Path

from langchain_core.tools import tool

_PRODUCT_PHOTOS_DIR = Path(__file__).resolve().parent.parent / "brand" / "product_photos"
_MANIFEST_PATH = _PRODUCT_PHOTOS_DIR / "manifest.json"


@tool
def list_reference_photos() -> list[dict]:
    """
    List real Alamex product/installation photos available as `reference_photo` for a post
    (brand/product_photos/). Each item: {filename, tags, description}. Only entries whose file
    actually exists on disk are returned — a stale manifest entry can't be picked.
    """
    if not _MANIFEST_PATH.exists():
        return []
    entries = json.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))
    return [entry for entry in entries if (_PRODUCT_PHOTOS_DIR / entry["filename"]).exists()]


def load_reference_photo(filename: str) -> bytes | None:
    """Read a reference photo's bytes by filename, validating it's a real manifest entry first —
    never trust an LLM-provided filename as a raw path (directory traversal, arbitrary reads)."""
    valid_filenames = {entry["filename"] for entry in list_reference_photos.invoke({})}
    if filename not in valid_filenames:
        return None
    return (_PRODUCT_PHOTOS_DIR / filename).read_bytes()
