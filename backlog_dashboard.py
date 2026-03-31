"""
Backlogged Permits Dashboard — Streamlit
========================================
Drop-in replacement for the Jupyter ipywidgets version.

Run locally:
    pip install streamlit plotly pandas
    streamlit run backlog_dashboard.py

Deploy free:
    https://streamlit.io/cloud  (connect your GitHub repo, done)
"""

import streamlit as st
import plotly.express as px
import pandas as pd

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Backlogged Permits",
    page_icon="📋",
    layout="wide",
)

# ── Custom CSS — cleaner look ─────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* Top header bar */
.dash-header {
    background: linear-gradient(135deg, #003d72 0%, #0072bc 100%);
    border-radius: 12px;
    padding: 20px 28px;
    margin-bottom: 24px;
    color: white;
}
.dash-header h1 { margin: 0; font-size: 22px; font-weight: 600; letter-spacing: -0.3px; }
.dash-header p  { margin: 4px 0 0; font-size: 13px; opacity: 0.75; }

/* Region selector pills */
.stMultiSelect [data-baseweb="tag"] {
    background-color: #0072bc !important;
    border-radius: 6px !important;
}

/* Detail table */
.detail-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
    font-family: 'DM Sans', sans-serif;
}
.detail-table th {
    background: #003d72;
    color: white;
    padding: 8px 12px;
    text-align: left;
    white-space: nowrap;
    font-weight: 500;
}
.detail-table td {
    padding: 6px 12px;
    border-bottom: 1px solid #e4edf7;
    color: #1a3a5c;
}
.detail-table tr:nth-child(even) td { background: #f4f9ff; }
.detail-table tr:hover td           { background: #dceeff; }

/* Info box */
.info-box {
    background: #f0f7ff;
    border-left: 4px solid #0072bc;
    border-radius: 0 8px 8px 0;
    padding: 12px 16px;
    font-size: 13px;
    color: #1a3a5c;
    margin-bottom: 12px;
}

/* Card container */
.card {
    background: white;
    border: 1px solid #e0ecf8;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 2px 8px rgba(0,114,188,0.07);
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# ── YOUR DATA SETUP — replace this block with your actual df / regional_backlog
# ══════════════════════════════════════════════════════════════════════════════
# Example stub — delete and use your real dataframes:
@st.cache_data
def load_data():
    # ------------------------------------------------------------------ #
    # REPLACE THIS with however you currently load df and regional_backlog #
    # ------------------------------------------------------------------ #
    import numpy as np
    rng = np.random.default_rng(42)
    regions = ["Northeast", "Southeast", "Midwest", "Southwest", "West"]
    years   = list(range(2018, 2025))

    rows = []
    for region in regions:
        for year in years:
            n = int(rng.integers(5, 40))
            for _ in range(n):
                rows.append({
                    "Region": region,
                    "County": rng.choice(["County A", "County B", "County C"]),
                    "Municipality": rng.choice(["Town 1", "Town 2", "City 3"]),
                    "Client": f"Client {rng.integers(1,20)}",
                    "Site Name": f"Site {rng.integers(100,999)}",
                    "Site ID": f"S{rng.integers(1000,9999)}",
                    "PF Name": f"Facility {rng.integers(1,50)}",
                    "PF ID": f"PF{rng.integers(1000,9999)}",
                    "Active Facility": rng.choice(["Yes", "No"]),
                    "Application Type": rng.choice(["New", "Renewal"]),
                    "Permit Type": rng.choice(["Type A", "Type B", "Type C"]),
                    "General Permit Type": rng.choice(["GP-1", "GP-2"]),
                    "Disposition Code": rng.choice(["PEND", "BACK", "HOLD"]),
                    "Date Received": f"202{rng.integers(0,5)}-0{rng.integers(1,9)}-15",
                    "Date Disposed": "",
                    "Date Expires": f"202{rng.integers(5,9)}-0{rng.integers(1,9)}-01",
                    "Permit Hyperlink": rng.choice([
                        "https://example.gov/permit/123",
                        "https://example.gov/permit/456",
                        None
                    ]),
                    "Disposition Year": year,
                    "backlogged": True,
                })

    df = pd.DataFrame(rows)
    regional_backlog = df.groupby(["Disposition Year", "Region"]).size().unstack(fill_value=0)
    regions_list = regional_backlog.columns.tolist()
    return df, regional_backlog, regions_list

df, regional_backlog, regions = load_data()
# ══════════════════════════════════════════════════════════════════════════════


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="dash-header">
  <h1>📋 Backlogged Permits Dashboard</h1>
  <p>New &amp; Renewal permits · Click a data point to inspect individual records</p>
</div>
""", unsafe_allow_html=True)


# ── Sidebar controls ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🗂️ Filter Regions")
    selected_regions = st.multiselect(
        label="Visible regions",
        options=regions,
        default=regions,
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("### 📅 Year Range")
    years_available = sorted(regional_backlog.index.tolist())
    year_range = st.slider(
        "Select range",
        min_value=int(min(years_available)),
        max_value=int(max(years_available)),
        value=(int(min(years_available)), int(max(years_available))),
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.caption("Select a single region then click a point on the chart to drill into permit records.")


# ── Filter data ───────────────────────────────────────────────────────────────
filtered_backlog = regional_backlog.loc[
    (regional_backlog.index >= year_range[0]) &
    (regional_backlog.index <= year_range[1]),
    [r for r in selected_regions if r in regional_backlog.columns]
]

# ── Chart ─────────────────────────────────────────────────────────────────────
DETAIL_COLS = [
    "Region", "County", "Municipality", "Client", "Site Name", "Site ID",
    "PF Name", "PF ID", "Active Facility", "Application Type", "Permit Type",
    "General Permit Type", "Disposition Code",
    "Date Received", "Date Disposed", "Date Expires", "Permit Hyperlink",
]

PALETTE = [
    "#0072bc", "#e87722", "#00a86b", "#c8102e", "#7b2d8b",
    "#f5c400", "#00b0ca", "#ff6b35",
]

fig = px.line(
    filtered_backlog.reset_index(),
    x="Disposition Year",
    y=filtered_backlog.columns.tolist(),
    markers=True,
    title="",
    labels={
        "variable": "Region",
        "Disposition Year": "Year",
        "value": "Backlogged Permits",
    },
    color_discrete_sequence=PALETTE,
    template="simple_white",
)
fig.update_layout(
    legend_title_text="Region",
    hovermode="x unified",
    font=dict(family="DM Sans, sans-serif", size=12, color="#1a3a5c"),
    legend=dict(orientation="h", y=1.08, x=0),
    margin=dict(l=10, r=10, t=30, b=10),
    plot_bgcolor="white",
    paper_bgcolor="white",
    xaxis=dict(
        showgrid=True,
        gridcolor="#eef3f9",
        linecolor="#c8d9ec",
        title_font=dict(size=12),
    ),
    yaxis=dict(
        showgrid=True,
        gridcolor="#eef3f9",
        linecolor="#c8d9ec",
        title="Backlogged Permits",
        title_font=dict(size=12),
    ),
    height=420,
)
fig.update_traces(line=dict(width=2.5), marker=dict(size=7))

# Capture click via Streamlit plotly_events (or native st.plotly_chart select)
clicked = st.plotly_chart(
    fig,
    use_container_width=True,
    on_select="rerun",           # Streamlit ≥ 1.35 native click events
    key="backlog_chart",
    selection_mode="points",
)


# ── Detail panel ──────────────────────────────────────────────────────────────
st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)

selection = clicked.get("selection", {}) if clicked else {}
points    = selection.get("points", [])

if not points:
    st.markdown(
        '<div class="info-box">🖱️ <b>Click any data point</b> on the chart above to inspect the underlying permit records.</div>',
        unsafe_allow_html=True,
    )
else:
    pt     = points[0]
    year   = int(pt["x"])
    region = pt.get("customdata", [None])[0] or pt.get("legendgroup", "")

    # Fall back: derive region from trace index if customdata unavailable
    if not region and "curve_number" in pt:
        region = filtered_backlog.columns[pt["curve_number"]]

    mask = (
        (df["Region"] == region) &
        (df["Disposition Year"] == year) &
        (df["backlogged"] == True)
    )
    subset = df[mask].copy()

    cols   = [c for c in DETAIL_COLS if c in subset.columns]
    subset = subset[cols]

    col1, col2, col3 = st.columns([2, 1, 1])
    col1.metric("Region",  region)
    col2.metric("Year",    year)
    col3.metric("Permits", len(subset))

    if subset.empty:
        st.info("No records found for this selection.")
    else:
        # Make hyperlinks clickable
        if "Permit Hyperlink" in subset.columns:
            subset["Permit Hyperlink"] = subset["Permit Hyperlink"].apply(
                lambda v: f'<a href="{v}" target="_blank">View ↗</a>'
                if pd.notna(v) and str(v).startswith("http") else (v or "")
            )

        # Build styled HTML table
        headers  = "".join(f"<th>{c}</th>" for c in cols)
        rows_html = ""
        for _, row in subset.iterrows():
            cells = "".join(
                f"<td>{'' if pd.isna(v) else v}</td>" for v in row
            )
            rows_html += f"<tr>{cells}</tr>"

        table_html = f"""
        <div style="overflow-x:auto; max-height:340px; overflow-y:auto;
                    border:1px solid #dde8f5; border-radius:8px;">
          <table class="detail-table">
            <thead><tr>{headers}</tr></thead>
            <tbody>{rows_html}</tbody>
          </table>
        </div>
        """
        st.markdown(table_html, unsafe_allow_html=True)

        # Download button
        csv = df[mask][[c for c in DETAIL_COLS if c in df.columns]].to_csv(index=False)
        st.download_button(
            label="⬇️ Download these records as CSV",
            data=csv,
            file_name=f"backlog_{region}_{year}.csv",
            mime="text/csv",
            use_container_width=False,
        )