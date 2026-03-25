"""Graph Generator Module.

Builds a NetworkX directed graph of skills and produces a Plotly figure
suitable for rendering inside Streamlit.
"""
from __future__ import annotations

from typing import Any

import networkx as nx
import plotly.graph_objects as go


# Colour scheme
_COLOUR = {
    "known": "#2ecc71",       # green
    "missing_required": "#e74c3c",  # red
    "missing_optional": "#f39c12",  # orange
    "adjacent": "#3498db",    # blue
    "neutral": "#95a5a6",     # grey
}


def build_graph(
    analysis: dict[str, Any],
    kb: dict[str, Any],
    include_all: bool = False,
) -> nx.DiGraph:
    """Return a directed dependency graph for the current analysis context.

    Nodes represent skills; edges go from prerequisite → skill.
    Node attributes:
      - ``status``: one of ``known | missing_required | missing_optional |
        adjacent | neutral``
      - ``category``: skill category from the knowledge base
    """
    dependencies: dict[str, list[str]] = kb.get("dependencies", {})
    skills_meta: dict[str, Any] = kb.get("skills", {})

    known_set = set(analysis["known"])
    missing_req_set = set(analysis["missing_required"])
    missing_opt_set = set(analysis["missing_optional"])
    adjacent_set = set(analysis["adjacent"])

    # Decide which skills to include in the graph
    if include_all:
        node_names = list(skills_meta.keys())
    else:
        node_names = list(
            known_set
            | missing_req_set
            | missing_opt_set
            | adjacent_set
        )

    G = nx.DiGraph()

    for skill in node_names:
        if skill in known_set:
            status = "known"
        elif skill in missing_req_set:
            status = "missing_required"
        elif skill in missing_opt_set:
            status = "missing_optional"
        elif skill in adjacent_set:
            status = "adjacent"
        else:
            status = "neutral"
        category = skills_meta.get(skill, {}).get("category", "Other")
        G.add_node(skill, status=status, category=category)

    for skill in node_names:
        for prereq in dependencies.get(skill, []):
            if G.has_node(prereq):
                G.add_edge(prereq, skill)

    return G


def _spring_layout(G: nx.DiGraph) -> dict[str, tuple[float, float]]:
    """Return 2-D positions for graph nodes using a spring layout."""
    if len(G) == 0:
        return {}
    seed = 42
    pos = nx.spring_layout(G, seed=seed, k=2.5)
    return pos


def create_plotly_figure(
    G: nx.DiGraph,
    title: str = "Skill Graph",
) -> go.Figure:
    """Convert a NetworkX graph to an interactive Plotly figure."""
    if len(G) == 0:
        fig = go.Figure()
        fig.update_layout(title=title)
        return fig

    pos = _spring_layout(G)

    # Build edge traces
    edge_x: list[float | None] = []
    edge_y: list[float | None] = []
    for u, v in G.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        line={"width": 1, "color": "#888"},
        hoverinfo="none",
        mode="lines",
    )

    # Build node trace per status for the legend
    status_groups: dict[str, list[str]] = {}
    for node, data in G.nodes(data=True):
        status = data.get("status", "neutral")
        status_groups.setdefault(status, []).append(node)

    status_labels = {
        "known": "Known",
        "missing_required": "Missing (Required)",
        "missing_optional": "Missing (Optional)",
        "adjacent": "Unlockable Next",
        "neutral": "Other",
    }

    node_traces: list[go.Scatter] = []
    for status, nodes in status_groups.items():
        x_vals = [pos[n][0] for n in nodes]
        y_vals = [pos[n][1] for n in nodes]
        hover = [
            f"<b>{n}</b><br>Category: {G.nodes[n].get('category','')}"
            for n in nodes
        ]
        node_traces.append(
            go.Scatter(
                x=x_vals,
                y=y_vals,
                mode="markers+text",
                hoverinfo="text",
                text=nodes,
                hovertext=hover,
                textposition="top center",
                name=status_labels.get(status, status),
                marker={
                    "size": 18,
                    "color": _COLOUR.get(status, "#95a5a6"),
                    "line": {"width": 2, "color": "#fff"},
                },
            )
        )

    fig = go.Figure(
        data=[edge_trace, *node_traces],
        layout=go.Layout(
            title={"text": title, "font": {"size": 18}},
            showlegend=True,
            hovermode="closest",
            xaxis={"showgrid": False, "zeroline": False, "showticklabels": False},
            yaxis={"showgrid": False, "zeroline": False, "showticklabels": False},
            paper_bgcolor="#0e1117",
            plot_bgcolor="#0e1117",
            font={"color": "#fafafa"},
            margin={"l": 20, "r": 20, "t": 60, "b": 20},
            height=550,
        ),
    )
    return fig
