"""06_visualization — Plotly/Matplotlib chart helpers.

Pure helper functions that return figure objects; they do not render or save by
themselves so they can be embedded in the Streamlit app, notebooks or report
generation. Plotly is the default (interactive dashboard); a Matplotlib helper
is provided for static report images.
"""

from __future__ import annotations

import pandas as pd

from .packaging import Component


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


def packaging_topview(components: list[Component]):
    """Plotly 2-D top view (x-y plane) of component bounding boxes."""
    import plotly.graph_objects as go

    fig = go.Figure()
    for c in components:
        b = c.box
        fig.add_shape(
            type="rect",
            x0=b.min_x, x1=b.max_x, y0=b.min_y, y1=b.max_y,
            line={"width": 1},
            opacity=0.4,
        )
        fig.add_trace(
            go.Scatter(
                x=[b.cx], y=[b.cy], mode="markers+text",
                text=[c.name], textposition="top center", name=c.name,
            )
        )
    fig.update_layout(
        title="Packaging — top view (x longitudinal, y lateral)",
        xaxis_title="x (mm)", yaxis_title="y (mm)",
        yaxis={"scaleanchor": "x", "scaleratio": 1},
    )
    return fig


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
