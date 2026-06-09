"""Tests for HAEN partner/supplier engagement statuses and partner RFI items.

Verifies the named entities carry the correct (non-confirmed) engagement status,
that RFI questions are generated for RFI candidates only, and that no
supplier-confirmed claim is introduced.
"""

from haen.governance import check_text
from haen.rfi_builder import build_rfi
from haen.sample_data import build_sample_partners
from haen.supplier_evidence import EngagementStatus, Partner


def _by_name():
    return {p.name: p for p in build_sample_partners()}


def test_hylium_is_rfi_candidate_level1_not_confirmed():
    h = _by_name()["Hylium"]
    assert h.engagement_status is EngagementStatus.RFI_CANDIDATE
    assert h.rfi_level == 1
    # status is "RFI candidate", which is not a confirmation/selection
    assert h.engagement_status is not EngagementStatus.NONE
    # the note does not introduce a forbidden "supplier confirmed" claim
    assert check_text(h.notes) == []


def test_cryos_dalim_parity_are_watch_branch():
    p = _by_name()
    for name in ["Cryos", "DALIM", "Parity"]:
        assert p[name].engagement_status is EngagementStatus.WATCH_BRANCH


def test_kimm_is_technology_observation():
    assert _by_name()["KIMM"].engagement_status is EngagementStatus.TECHNOLOGY_OBSERVATION


def test_rfi_generated_for_rfi_candidates_only():
    rfi = build_rfi(title="t", branch="all", partners=build_sample_partners())
    partner_items = [i for i in rfi.items if i.ref.startswith("P-")]
    # exactly one RFI-candidate partner (Hylium) -> one partner item
    assert len(partner_items) == 1
    assert "Hylium" in partner_items[0].topic
    assert "RFI Level 1" in partner_items[0].topic


def test_watch_and_observation_partners_not_contacted():
    rfi = build_rfi(title="t", branch="all", partners=build_sample_partners())
    topics = " ".join(i.topic for i in rfi.items)
    for name in ["Cryos", "DALIM", "Parity", "KIMM"]:
        assert name not in topics


def test_rfi_markdown_has_no_forbidden_claims():
    rfi = build_rfi(title="t", branch="all", partners=build_sample_partners())
    assert check_text(rfi.to_markdown()) == []


def test_partner_rfi_level_validation():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        Partner(name="X", engagement_status=EngagementStatus.RFI_CANDIDATE, rfi_level=0)
