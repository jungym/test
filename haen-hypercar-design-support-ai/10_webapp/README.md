# 10_webapp

**Implemented in:** [`haen/webapp/app.py`](../haen/webapp/app.py)

Streamlit dashboard — the human-in-the-loop review surface.

Run:

```bash
streamlit run haen/webapp/app.py
```

Pages: Overview, Mass & energy, Low-fidelity simulation, Branch trade-off,
Packaging, Supplier evidence, RFI builder, Forbidden claim checker.

The dashboard surfaces outputs for a person to assess. It does not make decisions
and does not certify anything; the disclaimer is shown on every page.
