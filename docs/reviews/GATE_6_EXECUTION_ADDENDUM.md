# Gate 6 Execution Addendum

This addendum clarifies execution rules for Review Gate 6.

If this addendum conflicts with earlier Gate 6 wording, this addendum takes
precedence only on the clarification points it covers.

## 1. Supersession of stale "First Task Now" wording

Any historical "First Task Now" text in the master specification is superseded by
the active Gate 6 command and this addendum.

Current authoritative state:

- Gate 5 CI for commit `19e48ff` has already been confirmed green.
- Gate 5 closure and Gate 6 scope proposal have already been committed as `9536386`.
- Gate 6 scope exists and is accepted for execution.
- Do not recreate Gate 5 closure.
- Do not redraft Gate 6 scope unless a correction is explicitly required.
- Proceed with Gate 6 only after normal baseline verification.

## 2. Manifest and bundle hash rule

Avoid circular hashing.

The release bundle must not contain a manifest field that hashes the bundle
containing that same manifest field.

Use this rule:

1. `manifest.json` records checksums for individual package artifacts.
2. The archive/bundle may include `manifest.json`.
3. The archive/bundle hash must be written outside the archive as a sidecar file,
   for example:

   ```
   release_bundle.zip
   release_bundle.zip.sha256
   ```

4. If `bundle_sha256` is stored in structured metadata, it must live in a sidecar
   metadata file outside the archive, not inside the manifest that is included in
   the archive.

Do not silently choose a circular-hash workaround.

> Note on existing code: the current `manifest.json` already carries a
> `bundle_sha256` that hashes the **file→checksum map** (the package artifacts),
> NOT an archive that contains the manifest — so it is non-circular today. When
> Gate 6 adds an *archive* (zip) hash, that archive hash must be a sidecar
> (`*.zip.sha256`) and must not be stored inside the manifest that the archive
> contains.

## 3. Deterministic archive rule

Python `zipfile` archives are not deterministic by default because file
timestamps and entry ordering can vary.

When reproducibility mode is enabled:

1. Sort archive entries lexicographically by normalized relative path.
2. Normalize each `ZipInfo.date_time` to the fixed `generated_at` value when
   practical.
3. Use a stable compression mode and stable file permissions where practical.
4. If deterministic zip creation cannot be guaranteed, explicitly mark the
   archive as non-deterministic and exclude the archive itself from the
   deterministic core hash set.
5. SVG and text artifacts should remain the deterministic baseline whenever
   possible.
6. Optional PNG/raster artifacts must be treated as non-deterministic unless
   proven stable by tests.

Required manifest distinction:

- `deterministic_core_artifacts`
- `optional_non_deterministic_artifacts`
- `archive_determinism_status`
- `archive_hash_sidecar`

Do not claim full archive reproducibility unless tests demonstrate it.

## 4. Claim-checker scan scope and safe-section limits

The claim checker must not fail because it sees its own pattern definitions or
finding records.

Hard forbidden-claim scanning applies to generated prose artifacts such as:

- dossier markdown
- readiness markdown
- RFI markdown
- generated internal reports
- generated documentation intended for operator review
- exported release notes
- dashboard-visible prose if exported as text

Hard forbidden-claim scanning does not apply to raw machine-readable pattern or
finding files such as:

- `haen/data/forbidden_claims.yaml`
- `forbidden_claim_scan.json`
- `semantic_risk_findings.json`
- manifest files that merely reference scan results
- test fixtures that intentionally contain forbidden phrases

Safe-section handling is restricted.

Safe sections are valid only in repository documentation under `docs/`.

Safe sections must never be allowed in generated artifacts, including:

- dossier
- readiness output
- RFI output
- validation report
- release package notes
- exported operator-facing artifacts

Generated artifacts must not contain safe-section markers such as:

- "Prohibited claim categories"
- "Forbidden wording examples"
- "Do not claim"
- "Unsafe wording categories"
- "Claim-risk examples for scanner tests"

Gate 6 implementation must add or update governance tests asserting that
generated outputs contain no safe-section markers.

The scanner must still scan normal generated prose and must never allow actual
output claims such as certification, road legality, supplier confirmation,
production readiness, design completion, or real-world validation.

## 5. Package layout precedence

Any package layout shown in this addendum is illustrative only.

The existing repository export layout wins.

Do not change the existing artifact/package layout merely to match an example in
the master specification or this addendum.

If existing Gate 4 or Gate 5 export code places packaging artifacts in a specific
folder, preserve that layout unless Gate 6 explicitly requires a compatible
extension.

Gate 6 may add metadata, validation, sidecar hashes, or reproducibility fields,
but it must not introduce avoidable path churn that breaks existing tests or user
workflows.

## 6. Docs-only CI pending policy

For docs-only commits:

Proceeding with the next Gate is allowed while docs-only CI is pending only if all
of the following are true:

1. The latest commit changed documentation files only.
2. No source, test, dashboard, export, CLI, configuration, dependency, or CI
   files changed.
3. The working tree is clean.
4. The prior implementation Gate has already passed local validation and CI.
5. The final report records that docs-only CI was pending at start.

For code-changing commits:

Do not close the Gate as fully complete until code CI is green.

For implementation Gates:

- local validation green is required before push
- CI must be checked once after push
- if CI is pending, report pending and do not continuously poll
- if CI fails, stop and report the smallest safe fix
- do not mark local + CI verified until CI is actually green

## 7. Reproducibility path reuse rule

Gate 6 Item 4 and Gate 6 Item 5 must share one implementation path.

Item 4 creates the canonical reproducibility mechanism.

Item 5 must reuse that mechanism.

Do not implement a separate timestamp injection path inside the
"release-candidate" command.

Required behavior:

- `--generated-at` in "release-candidate" must call the same internal
  reproducibility option created in Item 4.
- fixed `generated_at` must propagate consistently to:
  - dossier
  - readiness report
  - RFI output if generated
  - manifest
  - validation report
  - archive metadata where practical
  - reproducibility metadata
- stable artifact ordering must be shared between export and release-candidate
  flows.
- tests must confirm that direct export mode and release-candidate mode use the
  same generated_at and ordering behavior.

## 8. Active Gate 6 execution authority

After this addendum is committed, Gate 6 may proceed sequentially using:

1. `docs/reviews/REVIEW_GATE_6_SCOPE.md`
2. this addendum
3. the active Gate 6 command

Do not go beyond Gate 6.

Do not implement Gate 7.

Do not open a PR.

Do not touch SafeCopy base.

Do not amend or force-push.

Do not make external-release, certification, production, supplier-confirmation,
road-legality, design-completion, or real-world validation claims.

## Amendment A — clarification patch (applied at execution start)

The user-supplied clarification patch confirmed this addendum and added:

1. **Safe-section mechanism requirement:** if the repository lacks a
   safe-section mechanism, implement one before expanding Korean governance
   docs. → Implemented in Gate 6 Item 6 (`haen.governance`:
   `claim-safe-section` markers, `check_doc_text`, marker-free enforcement on
   generated artifacts).
2. **Release-candidate target UX:**
   `python -m haen.cli release-candidate --out dist/internal_review
   --generated-at <ISO>` must reuse the same reproducibility code path as the
   lower-level export functions. → Implemented in Gate 6 Items 3/4.
3. Any package layout shown in the patch remains illustrative; the existing
   repository export layout was preserved (§5 of this addendum still governs).
