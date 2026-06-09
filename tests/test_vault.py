from safecopy_core.detection import detect
from safecopy_core.masking import BLOCKED, mask
from safecopy_core.vault import Vault


def test_roundtrip_persists_encrypted(tmp_path):
    path = tmp_path / "vault.json"
    text = "전화 010-1234-5678"
    mappings = mask(text, detect(text)).mappings

    v = Vault.open(path, passphrase="pw")
    v.store("doc-1", mappings)
    v.save()

    # File on disk must not contain the plaintext original.
    assert "010-1234-5678" not in path.read_text(encoding="utf-8")

    reopened = Vault.open(path, passphrase="pw")
    assert reopened.resolve("doc-1", "[PHONE_001]") == "010-1234-5678"


def test_blocked_secret_not_stored_as_original(tmp_path):
    text = "API_KEY=sk_live_abcdef0123456789ABCD"
    mappings = mask(text, detect(text)).mappings
    v = Vault.open(tmp_path / "vault.json", passphrase="pw")
    v.store("doc-1", mappings)
    token = next(m.token for m in mappings if not m.reversible)
    assert v.resolve("doc-1", token) == BLOCKED


def test_scopes_are_isolated(tmp_path):
    text = "a@b.com"
    mappings = mask(text, detect(text)).mappings
    v = Vault.open(tmp_path / "vault.json", passphrase="pw")
    v.store("app-A", mappings)
    assert v.resolve("app-B", "[EMAIL_001]") is None


def test_delete_scope(tmp_path):
    text = "a@b.com"
    mappings = mask(text, detect(text)).mappings
    v = Vault.open(tmp_path / "vault.json", passphrase="pw")
    v.store("app-A", mappings)
    v.delete("app-A")
    assert v.resolve("app-A", "[EMAIL_001]") is None
