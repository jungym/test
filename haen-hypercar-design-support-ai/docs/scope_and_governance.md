# Scope and Governance

## Purpose

The HAEN Hypercar Design Support AI is a **human-reviewed, AI-assisted design
support system**. It exists to help engineers explore and compare early-stage
hypercar architecture concepts faster, with traceable assumptions and evidence.

It is **not** an autonomous design system. It does not make engineering decisions,
and it does not produce certified or final outputs.

## In scope (MVP)

- Vehicle definition and schema validation
- Architecture branch comparison
- Parametric packaging and overlap detection
- Low-fidelity simulation (mass, energy, first-order performance/range)
- Mass and energy comparison
- Supplier evidence management
- RFI generation
- Forbidden-claim checking
- Entry validation dossier building

## Explicitly out of scope / forbidden claims

The system must never assert any of the following. The forbidden-claim checker
([`haen/governance.py`](../haen/governance.py),
[`haen/data/forbidden_claims.yaml`](../haen/data/forbidden_claims.yaml)) detects
them, and the report/RFI builders refuse to emit text that contains them.

| Forbidden claim | Correct framing |
|-----------------|-----------------|
| road legal / street legal | road-legality **not assessed** |
| homologation ready | homologation status **not assessed** |
| crash safe | crashworthiness **not evaluated** |
| production feasible | manufacturability **not assessed** |
| supplier confirmed | supplier-quoted (**unverified**) until human-verified |
| design complete | design **exploration in progress** |

## Human-in-the-loop principles

1. **Assumptions are explicit.** Every figure used to produce an output is logged
   in the assumption ledger with a source and confidence.
2. **Uncertainty is surfaced, not hidden.** Gaps become RFI items rather than
   being asserted as facts.
3. **Evidence, not confirmation.** Supplier inputs are tracked with a verification
   state that only a human can advance.
4. **Low fidelity is labelled.** Simulation outputs carry an explicit caveat and
   are never presented as predictions or certifications.
5. **Trade-off scores are advisory.** Branch selection is a human decision.

## Fidelity statement

The simulation module is a first-order point-mass model. It ignores gearing,
traction and thermal limits, transient dynamics, real-world drive cycles, regen
and many other effects. Use results for *relative comparison only*.
