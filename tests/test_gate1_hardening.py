"""Review Gate 1 hardening tests.

Covers the forbidden claims added in Gate 1 (certification ready, CFD validated,
crash simulation complete, digital twin complete), hyphenated and Korean
variants, false-positive guards for the recommended safe framings, the
low-fidelity top-speed plausibility warning, and dossier safety wording.
"""

import pytest

from haen import low_fidelity_simulation as sim
from haen.governance import check_text
from haen.report_builder import build_dossier
from haen.sample_data import build_sample_fleet


# --------------------------------------------------------------------------- #
# Forbidden-claim coverage (Gate 1 required list)
# --------------------------------------------------------------------------- #
GATE1_REQUIRED = [
    "road legal",
    "homologation ready",
    "crash safe",
    "production feasible",
    "supplier confirmed",
    "design complete",
    "certification ready",
    "CFD validated",
    "crash simulation complete",
    "digital twin complete",
]


@pytest.mark.parametrize("claim", GATE1_REQUIRED)
def test_required_claims_blocked(claim):
    assert check_text(f"The vehicle is {claim}."), f"{claim!r} must be blocked"


@pytest.mark.parametrize(
    "text",
    [
        "road-legal",
        "crash-safe",
        "production-ready",
        "CFD-validated",
        "crash-simulation complete",
        "digital-twin validated",
        "type-approved",
        "certification-ready",
    ],
)
def test_hyphenated_variants_blocked(text):
    assert check_text(text), f"hyphenated form {text!r} must be blocked"


@pytest.mark.parametrize(
    "text",
    [
        "양산 가능",
        "양산가능",
        "인증 완료",
        "충돌 해석 완료",
        "충돌 시뮬레이션 완료",
        "설계 완료",
        "디지털 트윈 구축 완료",
        "공급사 확정",
        "CFD 검증 완료",
        "도로 주행 합법",
        "충돌 안전성 확보",
    ],
)
def test_korean_variants_blocked(text):
    assert check_text(text), f"Korean form {text!r} must be blocked"


@pytest.mark.parametrize(
    "text",
    [
        "road-legality not assessed",
        "crashworthiness not evaluated",
        "certification status: not assessed",
        "CFD not performed",
        "crash simulation not performed",
        "not a validated digital twin",
        "this is not a validated digital twin",
        "screening models only; not a validated digital twin",
        "인증 미완료",
        "충돌 안전성 미평가",
        "설계 미완료",
    ],
)
def test_recommended_safe_framings_not_blocked(text):
    assert check_text(text) == [], f"safe framing {text!r} must NOT be flagged"


def test_affirmative_validated_digital_twin_still_blocked():
    assert check_text("we delivered a validated digital twin")
    assert check_text("digital twin validated")


# --------------------------------------------------------------------------- #
# Low-fidelity simulation caveats
# --------------------------------------------------------------------------- #
def test_bev_top_speed_flagged_as_artifact():
    fleet = {v.id: v for v in build_sample_fleet()}
    r = sim.simulate(fleet["GT-1-c01"])
    assert r.top_speed_kph > sim.TOP_SPEED_PLAUSIBILITY_KPH
    assert r.top_speed_is_artifact is True
    assert r.warnings, "implausible top speed must carry a screening warning"
    assert "ARTIFACT" in r.warnings[0].upper()
    assert "not a real-world prediction" in r.warnings[0].lower()


def test_plausible_top_speed_has_no_warning():
    fleet = {v.id: v for v in build_sample_fleet()}
    r = sim.simulate(fleet["GT-1H-c01"])  # ~330 km/h, below the bound
    assert r.top_speed_is_artifact is False
    assert r.warnings == ()


# --------------------------------------------------------------------------- #
# Dossier safety wording
# --------------------------------------------------------------------------- #
def test_dossier_declares_not_performed_statuses():
    text = build_dossier(programme="P", branch="GT-1", vehicles=build_sample_fleet())
    assert check_text(text) == []  # governance gate
    for required_phrase in [
        "Certification status: **not assessed**",
        "Crash simulation: **not performed**",
        "CFD not performed",
        "Thermal behaviour: **not modelled**",
        "not a validated digital twin",
        "watch branch only",
    ]:
        assert required_phrase in text, f"dossier must declare: {required_phrase!r}"


def test_dossier_flags_top_speed_artifact():
    text = build_dossier(programme="P", branch="GT-1", vehicles=build_sample_fleet())
    assert "[!]" in text
    # Gate 2 Item 5: braking/load-transfer/CG are now provided as separate
    # low-fidelity screening (section 4a), explicitly not dynamics validation.
    assert "not vehicle-dynamics validation" in text
    assert "Dynamics screening" in text
