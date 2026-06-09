"""The end-to-end SafeCopy pipeline that ties the stages together.

    detect -> evaluate (policy) -> mask -> vault.store + audit.record

This is the single place that orchestrates a copy/paste interception. The
clipboard monitor and UI call :meth:`Guard.inspect`; everything it needs is
injected (vault, audit log, settings) so the orchestration stays testable and
free of global state.
"""

from __future__ import annotations

from dataclasses import dataclass

from .audit import AuditLog
from .config import Settings
from .detection import Finding, detect
from .masking import MaskResult, mask
from .policy import Action, Decision, Destination, evaluate
from .vault import Vault


@dataclass(frozen=True)
class InspectionResult:
    """Outcome of inspecting one clipboard/paste payload."""

    decision: Decision
    findings: list[Finding]
    mask_result: MaskResult | None  # None when nothing was masked

    @property
    def action(self) -> Action:
        return self.decision.action

    @property
    def safe_text(self) -> str | None:
        """Masked text to use in place of the original, if masking applied."""
        return self.mask_result.masked_text if self.mask_result else None


class Guard:
    """Inspect outbound text and apply detection -> policy -> masking + logging."""

    def __init__(self, vault: Vault, audit: AuditLog, settings: Settings | None = None):
        self._vault = vault
        self._audit = audit
        self._settings = settings or Settings()

    def inspect(
        self,
        text: str,
        *,
        destination: Destination,
        app: str,
        scope: str = "default",
        user_choice: str | None = None,
    ) -> InspectionResult:
        findings = detect(text)
        decision = evaluate(findings, destination)

        mask_result: MaskResult | None = None
        if decision.action is Action.MASK and findings:
            mask_result = mask(text, findings)
            self._vault.store(scope, mask_result.mappings)
            self._vault.save()

        self._audit.record(
            app=app,
            destination=destination.value,
            data_types=decision.data_types,
            action=decision.action,
            user_choice=user_choice,
            original_stored=self._settings.store_originals_in_audit,
        )

        return InspectionResult(decision=decision, findings=findings, mask_result=mask_result)
