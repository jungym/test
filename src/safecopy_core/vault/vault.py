"""Local encrypted Vault for token <-> original mappings.

Principles from the spec (4.4):
  - 클라우드 전송 없음: storage is a local file only.
  - 기본값 로컬 저장: mappings persist locally, encrypted at rest.
  - 사용자 삭제 가능: ``delete``/``clear`` remove entries.
  - 앱별/문서별 매핑 분리: entries are namespaced by ``scope``.
  - Blocked secrets are never stored (their Vault value is the BLOCKED marker).

Encryption: a Fernet key is derived from a master passphrase with PBKDF2-HMAC
-SHA256 over a per-vault random salt. The plaintext mapping table is JSON,
encrypted as a single blob. This is deliberately simple for the MVP; a future
version may switch to per-record encryption.
"""

from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass
from pathlib import Path

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from ..masking.engine import BLOCKED, Mapping

_KDF_ITERATIONS = 480_000
_SALT_BYTES = 16


@dataclass
class _VaultFile:
    salt: bytes
    blob: bytes  # Fernet-encrypted JSON

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "salt": base64.b64encode(self.salt).decode(),
            "blob": base64.b64encode(self.blob).decode(),
        }
        path.write_text(json.dumps(payload), encoding="utf-8")

    @staticmethod
    def read(path: Path) -> _VaultFile:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return _VaultFile(
            salt=base64.b64decode(payload["salt"]),
            blob=base64.b64decode(payload["blob"]),
        )


def _derive_key(passphrase: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=_KDF_ITERATIONS,
    )
    return base64.urlsafe_b64encode(kdf.derive(passphrase.encode("utf-8")))


class Vault:
    """An encrypted, scope-namespaced token store backed by a local file.

    Open with :meth:`open`. The in-memory table is ``{scope: {token: original}}``;
    call :meth:`save` to persist. Reversible mappings are stored; mappings
    flagged blocked are recorded only as the :data:`BLOCKED` marker.
    """

    def __init__(self, path: Path, key: bytes, salt: bytes, table: dict[str, dict[str, str]]):
        self._path = path
        self._fernet = Fernet(key)
        self._salt = salt
        self._table = table

    @classmethod
    def open(cls, path: Path, passphrase: str) -> Vault:
        """Open an existing vault or create a new empty one at ``path``."""
        if path.exists():
            vf = _VaultFile.read(path)
            key = _derive_key(passphrase, vf.salt)
            table = json.loads(Fernet(key).decrypt(vf.blob).decode("utf-8"))
            return cls(path, key, vf.salt, table)

        salt = os.urandom(_SALT_BYTES)
        key = _derive_key(passphrase, salt)
        return cls(path, key, salt, {})

    def store(self, scope: str, mappings: list[Mapping]) -> None:
        """Persist reversible mappings under ``scope``; blocked ones as markers."""
        bucket = self._table.setdefault(scope, {})
        for m in mappings:
            bucket[m.token] = m.original if m.reversible else BLOCKED

    def resolve(self, scope: str, token: str) -> str | None:
        """Return the original for ``token`` in ``scope`` (or None)."""
        return self._table.get(scope, {}).get(token)

    def delete(self, scope: str) -> None:
        """Remove all mappings for ``scope`` (사용자 삭제 가능)."""
        self._table.pop(scope, None)

    def clear(self) -> None:
        self._table.clear()

    def save(self) -> None:
        blob = self._fernet.encrypt(json.dumps(self._table, ensure_ascii=False).encode("utf-8"))
        _VaultFile(salt=self._salt, blob=blob).write(self._path)
