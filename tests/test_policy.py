from safecopy_core.detection import detect
from safecopy_core.policy import Action, Destination, evaluate


def test_api_key_to_ai_is_blocked():
    findings = detect("API_KEY=sk_live_abcdef0123456789ABCD")
    decision = evaluate(findings, Destination.AI)
    assert decision.action is Action.BLOCK


def test_phone_to_ai_is_masked():
    findings = detect("내 번호 010-1234-5678")
    decision = evaluate(findings, Destination.AI)
    assert decision.action is Action.MASK


def test_decision_is_most_restrictive_across_findings():
    findings = detect("hong@example.com 그리고 API_KEY=sk_live_abcdef0123456789ABCD")
    decision = evaluate(findings, Destination.AI)
    # email -> MASK, api key -> BLOCK; the payload as a whole is BLOCK.
    assert decision.action is Action.BLOCK


def test_no_findings_is_allow():
    decision = evaluate(detect("안녕하세요 평범한 문장입니다"), Destination.AI)
    assert decision.action is Action.ALLOW
