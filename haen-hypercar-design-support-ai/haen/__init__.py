"""HAEN Hypercar Design Support AI (MVP).

A human-reviewed, AI-assisted design *support* system. This package does NOT
make autonomous design decisions and does NOT certify any vehicle. Every output
is an engineering aid that requires human review.

Hard scope rules (enforced by ``haen.governance``): the system must never claim a
design is road legal, homologation ready, crash safe, production feasible,
supplier confirmed, or design complete.

Module map (numbered directories at the repository root document each module):

    00_governance              -> haen.governance
    01_vehicle_definition      -> haen.vehicle_definition
    02_design_space_explorer   -> haen.design_space_explorer
    03_packaging               -> haen.packaging
    04_mass_energy             -> haen.mass_energy
    05_low_fidelity_simulation -> haen.low_fidelity_simulation
    06_visualization           -> haen.visualization
    07_supplier_evidence       -> haen.supplier_evidence
    08_rfi_builder             -> haen.rfi_builder
    09_report_builder          -> haen.report_builder
    10_webapp                  -> haen.webapp
"""

from __future__ import annotations

__version__ = "0.1.0"

DISCLAIMER = (
    "HAEN Hypercar Design Support AI is a human-reviewed, AI-assisted design "
    "support tool. Outputs are engineering aids only. This system makes no "
    "assertion of road-legality, homologation readiness, crashworthiness, "
    "production feasibility, supplier confirmation, or design completeness for "
    "any concept; all such judgements require human review and formal process."
)

__all__ = ["__version__", "DISCLAIMER"]
