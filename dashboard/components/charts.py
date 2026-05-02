from typing import List
import pandas as pd
import plotly.graph_objects as go

PARTY_COLORS = {
    "DMK+":  "#E41E20",   # DMK red
    "ADMK+": "#FF671F",   # Saffron (BJP-led alliance)
    "TVK":   "#7C3AED",   # Purple — new party
    "NTK":   "#1F2937",   # Dark charcoal
}

def sentiment_timeline(df: pd.DataFrame, parties: List[str]) -> go.Figure:
    """
    df columns: date, party, sentiment_index
    """
    fig = go.Figure()
    for party in parties:
        pdata = df[df["party"] == party].sort_values("date")
        if pdata.empty:
            continue
        fig.add_trace(go.Scatter(
            x=pdata["date"],
            y=pdata["sentiment_index"],
            name=party,
            mode="lines+markers",
            line={"color": PARTY_COLORS.get(party, "#999"), "width": 2},
        ))
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.4)
    fig.update_layout(
        title="Party Sentiment Index Over Time",
        xaxis_title="Date",
        yaxis_title="Sentiment (-1 to +1)",
        yaxis={"range": [-1, 1]},
        hovermode="x unified",
        legend_title="Party",
    )
    return fig

def source_stacked_bar(df: pd.DataFrame) -> go.Figure:
    """
    df columns: date, source, post_count
    """
    fig = go.Figure()
    for source in df["source"].unique():
        sdata = df[df["source"] == source].sort_values("date")
        fig.add_trace(go.Bar(x=sdata["date"], y=sdata["post_count"], name=source))
    fig.update_layout(barmode="stack", title="Post Volume by Source", xaxis_title="Date", yaxis_title="Posts")
    return fig

def topic_heatmap(df: pd.DataFrame) -> go.Figure:
    """
    df columns: party, topic, count
    """
    pivot = df.pivot_table(index="party", columns="topic", values="count", fill_value=0)
    fig = go.Figure(go.Heatmap(
        z=pivot.values.tolist(),
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale="RdYlGn",
        zmid=0,
    ))
    fig.update_layout(title="Party × Topic Frequency")
    return fig

def _sentiment_label(value: float) -> tuple:
    """Return (label, bar_color) for a sentiment value."""
    if value >= 0.15:
        return "Positive", "#27ae60"
    if value <= -0.15:
        return "Negative", "#e74c3c"
    return "Neutral", "#f39c12"


def sentiment_gauge(party: str, value: float) -> go.Figure:
    label, bar_color = _sentiment_label(value)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=round(value, 2),
        title={
            "text": f"<b>{party}</b><br><span style='font-size:11px;color:#555'>{label}</span>",
            "font": {"size": 15},
        },
        number={"font": {"size": 22}, "valueformat": "+.2f"},
        gauge={
            "axis": {
                "range": [-1, 1],
                "tickvals": [-1, -0.5, 0, 0.5, 1],
                "ticktext": ["-1", "-0.5", "0", "+0.5", "+1"],
                "tickwidth": 1,
                "tickfont": {"size": 9},
            },
            "bar": {"color": bar_color, "thickness": 0.25},
            "steps": [
                {"range": [-1, -0.15], "color": "#fde8e8"},
                {"range": [-0.15, 0.15], "color": "#fef9e7"},
                {"range": [0.15, 1], "color": "#e8f8e8"},
            ],
            "threshold": {
                "line": {"color": "#333", "width": 2},
                "thickness": 0.75,
                "value": 0,
            },
        },
    ))
    fig.update_layout(height=240, margin={"l": 20, "r": 20, "t": 60, "b": 10})
    return fig
