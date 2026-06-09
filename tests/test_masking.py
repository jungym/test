from safecopy_core.detection import detect
from safecopy_core.masking import BLOCKED, mask


def test_masks_phone_reversibly():
    text = "전화 010-1234-5678"
    result = mask(text, detect(text))
    assert "[PHONE_001]" in result.masked_text
    phone = next(m for m in result.mappings if m.token == "[PHONE_001]")
    assert phone.reversible
    assert phone.original == "010-1234-5678"


def test_blocks_api_key_without_storing_original():
    text = "API_KEY=sk_live_abcdef0123456789ABCD"
    result = mask(text, detect(text))
    blocked = [m for m in result.mappings if not m.reversible]
    assert blocked, "expected the secret to be blocked"
    assert all(m.original == BLOCKED for m in blocked)
    assert "BLOCKED" in result.masked_text


def test_tokens_numbered_per_type():
    text = "a@x.com, b@y.com"
    result = mask(text, detect(text))
    assert "[EMAIL_001]" in result.masked_text
    assert "[EMAIL_002]" in result.masked_text
