# Review Gate 1 — HAEN MVP Verification & Hardening

**Mission:** Verify and harden the HAEN Hypercar Design Support AI MVP. No new
feature development. No merge. No PR. No SafeCopy base-branch changes.

## 1. Context

- **Branch checked:** `haen-standalone-extraction`
- **Baseline commit reviewed:** `192b400` ("Add GitHub Actions CI")
- **Patches from this gate:** committed on the same branch (see §10).
- **Repository state:** standalone HAEN layout at repo root; **no SafeCopy files
  present** (verified via `git ls-tree -r`); CI present at
  `.github/workflows/ci.yml`.

## 2. Local verification

| Command | Result |
|---------|--------|
| `python -m compileall -q haen tests` | ✅ `compileall OK` |
| `python -m pytest` | ✅ **89 passed** in ~0.6s (was 44; +45 Gate 1 tests) |
| `python -m haen.cli --version` | ✅ `haen 0.1.0` |
| `python -m haen.cli compare` | ✅ table + advisory ranking (GT-1 76.2, GT-1H-LH2 49.3, GT-1H 15.0) |
| `python -m haen.cli simulate` | ✅ now prints `[!] top-speed = MODEL ARTIFACT` for GT-1 BEV |
| `python -m haen.cli check <clean>` | ✅ exit 0, "no forbidden claims" |
| `python -m haen.cli check <dirty>` | ✅ exit 1, lists FC-001/FC-003 with locations |
| `python -m haen.cli dossier --branch GT-1` | ✅ generated, passes governance gate |

## 3. Guardrail findings (forbidden-claim checker)

**Finding G-1 (gap, fixed):** the baseline checker covered 6 of the 10 required
claims. **Missing: `certification ready`, `CFD validated`, `crash simulation
complete`, `digital twin complete`.** Empirically confirmed before patching.

**Patch:** added rules **FC-007** (certification ready), **FC-008** (CFD
validated), **FC-009** (crash simulation complete), **FC-010** (digital twin
complete) to `haen/data/forbidden_claims.yaml`.

**Finding G-2 (hardening):** no Korean-language coverage despite a Korean
deployment context. **Patch:** added Korean (한국어) patterns to all 10 rules,
anchored on affirmative verbs (확보/보장/입증/완료/가능/확정) so negated framings
(미평가/미완료) are not flagged.

**Finding G-3 (false positive, fixed):** the first FC-010 draft flagged the
*recommended safe* phrase "not a validated digital twin". **Patch:** guarded the
reverse-order pattern with stacked fixed-width negative lookbehinds
`(?<!not )(?<!not a )`. Affirmative "a validated digital twin" / "digital twin
validated" remain blocked; the negated safe form passes.

**Coverage now verified (all BLOCKED):** the 10 required claims; hyphenated forms
(`road-legal`, `crash-safe`, `CFD-validated`, `type-approved`, …); Korean forms
(`양산 가능`, `인증 완료`, `충돌 해석 완료`, `디지털 트윈 구축 완료`, `공급사 확정`,
`도로 주행 합법`, …). **Safe framings verified NOT blocked:** `road-legality not
assessed`, `crashworthiness not evaluated`, `certification status: not assessed`,
`CFD not performed`, `crash simulation not performed`, `not a validated digital
twin`, `인증 미완료`, `충돌 안전성 미평가`, `설계 미완료`. Tests:
`tests/test_gate1_hardening.py`.

## 4. Report / RFI safety findings

- Sample **dossier and RFI both pass the governance gate** (`check_text` returns
  no findings). The gate is enforced inside `build_dossier`/`save_dossier` and
  `RFI.to_markdown`.
- **Finding R-1 (hardening):** the dossier status block did not *explicitly*
  disclaim CFD / thermal / crash-simulation / digital-twin / certification, and
  did not state LH2 = watch-only or "no supplier secured". The text did not
  *imply* any of these, but explicit disclaimers are stronger.
  **Patch** (`templates/entry_validation_dossier.md.tmpl`) — status block now
  declares: Certification **not assessed**; Crash simulation **not performed**;
  Aerodynamics **CFD not performed**; Thermal **not modelled**; Supplier figures
  **(none secured)**; Model fidelity **not a validated digital twin**; GT-1H LH2
  **watch branch only — monitored, not adopted**.
- Confirmed generated text does **not** imply: hypercar completion, certification
  feasibility, road legality, production readiness, supplier secured, LH2
  adoption, or CFD/crash/thermal validation.

## 5. Vehicle branch separation findings

- **GT-1 BEV** = `baseline`, **GT-1H 700bar** = `halo`, **GT-1H-LH2** = `watch`.
  Confirmed in `haen/data/branches.yaml`. **LH2 remains a watch branch only**
  (powertrain, status and notes all reflect "watch / unresolved").
- **Label separation present:** *assumptions* carry confidence + status (open /
  substantiated / retired) + source in the assumption ledger; *targets* are an
  explicit `PerformanceTargets` schema; *verified* state lives in supplier
  evidence (`unverified / in_review / verified / disputed`). These three concepts
  are kept distinct in the data model.
- **Unresolved questions / supplier dependencies / certification questions** are
  represented: open low-confidence assumptions (e.g. `lh2.boiloff_rate`,
  `h2.tank_system_density`) and unverified evidence flow into the RFI builder;
  certification is disclaimed as "not assessed" in the dossier.
- **Finding S-1 (residual, not patched — would be new feature):** there is no
  dedicated structured *gate-status* field per branch. Gate status is currently
  represented implicitly via `branch_status` (baseline/halo/watch) plus the
  dossier §10 sign-off table. Adding an explicit per-branch gate/phase field is a
  candidate for a later pass (out of Gate 1 scope).

## 6. Low-fidelity simulation caveat findings

- Outputs that **exist** (top speed, 0-100, range, consumption) are labelled as
  low-fidelity screening estimates on every surface (`SimResult.notes`, CLI
  footer, dossier §4, dashboard banner).
- **Braking, load transfer and CG-sensitivity are NOT implemented** in this MVP,
  so there are no such outputs that could be mistaken for predictions. The
  dossier note now states this explicitly. (Implementing them would be new
  feature work — out of scope.)
- **Finding F-1 (hardening):** the BEV ~452 km/h top-speed value could be
  misread. **Patch** (`haen/low_fidelity_simulation.py`): added
  `TOP_SPEED_PLAUSIBILITY_KPH = 400`, `SimResult.warnings` and
  `SimResult.top_speed_is_artifact`. When exceeded, a loud warning is emitted and
  the value is flagged `[!]` in the CLI, the dossier table, and the dashboard,
  with the text "MODEL ARTIFACT … NOT a real-world prediction".

## 7. Issues found (summary)

| ID | Severity | Area | Status |
|----|----------|------|--------|
| G-1 | High | Missing 4 required forbidden claims | Fixed |
| G-2 | Medium | No Korean coverage | Fixed (added) |
| G-3 | Medium | False positive on safe "not a validated digital twin" | Fixed |
| R-1 | Low/Medium | Dossier lacked explicit CFD/thermal/crash-sim/digital-twin/LH2 disclaimers | Fixed |
| F-1 | Medium | BEV top-speed artifact could be misread | Fixed |
| S-1 | Low | No structured per-branch gate-status field | Open (out of scope) |

## 8. Patches made

- `haen/data/forbidden_claims.yaml` — added FC-007…FC-010; added Korean patterns
  to all rules; guarded the digital-twin reverse pattern.
- `templates/entry_validation_dossier.md.tmpl` — explicit "not performed / not
  modelled / not assessed" status lines; LH2 watch-only; no supplier secured;
  not a validated digital twin.
- `haen/low_fidelity_simulation.py` — plausibility bound, `warnings`,
  `top_speed_is_artifact`.
- `haen/report_builder.py` — dossier sim section flags `[!]` artifacts and lists
  the warnings; expanded fidelity caveat (braking/load-transfer/CG not modelled).
- `haen/cli.py` — `simulate` shows artifact flag and warnings.
- `haen/webapp/app.py` — dashboard simulation page surfaces warnings.
- `tests/test_gate1_hardening.py` — 45 new tests (claims, hyphen/Korean variants,
  false-positive guards, sim warnings, dossier wording).

## 9. Remaining risks

- **S-1:** no explicit per-branch gate-status field (tracked for a later pass).
- **Korean coverage is targeted, not exhaustive.** It anchors on the most common
  affirmative claim verbs; novel phrasings may evade it. English remains primary.
- The checker is **lexical** (regex). It cannot catch semantically-implied claims
  that avoid the listed wording. It is a safety net, not a substitute for human
  review.
- The plausibility bound (400 km/h) is a heuristic for *labelling only*; it does
  not change the underlying screening model.

## 10. Merge recommendation

**Recommendation: YES — eligible to merge _when a review owner approves_, but DO
NOT auto-merge.**

Rationale: all Gate 1 required guardrails are implemented and verified; the full
suite (89 tests) and byte-compile pass; generated dossier/RFI are governance-
clean and carry explicit safety disclaimers; branch separation and the LH2
watch-only designation are confirmed; the BEV top-speed artifact is unambiguously
flagged. The only open item (S-1, structured gate-status field) is a non-blocking
enhancement outside Gate 1 scope. Per mission constraints, this review performs
**no merge and opens no PR**; the human review owner decides promotion.
