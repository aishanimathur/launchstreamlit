import streamlit as st
import geopandas as gpd
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(layout="wide")
st.title("Chicago Housing Distress Dashboard (2024)")

# -----------------------------
# CACHED LOADERS
# -----------------------------
@st.cache_data
def load_wards_geo():
    gdf = gpd.read_file("wards_2023_final_dashboard.geojson")
    gdf = gdf.to_crs(epsg=4326)
    gdf["ward"] = gdf["ward"].astype(int)
    return gdf


@st.cache_data
def load_vacant_csv():
    vacant = pd.read_csv("vacant_minimal.csv")
    vacant["ward_spatial"] = vacant["ward_spatial"].astype(int)
    return vacant
vacant = load_vacant_csv()

@st.cache_data
def load_foreclosures_timeseries():
    foreclosures = pd.read_csv(
        "https://raw.githubusercontent.com/aaryal22/final_project_dataviz_group2/main/dataset/raw/foreclosures_chicago_wards_clean.csv"
    )
    foreclosures["ward"] = (
        foreclosures["Geography"].str.replace("Ward ", "", regex=False).astype(int)
    )

    year_cols = [c for c in foreclosures.columns if c.isdigit()]

    long = foreclosures.melt(
        id_vars=["ward"],
        value_vars=year_cols,
        var_name="year",
        value_name="foreclosures"
    )

    long["year"] = long["year"].astype(int)
    return long

# -----------------------------
# LOAD DATA
# -----------------------------
gdf = load_wards_geo()
vacant = load_vacant_csv()
ts = load_foreclosures_timeseries()

# Rename for consistency
gdf = gdf.rename(columns={
    "foreclosure_rate_2024": "Foreclosures (2024)",
    "vacant_count": "Vacant parcels",
    "housing_distress_index": "Housing Distress Index"
})

# -----------------------------
# SIDEBAR CONTROLS
# -----------------------------
st.sidebar.header("Controls")

ward_list = sorted(gdf["ward"].unique())

selected_ward = st.sidebar.selectbox(
    "Select a Ward",
    options=["Citywide"] + ward_list,
    index=0
)

map_metric = st.sidebar.radio(
    "Choropleth metric",
    options=[
        "Foreclosures (2024)",
        "Vacant parcels",
        "Housing Distress Index",
        "Risk tier"
    ],
    index=0
)

zoom_mode = st.sidebar.radio(
    "View",
    options=["Citywide", "Selected ward"],
    index=0
)

show_parcels = st.sidebar.checkbox("Show vacant parcel dots", value=True)

# -----------------------------
# MAP
# -----------------------------

hover_cols = [
    "ward",
    "Foreclosures (2024)",
    "Vacant parcels",
    "Housing Distress Index",
    "risk_tier"
]

if map_metric == "Risk tier":

    fig = px.choropleth_mapbox(
        gdf,
        geojson=gdf.__geo_interface__,
        locations="ward",
        featureidkey="properties.ward",
        color="risk_tier",
        mapbox_style="carto-positron",
        opacity=0.8,
        hover_data=hover_cols,
        color_discrete_map={
            "Low": "#2ecc71",
            "Watch": "#f1c40f",
            "Critical": "#e74c3c"
        }
    )

else:

    fig = px.choropleth_mapbox(
        gdf,
        geojson=gdf.__geo_interface__,
        locations="ward",
        featureidkey="properties.ward",
        color=map_metric,
        mapbox_style="carto-positron",
        opacity=0.75,
        hover_data=hover_cols,
        color_continuous_scale=(
            "Reds" if map_metric == "Foreclosures (2024)"
            else "Blues" if map_metric == "Vacant parcels"
            else "Purples"
        )
    )

fig.update_layout(
    mapbox=dict(center=dict(lat=41.85, lon=-87.68), zoom=9.4),
    margin={"r": 0, "t": 0, "l": 0, "b": 0}
)

# -----------------------------
# WARD DETAILS
# -----------------------------
if selected_ward != "Citywide":

    ward_row = gdf[gdf["ward"] == selected_ward].iloc[0]

    st.subheader(f"Ward {selected_ward}")

    st.write(
        "Foreclosures (2024):",
        f"{ward_row['Foreclosures (2024)']:.2f}%"
    )

    st.write("Vacant parcels:", int(ward_row["Vacant parcels"]))

    st.write(
        "Housing Distress Index:",
        f"{ward_row['Housing Distress Index']:.3f}"
    )

    st.write("Risk tier:", ward_row["risk_tier"])

    if show_parcels:
        filtered = vacant[vacant["ward_spatial"] == selected_ward]

        fig.add_trace(
            go.Scattermapbox(
                lat=filtered["latitude"],
                lon=filtered["longitude"],
                mode="markers",
                marker=dict(size=4, color="blue", opacity=0.6),
                name="Vacant parcels"
            )
        )

    if zoom_mode == "Selected ward":
        ward_shape = gdf[gdf["ward"] == selected_ward]
        center = ward_shape.geometry.centroid.iloc[0]
        fig.update_layout(
            mapbox=dict(center=dict(lat=center.y, lon=center.x), zoom=11.5)
        )

st.plotly_chart(fig, width="stretch")

# -----------------------------
# LINE GRAPH (ONLY FORECLOSURE MODE)
# -----------------------------
if map_metric == "Foreclosures (2024)" and selected_ward != "Citywide":

    st.subheader("Foreclosures over time")

    ts_ward = ts[ts["ward"] == selected_ward].sort_values("year")

    fig_line = px.line(
        ts_ward,
        x="year",
        y="foreclosures",
        markers=True,
        hover_data=["year", "foreclosures"],
        title=f"Ward {selected_ward}: Foreclosures by Year"
    )

    fig_line.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 0})

    st.plotly_chart(fig_line, width="stretch")
