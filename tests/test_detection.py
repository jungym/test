from safecopy_core.detection import DataType, RiskLevel, detect


def test_detects_email_and_phone():
    findings = detect("연락처: hong@example.com / 010-1234-5678")
    types = {f.data_type for f in findings}
    assert DataType.EMAIL in types
    assert DataType.PHONE in types


def test_detects_api_key_as_critical():
    findings = detect("API_KEY=sk_live_abcdef0123456789ABCD")
    # The assignment is matched; the value carries CRITICAL risk.
    assert any(f.risk is RiskLevel.CRITICAL for f in findings)


def test_detects_korean_rrn():
    findings = detect("주민번호 900101-1234567 입니다")
    assert any(f.data_type is DataType.RRN for f in findings)


def test_findings_are_non_overlapping_and_sorted():
    findings = detect("a@b.com 010-1234-5678")
    for prev, nxt in zip(findings, findings[1:], strict=False):
        assert prev.end <= nxt.start


def test_ssh_private_key_block():
    text = (
        "-----BEGIN OPENSSH PRIVATE KEY-----\n"
        "b3BlbnNzaC1rZXktdjEAAAAA\n"
        "-----END OPENSSH PRIVATE KEY-----"
    )
    findings = detect(text)
    assert any(f.data_type is DataType.SSH_PRIVATE_KEY for f in findings)
