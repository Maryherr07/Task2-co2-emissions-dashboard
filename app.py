"""
Global CO2 Emissions Explorer
=============================
An interactive dashboard exploring fossil CO2 emissions and land-use carbon
flux from the EDGAR v7.0 dataset (European Commission JRC).

Five linked visualizations:
  1. Choropleth world map         — total emissions by country (overview)
  2. Bubble scatter               — carbon intensity vs per-capita
  3. Sector horizontal bar        — sector breakdown for selected country
  4. Multi-line trend             — top emitters over time
  5. LULUCF diverging bar         — land-use emissions/removals by region

Run locally:
    streamlit run app.py
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Global CO2 Emissions Explorer",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# DATA LOADING (cached so it only runs once)
# ============================================================
# Aggregate entries (not real countries) — excluded from country-level views.
# These are kept in a separate variable in case we want to show them later.
NON_COUNTRY_ENTRIES = {
    "GLOBAL TOTAL",
    "EU27",
    "International Aviation",
    "International Shipping",
}


@st.cache_data
def load_data():
    """Load all five cleaned CSVs and filter out non-country aggregates."""
    totals = pd.read_csv("data/totals.csv")
    sectors = pd.read_csv("data/sectors.csv")
    per_gdp = pd.read_csv("data/per_gdp.csv")
    per_capita = pd.read_csv("data/per_capita.csv")
    lulucf = pd.read_csv("data/lulucf.csv")

    # Drop aggregate "countries" so they don't pollute country-level charts
    totals = totals[~totals["Country"].isin(NON_COUNTRY_ENTRIES)]
    sectors = sectors[~sectors["Country"].isin(NON_COUNTRY_ENTRIES)]
    per_gdp = per_gdp[~per_gdp["Country"].isin(NON_COUNTRY_ENTRIES)]
    per_capita = per_capita[~per_capita["Country"].isin(NON_COUNTRY_ENTRIES)]

    return totals, sectors, per_gdp, per_capita, lulucf


totals, sectors, per_gdp, per_capita, lulucf = load_data()

# ============================================================
# HEADER
# ============================================================
st.title("🌍 Global CO2 Emissions Explorer")
st.markdown(
    "Explore fossil CO₂ emissions and land-use carbon flux across countries, "
    "sectors and regions. Use the sidebar to filter by year and select a country "
    "to drill into. The selected country is highlighted across multiple views."
)

# ============================================================
# SIDEBAR FILTERS
# ============================================================
st.sidebar.header("Filters")

# Year slider — restricted to years where ALL country-level metrics exist (1990+)
common_min_year = max(per_gdp["Year"].min(), totals["Year"].min())
common_max_year = min(per_gdp["Year"].max(), totals["Year"].max())
year = st.sidebar.slider(
    "Select year",
    min_value=int(common_min_year),
    max_value=int(common_max_year),
    value=int(common_max_year),
    step=1,
)

# Top-N selector for the trend chart
top_n = st.sidebar.slider(
    "Top N emitters to compare in trend chart",
    min_value=5, max_value=20, value=10, step=1,
)

# Country drill-down selector
country_list = sorted(totals["Country"].dropna().unique())
default_country = "China" if "China" in country_list else country_list[0]
selected_country = st.sidebar.selectbox(
    "Drill into a country",
    options=country_list,
    index=country_list.index(default_country),
)

st.sidebar.markdown("---")
st.sidebar.caption(
    "**Data source:** EDGAR v7.0 (European Commission JRC), 2022 release. "
    "Per-GDP data starts in 1990; LULUCF data is at macro-region level only."
)

# ============================================================
# ROW 1 — CHOROPLETH MAP (full width, hero chart)
# ============================================================
st.subheader(f"Total CO₂ Emissions by Country — {year}")

map_df = totals[totals["Year"] == year].copy()
fig_map = px.choropleth(
    map_df,
    locations="ISO3",
    color="Emissions_Mt",
    hover_name="Country",
    color_continuous_scale="Reds",
    labels={"Emissions_Mt": "Mt CO₂/yr"},
    projection="natural earth",
)
fig_map.update_layout(
    margin=dict(l=0, r=0, t=10, b=0),
    height=450,
    coloraxis_colorbar=dict(title="Mt CO₂/yr"),
)
st.plotly_chart(fig_map, use_container_width=True)
st.caption(
    "Darker red indicates higher absolute emissions. "
    "Answers: which countries are the largest contributors to global CO₂?"
)

# ============================================================
# ROW 2 — SCATTER + SECTOR BAR (side by side)
# ============================================================
col1, col2 = st.columns(2)

# ---------- Scatter ----------
with col1:
    st.subheader(f"Carbon Intensity vs. Per-Capita — {year}")

    a = per_gdp[per_gdp["Year"] == year][["Country", "ISO3", "tCO2_per_kUSD"]]
    b = per_capita[per_capita["Year"] == year][["Country", "tCO2_per_capita"]]
    c = totals[totals["Year"] == year][["Country", "Emissions_Mt"]]
    scatter_df = a.merge(b, on="Country").merge(c, on="Country").dropna()

    fig_scatter = px.scatter(
        scatter_df,
        x="tCO2_per_kUSD",
        y="tCO2_per_capita",
        size="Emissions_Mt",
        hover_name="Country",
        size_max=45,
        opacity=0.6,
        color_discrete_sequence=["#888888"],
        labels={
            "tCO2_per_kUSD": "Carbon intensity (t CO₂ / k USD GDP)",
            "tCO2_per_capita": "Per-capita emissions (t CO₂ / person)",
            "Emissions_Mt": "Total Mt CO₂",
        },
    )

    # Highlight the selected country in red
    if selected_country in scatter_df["Country"].values:
        sel = scatter_df[scatter_df["Country"] == selected_country]
        fig_scatter.add_trace(
            go.Scatter(
                x=sel["tCO2_per_kUSD"],
                y=sel["tCO2_per_capita"],
                mode="markers+text",
                text=sel["Country"],
                textposition="top center",
                marker=dict(size=18, color="crimson",
                            line=dict(width=2, color="black")),
                showlegend=False,
                hovertemplate=f"<b>{selected_country}</b><br>" +
                              "Intensity: %{x:.3f}<br>" +
                              "Per-capita: %{y:.2f}<extra></extra>",
            )
        )

    fig_scatter.update_layout(
        height=400, margin=dict(l=0, r=0, t=10, b=0), showlegend=False
    )
    st.plotly_chart(fig_scatter, use_container_width=True)
    st.caption(
        "Bubble size = total emissions. "
        f"Selected country ({selected_country}) shown in red. "
        "Reveals clusters and outliers in economic vs personal carbon intensity."
    )

# ---------- Sector Bar ----------
with col2:
    st.subheader(f"Sector Breakdown — {selected_country}, {year}")

    sec_df = sectors[
        (sectors["Country"] == selected_country) & (sectors["Year"] == year)
    ].dropna(subset=["Emissions_Mt"]).sort_values("Emissions_Mt", ascending=True)

    if sec_df.empty:
        st.info(f"No sector data available for {selected_country} in {year}.")
    else:
        fig_sector = px.bar(
            sec_df,
            x="Emissions_Mt",
            y="Sector",
            orientation="h",
            color="Emissions_Mt",
            color_continuous_scale="Oranges",
            labels={"Emissions_Mt": "Mt CO₂/yr", "Sector": ""},
            text="Emissions_Mt",
        )
        fig_sector.update_traces(
            texttemplate="%{text:.1f}", textposition="outside"
        )
        fig_sector.update_layout(
            height=400,
            margin=dict(l=0, r=20, t=10, b=0),
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig_sector, use_container_width=True)
        st.caption(
            "Which sectors dominate emissions in the selected country? "
            "Bars sorted from smallest to largest contributor."
        )

# ============================================================
# ROW 3 — TREND LINE + LULUCF DIVERGING BAR
# ============================================================
col3, col4 = st.columns(2)

# ---------- Trend ----------
with col3:
    st.subheader(f"Emissions Trend — Top {top_n} vs {selected_country}")

    latest = totals[totals["Year"] == year].nlargest(top_n, "Emissions_Mt")
    top_countries = latest["Country"].tolist()
    if selected_country not in top_countries:
        top_countries.append(selected_country)

    trend_df = totals[totals["Country"].isin(top_countries)]
    fig_trend = px.line(
        trend_df,
        x="Year", y="Emissions_Mt",
        color="Country",
        labels={"Emissions_Mt": "Mt CO₂/yr"},
    )

    # Emphasize the selected country
    for trace in fig_trend.data:
        if trace.name == selected_country:
            trace.line.width = 5
            trace.line.color = "crimson"
        else:
            trace.line.width = 1.5
            trace.opacity = 0.55

    fig_trend.update_layout(
        height=420, margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(font=dict(size=9), itemsizing="constant"),
    )
    st.plotly_chart(fig_trend, use_container_width=True)
    st.caption(
        f"Historical trajectory of the top {top_n} current emitters. "
        f"{selected_country} highlighted in red."
    )

# ---------- LULUCF Diverging Bar ----------
with col4:
    st.subheader(f"Land-Use Carbon Flux by Region — {year}")

    # Use 'Net' sector — total land-use flux per region
    # LULUCF data is 1990-2020, so cap at 2020
    lulucf_year = min(year, int(lulucf["Year"].max()))
    lulucf_df = lulucf[
        (lulucf["Sector"] == "Net") & (lulucf["Year"] == lulucf_year)
    ].copy()
    # Exclude WORLD and EU27 to keep only mutually exclusive macro-regions
    lulucf_df = lulucf_df[~lulucf_df["Region"].isin(["WORLD", "EU27"])]
    lulucf_df = lulucf_df.sort_values("Emissions_Mt", ascending=True)

    if lulucf_df.empty:
        st.info(f"No LULUCF data available for {lulucf_year}.")
    else:
        # Diverging color: red = positive (emitter), blue = negative (sink)
        colors = ["#4575b4" if v < 0 else "#d73027"
                  for v in lulucf_df["Emissions_Mt"]]

        fig_lulucf = go.Figure(
            go.Bar(
                x=lulucf_df["Emissions_Mt"],
                y=lulucf_df["Region"],
                orientation="h",
                marker_color=colors,
                text=[f"{v:+.0f}" for v in lulucf_df["Emissions_Mt"]],
                textposition="outside",
                hovertemplate="<b>%{y}</b><br>" +
                              "Net flux: %{x:+.1f} Mt CO₂<extra></extra>",
            )
        )
        fig_lulucf.add_vline(x=0, line_width=1, line_color="black")
        fig_lulucf.update_layout(
            height=420,
            margin=dict(l=0, r=20, t=10, b=0),
            xaxis_title="Net land-use CO₂ flux (Mt CO₂/yr)",
            yaxis_title="",
        )
        if lulucf_year != year:
            fig_lulucf.add_annotation(
                text=f"Showing {lulucf_year} (latest LULUCF data)",
                xref="paper", yref="paper", x=1, y=1.05,
                showarrow=False, font=dict(size=10, color="gray"),
            )
        st.plotly_chart(fig_lulucf, use_container_width=True)
        st.caption(
            "🔵 Blue = net carbon sink (forests absorb more than is released). "
            "🔴 Red = net land-use emitter (deforestation, fires). "
            "Contrasts with the country-level fossil emissions above."
        )

# ============================================================
# FOOTER
# ============================================================
st.markdown("---")
st.caption(
    "📊 Built with Streamlit + Plotly · Data: EDGAR v7.0 FT2021 · "
    "European Commission Joint Research Centre, 2022 · "
    
)
