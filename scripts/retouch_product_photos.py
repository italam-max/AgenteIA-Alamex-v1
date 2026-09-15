"""
One-time (or re-run when raw/ changes) batch job: takes every raw photo in
brand/product_photos/raw/, cuts the product out of its original background (rembg —
deterministic segmentation, never redraws the product) and composites it onto a clean studio
gradient with a soft grounding shadow. Overwrites the matching filename (as .png) at
brand/product_photos/ root and updates manifest.json if the extension changed.

Usage:
    python scripts/retouch_product_photos.py                 # procesa todo raw/
    python scripts/retouch_product_photos.py nombre.jpg       # procesa solo ese archivo de raw/
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

    only_filename = sys.argv[1] if len(sys.argv) > 1 else None
    if only_filename:
        raw_paths = [_RAW_DIR / only_filename]
        if not raw_paths[0].exists():
            print(f"No existe {raw_paths[0]}")
            sys.exit(1)
    else:
        raw_paths = sorted(p for p in _RAW_DIR.iterdir() if p.is_file())

    manifest = json.loads(_MANIFEST_PATH.read_text(encoding="utf-8")) if _MANIFEST_PATH.exists() else []
    manifest_by_stem = {Path(entry["filename"]).stem: entry for entry in manifest}

    for raw_path in raw_paths:
        stem = raw_path.stem
        print(f"Procesando {raw_path.name}...")
        retouched_bytes = retouch_product_photo(raw_path.read_bytes())

        out_path = _PRODUCT_PHOTOS_DIR / f"{stem}.png"
        out_path.write_bytes(retouched_bytes)
        print(f"  -> {out_path}")

        entry = manifest_by_stem.get(stem)
        if entry is not None:
            entry["filename"] = out_path.name
        else:
            # New photo with no manifest entry yet (e.g. just uploaded) — add a placeholder;
            # whoever called this (a human, or the dashboard's upload endpoint) fills in real
            # tags/description afterward by editing manifest.json directly.
            new_entry = {"filename": out_path.name, "tags": [], "description": ""}
            manifest.append(new_entry)
            manifest_by_stem[stem] = new_entry

    _MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nmanifest.json actualizado ({len(manifest)} entradas).")


if __name__ == "__main__":
    main()
