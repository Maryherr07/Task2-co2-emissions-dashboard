"""
Global CO2 Emissions Explorer (2025 Edition)
============================================
Interactive dashboard exploring fossil CO2 emissions and land-use carbon
flux from the EDGAR 2025 release (European Commission JRC).
 
Data through 2024, eight sectors, country-level LULUCF.
 
Visualizations:
  1. KPI metrics row              — quick context numbers
  2. Choropleth world map         — total emissions by country
  3. Bubble scatter               — carbon intensity vs per-capita
  4. Sector horizontal bar        — sector breakdown for selected country
  5. Multi-line trend             — customizable country comparison
  6. LULUCF diverging bar         — toggle: macro-regions OR selected country
 
Run locally:
    streamlit run app_2025.py
"""
 
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
 
# ============================================================
# CONSTANTS
# ============================================================
NON_COUNTRY_ENTRIES = {
    "GLOBAL TOTAL", "EU27", "International Aviation", "International Shipping",
}
 
DATA_DIR = "data_2025"
 
# Categorical color palette for sectors — distinct, accessible
SECTOR_COLORS = {
    "Power Industry":         "#8B4513",  # saddle brown — fossil power
    "Industrial Combustion":  "#CD5C5C",  # indian red — heavy industry
    "Processes":              "#DAA520",  # goldenrod — chemical/cement
    "Transport":              "#4682B4",  # steel blue — mobility
    "Buildings":              "#9370DB",  # medium purple — residential/commercial
    "Fuel Exploitation":      "#2F4F4F",  # dark slate gray — extraction
    "Agriculture":            "#6B8E23",  # olive drab — land
    "Waste":                  "#708090",  # slate gray — disposal
}
 
# Region (continent) mapping by ISO3 → continent name, for the region filter.
# Built from a small static lookup so we don't need an extra dependency.
REGION_BY_ISO = {
    # Europe
    "ALB":"Europe","AND":"Europe","AUT":"Europe","BEL":"Europe","BGR":"Europe","BIH":"Europe",
    "BLR":"Europe","CHE":"Europe","CYP":"Europe","CZE":"Europe","DEU":"Europe","DNK":"Europe",
    "ESP":"Europe","EST":"Europe","FIN":"Europe","FRA":"Europe","FRK":"Europe","GBR":"Europe",
    "GRC":"Europe","HRV":"Europe","HUN":"Europe","IRL":"Europe","ISL":"Europe","ITA":"Europe",
    "LIE":"Europe","LTU":"Europe","LUX":"Europe","LVA":"Europe","MCO":"Europe","MDA":"Europe",
    "MKD":"Europe","MLT":"Europe","MNE":"Europe","NLD":"Europe","NOR":"Europe","POL":"Europe",
    "PRT":"Europe","ROU":"Europe","SCG":"Europe","SMR":"Europe","SRB":"Europe","SVK":"Europe",
    "SVN":"Europe","SWE":"Europe","UKR":"Europe","VAT":"Europe","FAR":"Europe","GIB":"Europe",
    "FRO":"Europe",
    # Asia
    "AFG":"Asia","ARM":"Asia","AZE":"Asia","BGD":"Asia","BHR":"Asia","BRN":"Asia","BTN":"Asia",
    "CHN":"Asia","GEO":"Asia","HKG":"Asia","IDN":"Asia","IND":"Asia","IRN":"Asia","IRQ":"Asia",
    "ISR":"Asia","JOR":"Asia","JPN":"Asia","KAZ":"Asia","KGZ":"Asia","KHM":"Asia","KOR":"Asia",
    "KWT":"Asia","LAO":"Asia","LBN":"Asia","LKA":"Asia","MAC":"Asia","MDV":"Asia","MMR":"Asia",
    "MNG":"Asia","MYS":"Asia","NPL":"Asia","OMN":"Asia","PAK":"Asia","PHL":"Asia","PRK":"Asia",
    "PSE":"Asia","QAT":"Asia","SAU":"Asia","SGP":"Asia","SYR":"Asia","TJK":"Asia","TKM":"Asia",
    "TLS":"Asia","TUR":"Asia","TWN":"Asia","UZB":"Asia","VNM":"Asia","YEM":"Asia","ARE":"Asia",
    "RUS":"Asia","THA":"Asia",
    # Africa
    "AGO":"Africa","BDI":"Africa","BEN":"Africa","BFA":"Africa","BWA":"Africa","CAF":"Africa",
    "CIV":"Africa","CMR":"Africa","COD":"Africa","COG":"Africa","COM":"Africa","CPV":"Africa",
    "DJI":"Africa","DZA":"Africa","EGY":"Africa","ERI":"Africa","ESH":"Africa","ETH":"Africa",
    "GAB":"Africa","GHA":"Africa","GIN":"Africa","GMB":"Africa","GNB":"Africa","GNQ":"Africa",
    "KEN":"Africa","LBR":"Africa","LBY":"Africa","LSO":"Africa","MAR":"Africa","MDG":"Africa",
    "MLI":"Africa","MOZ":"Africa","MRT":"Africa","MUS":"Africa","MWI":"Africa","NAM":"Africa",
    "NER":"Africa","NGA":"Africa","RWA":"Africa","SDN":"Africa","SEN":"Africa","SHN":"Africa",
    "SLE":"Africa","SOM":"Africa","SSD":"Africa","STP":"Africa","SWZ":"Africa","SYC":"Africa",
    "TCD":"Africa","TGO":"Africa","TUN":"Africa","TZA":"Africa","UGA":"Africa","ZAF":"Africa",
    "ZMB":"Africa","ZWE":"Africa","REU":"Africa",
    # Americas
    "ABW":"Americas","AIA":"Americas","ANT":"Americas","ARG":"Americas","ATG":"Americas","BHS":"Americas",
    "BLZ":"Americas","BMU":"Americas","BOL":"Americas","BRA":"Americas","BRB":"Americas",
    "CAN":"Americas","CHL":"Americas","COL":"Americas","CRI":"Americas","CUB":"Americas",
    "CUW":"Americas","CYM":"Americas","DMA":"Americas","DOM":"Americas","ECU":"Americas",
    "FLK":"Americas","GLP":"Americas","GRD":"Americas","GRL":"Americas","GTM":"Americas",
    "GUF":"Americas","GUY":"Americas","HND":"Americas","HTI":"Americas","JAM":"Americas",
    "KNA":"Americas","LCA":"Americas","MEX":"Americas","MTQ":"Americas","NIC":"Americas",
    "PAN":"Americas","PER":"Americas","PRI":"Americas","PRY":"Americas","SLV":"Americas",
    "SPM":"Americas","SUR":"Americas","TCA":"Americas","TTO":"Americas","URY":"Americas",
    "USA":"Americas","VCT":"Americas","VEN":"Americas","VGB":"Americas",
    # Oceania
    "AUS":"Oceania","COK":"Oceania","FJI":"Oceania","FSM":"Oceania","KIR":"Oceania",
    "MHL":"Oceania","NCL":"Oceania","NRU":"Oceania","NZL":"Oceania","PLW":"Oceania",
    "PNG":"Oceania","PYF":"Oceania","SLB":"Oceania","TON":"Oceania","TUV":"Oceania",
    "VUT":"Oceania","WSM":"Oceania",
}
 
 
# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Global CO2 Emissions Explorer (2025 Edition)",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)
 
 
# ============================================================
# DATA LOADING
# ============================================================
@st.cache_data
def load_data():
    """Load all six cleaned CSVs from data_2025/."""
    totals = pd.read_csv(f"{DATA_DIR}/totals.csv")
    sectors = pd.read_csv(f"{DATA_DIR}/sectors.csv")
    per_gdp = pd.read_csv(f"{DATA_DIR}/per_gdp.csv")
    per_capita = pd.read_csv(f"{DATA_DIR}/per_capita.csv")
    lulucf_regions = pd.read_csv(f"{DATA_DIR}/lulucf_regions.csv")
    lulucf_countries = pd.read_csv(f"{DATA_DIR}/lulucf_countries.csv")
 
    for df in (totals, sectors, per_gdp, per_capita):
        df.drop(df[df["Country"].isin(NON_COUNTRY_ENTRIES)].index, inplace=True)
 
    # Annotate continent for region filter
    totals["Continent"] = totals["ISO3"].map(REGION_BY_ISO).fillna("Other")
 
    return totals, sectors, per_gdp, per_capita, lulucf_regions, lulucf_countries
 
 
totals, sectors, per_gdp, per_capita, lulucf_regions, lulucf_countries = load_data()
 
# ============================================================
# HEADER
# ============================================================
st.title("🌍 Global CO2 Emissions Explorer")
st.markdown(
    "Explore fossil CO₂ emissions and land-use carbon flux across countries, "
    "sectors and regions. Data: **EDGAR 2025 release** (European Commission JRC), "
    "**1970–2024**."
)
 
# About expander
with st.expander("ℹ️ About this dashboard"):
    st.markdown(
        """
**What you can do here**
 
This interactive dashboard helps you explore global fossil CO₂ emissions
along five dimensions: total volume, economic intensity, per-capita footprint,
sectoral makeup and land-use carbon flux. Use the filters in the left sidebar
to narrow the year, region, country selection and chart options.
 
**Five questions it helps answer**
 
1. *Which countries are the largest absolute emitters?* → world map
2. *How efficient is each economy at producing emissions?* → carbon-intensity scatter
3. *Which sectors dominate emissions in a given country?* → sector bar chart
4. *How have specific countries' emissions evolved over time?* → multi-line trend
5. *Which regions are net land-use carbon sinks vs. sources?* → LULUCF diverging bar
 
**How to interact**
 
- Move the **year slider** to see any year from 1990 to 2024.
- Filter by **continent** to focus on a region of the world.
- Select up to ~10 countries in **"Compare countries"** to add them to the trend chart.
- The country picked in **"Drill into a country"** is highlighted in red across charts.
- Toggle the **LULUCF view** between macro-regions and the selected country.
- **Double-click** any country in the trend legend to isolate it. Single-click others to add them back.
 
**Data source**
 
EDGAR (Emissions Database for Global Atmospheric Research) v2025, produced
by the European Commission Joint Research Centre. Two source files are used:
the fossil-CO₂-only booklet for emissions and the full GHG booklet for LULUCF.
        """
    )
 
# ============================================================
# SIDEBAR
# ============================================================
st.sidebar.header("🔍 Filters")
 
# --- Year slider ---
common_min_year = max(per_gdp["Year"].min(), totals["Year"].min())
common_max_year = min(per_gdp["Year"].max(), totals["Year"].max())
year = st.sidebar.slider(
    "Year",
    min_value=int(common_min_year),
    max_value=int(common_max_year),
    value=int(common_max_year),
    step=1,
)
 
# --- Continent filter ---
all_continents = sorted([c for c in totals["Continent"].unique() if c != "Other"])
selected_continents = st.sidebar.multiselect(
    "Continents to include",
    options=all_continents,
    default=all_continents,
    help="Filter the map, scatter and country dropdown by continent.",
)
 
# Apply continent filter to a working copy
totals_f = totals[totals["Continent"].isin(selected_continents)] if selected_continents else totals
 
# --- Country drill-down ---
country_list = sorted(totals_f["Country"].dropna().unique())
default_country = "China" if "China" in country_list else (country_list[0] if country_list else None)
selected_country = st.sidebar.selectbox(
    "Drill into a country",
    options=country_list,
    index=country_list.index(default_country) if default_country else 0,
    help="Highlighted in red across the scatter, sector and LULUCF (when in country mode) charts.",
)
 
st.sidebar.markdown("---")
st.sidebar.subheader("📈 Trend chart")
 
# --- Trend mode: top-N or custom selection ---
trend_mode = st.sidebar.radio(
    "Select countries by",
    options=["top_n", "custom"],
    format_func=lambda v: "Top N emitters" if v == "top_n" else "Custom selection",
)
 
if trend_mode == "top_n":
    top_n = st.sidebar.slider(
        "How many top emitters", min_value=3, max_value=20, value=10, step=1,
    )
    custom_countries = []
else:
    top_n = 0
    all_countries_for_picker = sorted(totals["Country"].dropna().unique())
    default_pick = [c for c in ["China", "United States", "India", "Brazil"]
                    if c in all_countries_for_picker]
    custom_countries = st.sidebar.multiselect(
        "Compare these countries",
        options=all_countries_for_picker,
        default=default_pick,
        help="Pick any 2–10 countries to compare on the trend chart.",
    )
 
st.sidebar.markdown("---")
st.sidebar.subheader("🌳 LULUCF chart")
 
# --- Sticky LULUCF radio with stable values ---
lulucf_view = st.sidebar.radio(
    "View",
    options=["region", "country"],
    format_func=lambda v: "🌍 Macro-regions" if v == "region" else "🏳️ Selected country",
    help="Switch view of the land-use carbon flux chart. "
         "Your choice is preserved when you change country.",
)
 
st.sidebar.markdown("---")
st.sidebar.caption(
    "**Source:** EDGAR 2025 (European Commission JRC). "
    "Per-GDP data starts in 1990. LULUCF = Land Use, Land-Use Change & Forestry."
)
 
# ============================================================
# KPI METRICS ROW
# ============================================================
totals_year = totals[totals["Year"] == year]
global_total = totals_year["Emissions_Mt"].sum()
top_emitter_row = totals_year.nlargest(1, "Emissions_Mt").iloc[0]
selected_row = totals_year[totals_year["Country"] == selected_country]
 
# Year-over-year change for the global total
prev_year_total = totals[totals["Year"] == year - 1]["Emissions_Mt"].sum() if year > common_min_year else None
yoy_global = ((global_total - prev_year_total) / prev_year_total * 100) if prev_year_total else None
 
# Year-over-year change for the selected country
sel_yoy = None
if not selected_row.empty:
    sel_now = selected_row["Emissions_Mt"].iloc[0]
    prev = totals[(totals["Country"] == selected_country) & (totals["Year"] == year - 1)]
    if not prev.empty:
        sel_yoy = (sel_now - prev["Emissions_Mt"].iloc[0]) / prev["Emissions_Mt"].iloc[0] * 100
 
m1, m2, m3, m4 = st.columns(4)
m1.metric("Year", str(year))
m2.metric(
    "🌐 Global total",
    f"{global_total:,.0f} Mt CO₂",
    f"{yoy_global:+.1f}% vs {year-1}" if yoy_global is not None else None,
)
m3.metric(
    f"🥇 Top emitter ({top_emitter_row['Country']})",
    f"{top_emitter_row['Emissions_Mt']:,.0f} Mt",
    f"{top_emitter_row['Emissions_Mt']/global_total*100:.1f}% of world",
)
if not selected_row.empty:
    m4.metric(
        f"📍 {selected_country}",
        f"{selected_row['Emissions_Mt'].iloc[0]:,.0f} Mt",
        f"{sel_yoy:+.1f}% vs {year-1}" if sel_yoy is not None else None,
    )
else:
    m4.metric(f"📍 {selected_country}", "no data")
 
st.markdown("---")
 
# ============================================================
# ROW 1 — CHOROPLETH MAP (full width)
# ============================================================
st.subheader(f"Total Fossil CO₂ Emissions by Country — {year}")
 
map_df = totals_f[totals_f["Year"] == year].copy()
fig_map = px.choropleth(
    map_df,
    locations="ISO3",
    color="Emissions_Mt",
    hover_name="Country",
    color_continuous_scale="Reds",
    labels={"Emissions_Mt": "Mt CO₂/yr"},
    projection="equirectangular",
)
fig_map.update_geos(
    showframe=False,
    showcoastlines=True,
    coastlinecolor="rgba(120,120,120,0.4)",
    showland=True,
    landcolor="rgba(240,240,240,0.05)",
    showocean=False,
    fitbounds="locations" if selected_continents and len(selected_continents) < len(all_continents) else False,
)
fig_map.update_layout(
    margin=dict(l=0, r=0, t=10, b=0),
    height=500,
    coloraxis_colorbar=dict(title="Mt CO₂/yr", thickness=15, len=0.7),
    transition_duration=400,
)
st.plotly_chart(fig_map, use_container_width=True)
 
cap_cols = st.columns([4, 1])
cap_cols[0].caption(
    "Darker red = higher absolute emissions. "
    "Hover any country for details. Map auto-zooms when you filter by continent."
)
csv_map = map_df[["Country", "ISO3", "Emissions_Mt"]].to_csv(index=False).encode()
cap_cols[1].download_button(
    "⬇️ Map data (CSV)", csv_map, f"emissions_{year}.csv", "text/csv",
    use_container_width=True,
)
 
# ============================================================
# ROW 2 — SCATTER + SECTOR BAR
# ============================================================
col1, col2 = st.columns(2)
 
# ---------- Scatter ----------
with col1:
    st.subheader(f"Carbon Intensity vs. Per-Capita — {year}")
 
    a = per_gdp[per_gdp["Year"] == year][["Country", "ISO3", "tCO2_per_kUSD"]]
    b = per_capita[per_capita["Year"] == year][["Country", "tCO2_per_capita"]]
    c = totals_f[totals_f["Year"] == year][["Country", "Emissions_Mt", "Continent"]]
    scatter_df = a.merge(b, on="Country").merge(c, on="Country").dropna()
 
    fig_scatter = px.scatter(
        scatter_df,
        x="tCO2_per_kUSD",
        y="tCO2_per_capita",
        size="Emissions_Mt",
        hover_name="Country",
        color="Continent",
        size_max=45,
        opacity=0.65,
        labels={
            "tCO2_per_kUSD": "Carbon intensity (t CO₂ / k USD GDP)",
            "tCO2_per_capita": "Per-capita emissions (t CO₂ / person)",
            "Emissions_Mt": "Total Mt CO₂",
        },
    )
 
    if selected_country in scatter_df["Country"].values:
        sel = scatter_df[scatter_df["Country"] == selected_country]
        # Outer ring
        fig_scatter.add_trace(go.Scatter(
            x=sel["tCO2_per_kUSD"], y=sel["tCO2_per_capita"],
            mode="markers",
            marker=dict(size=34, color="rgba(0,0,0,0)",
                        line=dict(width=3, color="crimson")),
            showlegend=False, hoverinfo="skip",
        ))
        # Solid inner marker + label
        fig_scatter.add_trace(go.Scatter(
            x=sel["tCO2_per_kUSD"], y=sel["tCO2_per_capita"],
            mode="markers+text",
            text=sel["Country"], textposition="top center",
            textfont=dict(size=12, color="crimson"),
            marker=dict(size=14, color="crimson",
                        line=dict(width=2, color="white")),
            showlegend=False,
            hovertemplate=f"<b>{selected_country}</b><br>"
                          "Intensity: %{x:.3f}<br>"
                          "Per-capita: %{y:.2f}<extra></extra>",
        ))
 
    fig_scatter.update_layout(
        height=420, margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation="h", y=-0.2, font=dict(size=9)),
        transition_duration=400,
    )
    st.plotly_chart(fig_scatter, use_container_width=True)
    st.caption(
        f"Bubble size = total emissions, color = continent. "
        f"{selected_country} highlighted in red."
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
            color="Sector",
            color_discrete_map=SECTOR_COLORS,
            labels={"Emissions_Mt": "Mt CO₂/yr", "Sector": ""},
            text="Emissions_Mt",
        )
        fig_sector.update_traces(
            texttemplate="%{text:.1f}", textposition="outside",
        )
        fig_sector.update_layout(
            height=420,
            margin=dict(l=0, r=40, t=10, b=0),
            showlegend=False,
            transition_duration=400,
        )
        st.plotly_chart(fig_sector, use_container_width=True)
        st.caption(
            "Distinct color per sector. Bars sorted from smallest to largest contributor."
        )
 
# ============================================================
# ROW 3 — TREND + LULUCF
# ============================================================
col3, col4 = st.columns(2)
 
# ---------- Trend ----------
with col3:
    if trend_mode == "top_n":
        st.subheader(f"Emissions Trend — Top {top_n} vs {selected_country}")
        latest = totals[totals["Year"] == year].nlargest(top_n, "Emissions_Mt")
        trend_countries = latest["Country"].tolist()
        if selected_country not in trend_countries:
            trend_countries.append(selected_country)
    else:
        st.subheader("Emissions Trend — Custom comparison")
        trend_countries = list(custom_countries)
        if selected_country not in trend_countries:
            trend_countries.append(selected_country)
 
    if not trend_countries:
        st.info("Select at least one country to display the trend chart.")
    else:
        trend_df = totals[totals["Country"].isin(trend_countries)]
        fig_trend = px.line(
            trend_df,
            x="Year", y="Emissions_Mt",
            color="Country",
            labels={"Emissions_Mt": "Mt CO₂/yr"},
        )
        for trace in fig_trend.data:
            if trace.name == selected_country:
                trace.line.width = 5
                trace.line.color = "crimson"
            else:
                trace.line.width = 1.8
                trace.opacity = 0.7
 
        # Vertical line at the selected year
        fig_trend.add_vline(
            x=year, line_width=1, line_dash="dash", line_color="gray",
            annotation_text=str(year), annotation_position="top",
        )
 
        fig_trend.update_layout(
            height=440,
            margin=dict(l=0, r=0, t=10, b=10),
            legend=dict(
                orientation="h", yanchor="top", y=-0.18,
                xanchor="center", x=0.5,
                font=dict(size=9), itemsizing="constant",
            ),
            transition_duration=400,
        )
        st.plotly_chart(fig_trend, use_container_width=True)
        st.caption(
            "💡 **Tip:** double-click any country in the legend to isolate it; "
            "single-click others to add them back. Selected country in red."
        )
 
# ---------- LULUCF ----------
with col4:
    if lulucf_view == "region":
        st.subheader(f"Land-Use Carbon Flux by Region — {year}")
        lulucf_df = lulucf_regions[
            (lulucf_regions["Sector"] == "Net") & (lulucf_regions["Year"] == year)
        ].copy().sort_values("Emissions_Mt", ascending=True)
        y_col = "Region"
        chart_caption = (
            "🔵 Blue = net carbon **sink** (forests absorb more than is released). "
            "🔴 Red = net land-use **source** (deforestation, fires). "
            "Aggregated by macro-region."
        )
    else:
        st.subheader(f"Land-Use Flux Breakdown — {selected_country}, {year}")
        lulucf_df = lulucf_countries[
            (lulucf_countries["Country"] == selected_country)
            & (lulucf_countries["Year"] == year)
            & (lulucf_countries["Sector"] != "Net")
        ].copy().sort_values("Emissions_Mt", ascending=True)
        y_col = "Sector"
        chart_caption = (
            f"Land-use sub-sector breakdown for **{selected_country}**. "
            "🔵 Blue = sink, 🔴 Red = source."
        )
 
    if lulucf_df.empty:
        st.info(f"No LULUCF data available for this selection in {year}.")
    else:
        colors = ["#4575b4" if v < 0 else "#d73027"
                  for v in lulucf_df["Emissions_Mt"]]
 
        fig_lulucf = go.Figure(go.Bar(
            x=lulucf_df["Emissions_Mt"],
            y=lulucf_df[y_col],
            orientation="h",
            marker_color=colors,
            text=[f"{v:+.0f}" for v in lulucf_df["Emissions_Mt"]],
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>"
                          "Net flux: %{x:+.1f} Mt CO₂<extra></extra>",
        ))
        fig_lulucf.add_vline(x=0, line_width=1, line_color="gray")
        fig_lulucf.update_layout(
            height=440,
            margin=dict(l=0, r=50, t=10, b=10),
            xaxis_title="Net land-use CO₂ flux (Mt CO₂/yr)",
            yaxis_title="",
            transition_duration=400,
        )
        st.plotly_chart(fig_lulucf, use_container_width=True)
        st.caption(chart_caption)
 
# ============================================================
# FOOTER
# ============================================================
st.markdown("---")
st.caption(
    "📊 Built with Streamlit + Plotly · Data: EDGAR 2025 release · "
    "European Commission Joint Research Centre · "
)
