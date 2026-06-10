"""Tests for Review Gate 5 Item 8 — expanded Korean forbidden-claim coverage."""

import pytest

from haen.governance import check_text


@pytest.mark.parametrize(
    "text",
    [
        "도로 주행 가능 인증",      # road legal (FC-001)
        "합법 주행",               # road legal
        "형식 인증 완료",          # homologation (FC-002)
        "충돌 안전성 검증 완료",     # crash safe (FC-003)
        "대량 생산 가능",          # production (FC-004)
        "공급 확정",               # supplier (FC-005)
        "납품 확정",               # supplier
        "디자인 완료",             # design complete (FC-006)
        "인증 획득",               # certification (FC-007)
        "승인 완료",               # certification/approval
        "공력 검증 완료",          # CFD-adjacent (FC-008)
        "전산 유체 해석 검증 완료",  # CFD (FC-008)
        "충돌 시험 통과",          # crash sim (FC-009)
        "디지털 트윈 검증",        # digital twin (FC-010)
    ],
)
def test_new_korean_claims_blocked(text):
    assert check_text(text), f"expected Korean claim blocked: {text!r}"


@pytest.mark.parametrize(
    "text",
    [
        "인증 미완료",
        "충돌 안전성 미검증",
        "승인 안 됨",
        "양산 불가",
        "설계 미완료",
    ],
)
def test_korean_negations_not_flagged(text):
    assert check_text(text) == [], f"safe Korean framing must not be flagged: {text!r}"


def test_existing_english_checks_still_pass():
    for c in ["road legal", "crash safe", "supplier confirmed", "CFD validated",
              "certification ready", "digital twin complete"]:
        assert check_text(f"It is {c}.")
    # safe English noun-form framings remain clean
    assert check_text("road-legality not assessed") == []
    assert check_text("certification status: not assessed") == []
