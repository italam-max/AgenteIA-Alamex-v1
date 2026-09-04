"""
One-time (or re-run when raw/ changes) batch job: takes every raw photo in
brand/product_photos/raw/, cuts the product out of its original background (rembg —
deterministic segmentation, never redraws the product) and composites it onto a clean studio
gradient with a soft grounding shadow. Overwrites the matching filename (as .png) at
brand/product_photos/ root and updates manifest.json if the extension changed.

Usage:
    python scripts/retouch_product_photos.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from integrations.media.product_retouch import retouch_product_photo

_PRODUCT_PHOTOS_DIR = Path(__file__).resolve().parent.parent / "brand" / "product_photos"
_RAW_DIR = _PRODUCT_PHOTOS_DIR / "raw"
_MANIFEST_PATH = _PRODUCT_PHOTOS_DIR / "manifest.json"


def main() -> None:
    if not _RAW_DIR.exists():
        print(f"No hay carpeta {_RAW_DIR} — nada que procesar.")
        return

    manifest = json.loads(_MANIFEST_PATH.read_text(encoding="utf-8")) if _MANIFEST_PATH.exists() else []
    manifest_by_stem = {Path(entry["filename"]).stem: entry for entry in manifest}

    for raw_path in sorted(_RAW_DIR.iterdir()):
        if not raw_path.is_file():
            continue
        stem = raw_path.stem
        print(f"Procesando {raw_path.name}...")
        retouched_bytes = retouch_product_photo(raw_path.read_bytes())

        out_path = _PRODUCT_PHOTOS_DIR / f"{stem}.png"
        out_path.write_bytes(retouched_bytes)
        print(f"  -> {out_path}")

        entry = manifest_by_stem.get(stem)
        if entry is not None:
            entry["filename"] = out_path.name

    _MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nmanifest.json actualizado ({len(manifest)} entradas).")


if __name__ == "__main__":
    main()
