import json
from unittest.mock import patch

from tools import product_photos_tools


def test_list_reference_photos_filters_out_missing_files(tmp_path):
    manifest = [
        {"filename": "exists.jpg", "tags": ["MRL-G"], "description": "..."},
        {"filename": "missing.jpg", "tags": ["HYD"], "description": "..."},
    ]
    (tmp_path / "exists.jpg").write_bytes(b"fake-jpg-bytes")
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with patch.object(product_photos_tools, "_PRODUCT_PHOTOS_DIR", tmp_path):
        with patch.object(product_photos_tools, "_MANIFEST_PATH", manifest_path):
            result = product_photos_tools.list_reference_photos.invoke({})

    assert result == [{"filename": "exists.jpg", "tags": ["MRL-G"], "description": "..."}]


def test_list_reference_photos_returns_empty_when_no_manifest(tmp_path):
    with patch.object(product_photos_tools, "_MANIFEST_PATH", tmp_path / "nope.json"):
        assert product_photos_tools.list_reference_photos.invoke({}) == []


def test_load_reference_photo_rejects_filename_not_in_manifest(tmp_path):
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps([]), encoding="utf-8")

    with patch.object(product_photos_tools, "_PRODUCT_PHOTOS_DIR", tmp_path):
        with patch.object(product_photos_tools, "_MANIFEST_PATH", manifest_path):
            result = product_photos_tools.load_reference_photo("../../etc/passwd")

    assert result is None


def test_load_reference_photo_reads_bytes_for_valid_filename(tmp_path):
    manifest = [{"filename": "real.jpg", "tags": [], "description": "..."}]
    (tmp_path / "real.jpg").write_bytes(b"real-bytes")
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with patch.object(product_photos_tools, "_PRODUCT_PHOTOS_DIR", tmp_path):
        with patch.object(product_photos_tools, "_MANIFEST_PATH", manifest_path):
            result = product_photos_tools.load_reference_photo("real.jpg")

    assert result == b"real-bytes"
