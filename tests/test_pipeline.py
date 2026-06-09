from safecopy_core.audit import AuditLog
from safecopy_core.config import Settings
from safecopy_core.pipeline import Guard
from safecopy_core.policy import Action, Destination
from safecopy_core.vault import Vault


def _guard(tmp_path):
    settings = Settings(data_dir=tmp_path)
    vault = Vault.open(settings.vault_path, passphrase="pw")
    audit = AuditLog(settings.audit_path)
    return Guard(vault, audit, settings), settings


def test_masking_path_stores_mapping_and_audits(tmp_path):
    guard, settings = _guard(tmp_path)
    result = guard.inspect(
        "내 번호 010-1234-5678", destination=Destination.AI, app="chat", scope="doc-1"
    )
    assert result.action is Action.MASK
    assert result.safe_text is not None and "[PHONE_001]" in result.safe_text
    assert settings.audit_path.exists()


def test_block_path_does_not_mask(tmp_path):
    guard, _ = _guard(tmp_path)
    result = guard.inspect(
        "API_KEY=sk_live_abcdef0123456789ABCD", destination=Destination.AI, app="chat"
    )
    assert result.action is Action.BLOCK
    assert result.safe_text is None


def test_audit_does_not_store_originals_by_default(tmp_path):
    guard, settings = _guard(tmp_path)
    guard.inspect("a@b.com", destination=Destination.AI, app="chat")
    contents = settings.audit_path.read_text(encoding="utf-8")
    assert "a@b.com" not in contents
