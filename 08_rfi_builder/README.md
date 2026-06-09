# 08_rfi_builder

**Implemented in:** [`haen/rfi_builder.py`](../haen/rfi_builder.py)

Request For Information (RFI) generation.

- `build_rfi(...)` — turns information gaps into a structured RFI:
  - open low-confidence assumptions (from the ledger) → high priority,
  - unverified supplier evidence → medium priority,
  - expected components with no evidence → high priority.
- `RFI.to_markdown()` — renders the RFI as Markdown, gated by the forbidden-claim
  checker before emission.

The RFI is how the system *resolves* uncertainty instead of asserting unknowns.
