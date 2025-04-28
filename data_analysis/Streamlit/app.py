import streamlit as st
import pandas as pd
import folium
import branca.colormap as cm
from streamlit_folium import st_folium
import numpy as np
import streamlit.components.v1 as components

# --- Page Configuration ---
st.set_page_config(layout="wide")

# --- Constants ---
DEFAULT_ZOOM = 9
SAMPLING_THRESHOLD = 5000
SAMPLING_SIZE = 2000

HEATMAP_FILES = {
    "# of Nearby Parks": "../EDA/heatmap_nearby_parks.html",
    "# of Nearby Bus Stops": "../EDA/heatmap_nearby_bus_stops.html"
}

# --- Data Loading ---
@st.cache_data
def load_main_data(path):
    df = pd.read_csv(path)
    df = df[["listing_db_id", "latitude", "longitude", "QoL_0_1"]]
    return df.dropna(subset=["latitude", "longitude", "QoL_0_1"])

# --- Map Builder ---
def create_qol_map(df, feature="QoL_0_1", zoom=DEFAULT_ZOOM):
    lat0, lon0 = df.latitude.mean(), df.longitude.mean()
    m = folium.Map(location=[lat0, lon0], zoom_start=zoom)

    plot_df = df.sample(n=SAMPLING_SIZE, random_state=42) if len(df) > SAMPLING_THRESHOLD else df
    plot_df = plot_df.dropna(subset=[feature])
    if plot_df.empty:
        return m

    vmin, vmax = plot_df[feature].min(), plot_df[feature].quantile(0.95)
    cmap = cm.linear.viridis.scale(vmin, vmax)
    cmap.caption = feature
    m.add_child(cmap)

    for _, row in plot_df.iterrows():
        val = row[feature]
        folium.CircleMarker(
            [row.latitude, row.longitude],
            radius=4,
            color=cmap(val),
            fill=True, fill_color=cmap(val), fill_opacity=0.7,
            popup=f"{feature}: {val:.3f}"
        ).add_to(m)
    return m

# --- App Start ---
st.title("Rental Listing Explorer")

# Load data once
df = load_main_data("../EDA/final_rental_listings_with_qol.csv")

# Sidebar
st.sidebar.header("View Options")
choice = st.sidebar.radio("Select view:", ["QoL Map", "Static Heatmaps"])

# Main
if df is None or df.empty:
    st.error("No data available.")
else:
    if choice == "QoL Map":
        st.header("Quality-of-Life Map")
        qol_map = create_qol_map(df)
        st_folium(qol_map, width=1000, height=600)

    elif choice == "Static Heatmaps":
        st.header("Pre-generated Static Heatmaps")
        selected = st.sidebar.selectbox("Which heatmap?", list(HEATMAP_FILES.keys()))
        path = HEATMAP_FILES[selected]
        try:
            html = open(path, "r", encoding="utf-8").read()
            components.html(html, height=600, scrolling=True)
        except FileNotFoundError:
            st.error(f"Heatmap file not found:\n{path}")
        except Exception as e:
            st.error(f"Error loading heatmap:\n{e}")