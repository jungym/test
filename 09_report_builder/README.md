# 09_report_builder

**Implemented in:** [`haen/report_builder.py`](../haen/report_builder.py)

Entry validation dossier builder.

- `build_dossier(...)` — assembles vehicle definition, mass/energy, simulation,
  trade-off, supplier evidence, assumptions and RFI summary into one Markdown
  dossier using [`templates/entry_validation_dossier.md.tmpl`](../templates/entry_validation_dossier.md.tmpl).
- `save_dossier(text, path)` — writes after a final governance check.

Every dossier is passed through the forbidden-claim checker; the system cannot
emit a dossier containing a forbidden claim. The template states explicit
"not assessed" / "not evaluated" statuses.
