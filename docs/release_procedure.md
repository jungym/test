# Internal Release Procedure

How to build, validate, and record an **internal** review release of HAEN
Hypercar Design Support AI. This procedure produces internal-only artifacts; it
does **not** authorize any external release, and confers no certification,
production, or real-world validation status.

## 1. Preconditions

- Working tree clean on the development branch.
- Local validation green:
  ```bash
  ruff check .
  python -m compileall -q haen tests
  python -m pytest -q
  ```
- CI green for the release commit (Python 3.11 + 3.12).

## 2. Update version + changelog

- Bump `version` in `pyproject.toml` if changed.
- Add a dated entry to `CHANGELOG.md` summarizing the release.

## 3. Build the internal review package (reproducible)

```bash
haen release-candidate \
  --project examples/project/haen-project.yaml \
  --out dist/internal_review \
  --generated-at <fixed-ISO-timestamp>
```

Use a fixed `--generated-at` so the package and archive are byte-stable
(reproducible). Substitute your own `--project` manifest for a real concept.

## 4. Validate

```bash
haen validate dist/internal_review            # directory
haen validate dist/internal_review.zip        # archive + .sha256 sidecar
```

Both must report `OK ... valid and internal-only`. The package manifest must
record `internal_only: true`, `human_review_required: true`,
`external_release_allowed: false`.

## 5. Human review

A human reviewer reads the dossier, readiness checklist, and RFI; checks the
advisory semantic-risk section; and confirms no forbidden claims. Record the
sign-off in the dossier's review block. `external_release_allowed` stays `false`
unless a separate, explicit, governed decision is made.

## 6. Tagging (only on explicit instruction)

Tagging a release is a deliberate, separate step:

```bash
git tag -a v<version> -m "HHDS-AI v<version> internal release candidate"
git push origin v<version>
```

Do **not** tag or push tags without an explicit instruction.

## 7. Integrity notes

- Per-file SHA-256 checksums live in `manifest.json`; a `bundle_sha256` hashes
  the artifact map (non-circular — it never hashes an archive that contains the
  manifest).
- The archive hash lives in a sidecar `*.zip.sha256` outside the archive.
- External cryptographic signing is **parked** (requires approved key
  management); current integrity is hash-based and deterministic.
