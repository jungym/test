"""06_visualization — Plotly/Matplotlib chart helpers.

Pure helper functions that return figure objects; they do not render or save by
themselves so they can be embedded in the Streamlit app, notebooks or report
generation. Plotly is the default (interactive dashboard); a Matplotlib helper
is provided for static report images.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .packaging import Component

INTERNAL_PACKAGING_CAPTION = (
    "Internal-only low-fidelity packaging diagram (axis-aligned bounding boxes). "
    "Not CAD, not geometric or packaging validation."
)


def mass_energy_bar(df: pd.DataFrame, *, metric: str = "curb_mass_kg"):
    """Plotly bar chart of a single metric across branches/vehicles."""
    import plotly.express as px

    if metric not in df.columns:
        raise KeyError(f"metric '{metric}' not in dataframe columns")
    plot_df = df.reset_index()
    label = df.index.name or "id"
    fig = px.bar(
        plot_df,
        x=label,
        y=metric,
        color="branch" if "branch" in plot_df.columns else None,
        title=f"{metric} by {label}",
    )
    fig.update_layout(showlegend=True)
    return fig


def tradeoff_radar(table: pd.DataFrame, criteria_keys: list[str]):
    """Plotly radar chart comparing vehicles across normalised criteria."""
    import plotly.graph_objects as go

    available = [k for k in criteria_keys if k in table.columns]
    if not available:
        raise KeyError("none of the requested criteria keys are present")

    # Min-max normalise each criterion to [0, 1] for comparable radial axes.
    norm = table[available].copy()
    for col in available:
        lo, hi = norm[col].min(), norm[col].max()
        norm[col] = 0.5 if hi == lo else (norm[col] - lo) / (hi - lo)

    fig = go.Figure()
    for idx, row in norm.iterrows():
        fig.add_trace(
            go.Scatterpolar(
                r=row.tolist() + [row.tolist()[0]],
                theta=available + [available[0]],
                fill="toself",
                name=str(idx),
            )
        )
    fig.update_layout(
        polar={"radialaxis": {"visible": True, "range": [0, 1]}},
        title="Normalised criteria comparison (advisory)",
    )
    return fig


# --------------------------------------------------------------------------- #
# Packaging diagrams (Review Gate 3, Item 4)
# --------------------------------------------------------------------------- #
# The diagram *model* below is pure Python (no plotting dependency) so it can be
# computed and tested deterministically. Plotly renderers consume it.
@dataclass(frozen=True)
class Rect:
    """A 2-D rectangle in a chosen packaging view (mm)."""

    name: str
    x0: float
    y0: float
    x1: float
    y1: float
    kind: str = "component"  # component | envelope | conflict


@dataclass(frozen=True)
class PackagingDiagram:
    """A deterministic, lib-free packaging diagram model for one view.

    ``view`` is "top" (x–y) or "side" (x–z). ``rects`` holds component (and
    optional envelope) rectangles; ``conflicts`` holds the intersection
    rectangles of overlapping components. Internal-only, low-fidelity.
    """

    view: str
    rects: tuple[Rect, ...]
    conflicts: tuple[Rect, ...]
    internal_only: bool = True
    caption: str = INTERNAL_PACKAGING_CAPTION


def _axis_bounds(box, view: str) -> tuple[float, float, float, float]:
    if view == "top":
        return box.min_x, box.min_y, box.max_x, box.max_y
    if view == "side":
        return box.min_x, box.min_z, box.max_x, box.max_z
    raise ValueError("view must be 'top' or 'side'")


def packaging_diagram(
    components: list[Component],
    vehicle=None,
    *,
    view: str = "top",
) -> PackagingDiagram:
    """Build a deterministic packaging diagram model for ``view``.

    Components are drawn as rectangles; if ``vehicle`` is given, its external
    envelope is added. Overlapping component pairs contribute conflict rectangles
    (their intersection). Handles an empty component list gracefully.
    """
    if view not in ("top", "side"):
        raise ValueError("view must be 'top' or 'side'")

    rects = [
        Rect(c.name, *_axis_bounds(c.box, view), kind="component") for c in components
    ]

    if vehicle is not None:
        half_len = vehicle.dimensions.length_mm / 2
        if view == "top":
            half_wid = vehicle.dimensions.width_mm / 2
            rects.append(Rect("envelope", -half_len, -half_wid, half_len, half_wid, kind="envelope"))
        else:
            height = vehicle.dimensions.height_mm
            rects.append(Rect("envelope", -half_len, 0.0, half_len, height, kind="envelope"))

    conflicts: list[Rect] = []
    n = len(components)
    for i in range(n):
        for j in range(i + 1, n):
            a, b = components[i].box, components[j].box
            ix0, ix1 = max(a.min_x, b.min_x), min(a.max_x, b.max_x)
            iy0, iy1 = max(a.min_y, b.min_y), min(a.max_y, b.max_y)
            iz0, iz1 = max(a.min_z, b.min_z), min(a.max_z, b.max_z)
            if ix1 > ix0 and iy1 > iy0 and iz1 > iz0:  # true 3-D overlap
                name = f"{components[i].name} x {components[j].name}"
                if view == "top":
                    conflicts.append(Rect(name, ix0, iy0, ix1, iy1, kind="conflict"))
                else:
                    conflicts.append(Rect(name, ix0, iz0, ix1, iz1, kind="conflict"))

    return PackagingDiagram(view=view, rects=tuple(rects), conflicts=tuple(conflicts))


def _render_diagram(diagram: PackagingDiagram):
    """Render a :class:`PackagingDiagram` as a Plotly figure (lazy import)."""
    import plotly.graph_objects as go

    vlabel = "y (mm)" if diagram.view == "top" else "z (mm)"
    fig = go.Figure()
    for r in diagram.rects:
        line_w = 2 if r.kind == "envelope" else 1
        dash = "dot" if r.kind == "envelope" else "solid"
        fig.add_shape(
            type="rect", x0=r.x0, y0=r.y0, x1=r.x1, y1=r.y1,
            line={"width": line_w, "dash": dash}, opacity=0.35,
        )
        fig.add_trace(
            go.Scatter(
                x=[(r.x0 + r.x1) / 2], y=[(r.y0 + r.y1) / 2],
                mode="markers+text", text=[r.name], textposition="top center", name=r.name,
            )
        )
    for c in diagram.conflicts:
        fig.add_shape(
            type="rect", x0=c.x0, y0=c.y0, x1=c.x1, y1=c.y1,
            line={"width": 2, "color": "red"}, fillcolor="red", opacity=0.3,
        )
    fig.update_layout(
        title=f"Packaging — {diagram.view} view (INTERNAL — low-fidelity AABB)",
        xaxis_title="x (mm)", yaxis_title=vlabel,
        yaxis={"scaleanchor": "x", "scaleratio": 1},
    )
    return fig


def packaging_topview(components: list[Component], vehicle=None):
    """Plotly 2-D top view (x–y) of component bounding boxes + conflicts."""
    return _render_diagram(packaging_diagram(components, vehicle, view="top"))


def packaging_sideview(components: list[Component], vehicle=None):
    """Plotly 2-D side view (x–z) of component bounding boxes + conflicts."""
    return _render_diagram(packaging_diagram(components, vehicle, view="side"))


def mass_breakdown_pie_mpl(breakdown: pd.DataFrame):
    """Matplotlib pie of mass groups for static report embedding.

    Expects a dataframe with 'group' and 'mass_kg' columns.
    """
    import matplotlib

    matplotlib.use("Agg")  # headless backend for report generation
    import matplotlib.pyplot as plt

    grouped = breakdown.groupby("group")["mass_kg"].sum()
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.pie(grouped.values, labels=grouped.index, autopct="%1.0f%%")
    ax.set_title("Mass breakdown by group")
    return fig
