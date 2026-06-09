"""03_packaging — parametric packaging and overlap detection.

Represents major components as axis-aligned bounding boxes (AABBs) in a simple
vehicle coordinate frame:

    x: longitudinal, +x toward the front (mm)
    y: lateral,      +y toward the left   (mm)
    z: vertical,     +z up                (mm)

Provides interference (overlap) detection between components and a basic
envelope check against the vehicle's external dimensions. This is a low-fidelity
packaging aid for early exploration, not a CAD clash-detection system.
"""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, Field

from .vehicle_definition import VehicleDefinition


class Box(BaseModel):
    """An axis-aligned bounding box centred at (cx, cy, cz) with sizes (mm)."""

    cx: float
    cy: float
    cz: float
    size_x: float = Field(..., gt=0)
    size_y: float = Field(..., gt=0)
    size_z: float = Field(..., gt=0)

    @property
    def min_x(self) -> float: return self.cx - self.size_x / 2
    @property
    def max_x(self) -> float: return self.cx + self.size_x / 2
    @property
    def min_y(self) -> float: return self.cy - self.size_y / 2
    @property
    def max_y(self) -> float: return self.cy + self.size_y / 2
    @property
    def min_z(self) -> float: return self.cz - self.size_z / 2
    @property
    def max_z(self) -> float: return self.cz + self.size_z / 2

    @property
    def volume_m3(self) -> float:
        return (self.size_x * self.size_y * self.size_z) / 1e9


class Component(BaseModel):
    """A named packaging component occupying a bounding box."""

    name: str
    group: str = "other"
    box: Box
    # When True, any overlap with another component is a hard clash; some
    # components (e.g. crash structure zones) may be allowed to be tolerant.
    rigid: bool = True


@dataclass(frozen=True)
class Overlap:
    """A detected interference between two components."""

    a: str
    b: str
    overlap_x_mm: float
    overlap_y_mm: float
    overlap_z_mm: float

    @property
    def overlap_volume_m3(self) -> float:
        return (self.overlap_x_mm * self.overlap_y_mm * self.overlap_z_mm) / 1e9


def _axis_overlap(a_min: float, a_max: float, b_min: float, b_max: float) -> float:
    """Return the 1-D overlap length (>= 0) of two intervals."""
    return max(0.0, min(a_max, b_max) - max(a_min, b_min))


def boxes_overlap(a: Box, b: Box, *, tol_mm: float = 0.0) -> Overlap | None:
    """Return an :class:`Overlap` if boxes ``a`` and ``b`` interfere.

    ``tol_mm`` shrinks each box symmetrically so that touching faces or
    sub-tolerance penetrations are not reported as clashes.
    """
    ox = _axis_overlap(a.min_x, a.max_x, b.min_x, b.max_x) - tol_mm
    oy = _axis_overlap(a.min_y, a.max_y, b.min_y, b.max_y) - tol_mm
    oz = _axis_overlap(a.min_z, a.max_z, b.min_z, b.max_z) - tol_mm
    if ox > 0 and oy > 0 and oz > 0:
        return Overlap("", "", ox, oy, oz)
    return None


def detect_overlaps(
    components: list[Component], *, tol_mm: float = 1.0, rigid_only: bool = True
) -> list[Overlap]:
    """Detect pairwise interferences among ``components``.

    When ``rigid_only`` is True, only pairs where *both* components are rigid are
    reported (a tolerant zone is allowed to share space).
    """
    overlaps: list[Overlap] = []
    n = len(components)
    for i in range(n):
        for j in range(i + 1, n):
            ci, cj = components[i], components[j]
            if rigid_only and not (ci.rigid and cj.rigid):
                continue
            ov = boxes_overlap(ci.box, cj.box, tol_mm=tol_mm)
            if ov is not None:
                overlaps.append(
                    Overlap(ci.name, cj.name, ov.overlap_x_mm, ov.overlap_y_mm, ov.overlap_z_mm)
                )
    return overlaps


@dataclass(frozen=True)
class EnvelopeViolation:
    component: str
    axis: str
    amount_mm: float


def check_envelope(
    components: list[Component], vehicle: VehicleDefinition, *, margin_mm: float = 0.0
) -> list[EnvelopeViolation]:
    """Check that components fit within the vehicle's external envelope.

    The envelope origin is the vehicle centre on y/z and the wheelbase mid-point
    on x. Components protruding beyond length/width/height (less ``margin_mm``)
    are reported. This is an approximate sanity check only.
    """
    half_len = vehicle.dimensions.length_mm / 2 - margin_mm
    half_wid = vehicle.dimensions.width_mm / 2 - margin_mm
    height = vehicle.dimensions.height_mm - margin_mm

    violations: list[EnvelopeViolation] = []
    for c in components:
        if c.box.max_x > half_len:
            violations.append(EnvelopeViolation(c.name, "x+", c.box.max_x - half_len))
        if c.box.min_x < -half_len:
            violations.append(EnvelopeViolation(c.name, "x-", -half_len - c.box.min_x))
        if c.box.max_y > half_wid:
            violations.append(EnvelopeViolation(c.name, "y+", c.box.max_y - half_wid))
        if c.box.min_y < -half_wid:
            violations.append(EnvelopeViolation(c.name, "y-", -half_wid - c.box.min_y))
        if c.box.max_z > height:
            violations.append(EnvelopeViolation(c.name, "z+", c.box.max_z - height))
        if c.box.min_z < 0:
            violations.append(EnvelopeViolation(c.name, "z-", -c.box.min_z))
    return violations


def packed_volume_m3(components: list[Component]) -> float:
    """Total bounding-box volume of all components (m^3)."""
    return sum(c.box.volume_m3 for c in components)
