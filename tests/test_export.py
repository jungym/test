"""Tests for Review Gate 4 Item 2 — dossier artifact export."""

import json

import pytest

from haen.export import export_dossier, sha256_text
from haen.report_builder import build_dossier
from haen.sample_data import build_sample_components, build_sample_fleet

FIXED_TS = "2026-01-01T00:00:00+00:00"


def _dossier(generated_at=FIXED_TS):
    return build_dossier(
        programme="HAEN GT-1",
        branch="GT-1",
        vehicles=build_sample_fleet(),
        components=build_sample_components(),
        generated_at=generated_at,
    )


def test_export_writes_files(tmp_path):
    res = export_dossier(_dossier(), tmp_path, programme="HAEN GT-1", branch="GT-1",
                         generated_at=FIXED_TS)
    assert res.dossier_path.exists()
    assert res.metadata_path.exists()
    assert res.dossier_path.name == "dossier.md"
    assert res.metadata_path.name == "dossier.meta.json"


def test_metadata_is_internal_and_review_required(tmp_path):
    res = export_dossier(_dossier(), tmp_path, programme="HAEN GT-1", branch="GT-1",
                         commit="abc1234", generated_at=FIXED_TS)
    meta = json.loads(res.metadata_path.read_text())
    assert meta["human_review_required"] is True
    assert meta["external_release_allowed"] is False
    assert meta["internal_only"] is True
    assert meta["branch"] == "GT-1"
    assert meta["commit"] == "abc1234"
    assert meta["report_version"]
    assert meta["generated_at"] == FIXED_TS


def test_checksum_matches_content(tmp_path):
    res = export_dossier(_dossier(), tmp_path, programme="HAEN GT-1", branch="GT-1",
                         generated_at=FIXED_TS)
    meta = json.loads(res.metadata_path.read_text())
    assert meta["dossier_sha256"] == sha256_text(res.dossier_path.read_text())


def test_forbidden_claim_refused(tmp_path):
    bad = "# Dossier\n\nThis vehicle is road legal and crash safe."
    with pytest.raises(ValueError):
        export_dossier(bad, tmp_path, programme="P", branch="GT-1", generated_at=FIXED_TS)
    # nothing written
    assert not (tmp_path / "dossier.md").exists()


def test_deterministic_export(tmp_path):
    a = export_dossier(_dossier(), tmp_path / "a", programme="HAEN GT-1", branch="GT-1",
                       generated_at=FIXED_TS)
    b = export_dossier(_dossier(), tmp_path / "b", programme="HAEN GT-1", branch="GT-1",
                       generated_at=FIXED_TS)
    assert a.dossier_path.read_bytes() == b.dossier_path.read_bytes()
    assert a.files["dossier.md"] == b.files["dossier.md"]
