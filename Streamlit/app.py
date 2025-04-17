import streamlit as st
import pandas as pd
import folium
import math
import branca.colormap as cm
from streamlit_folium import st_folium
# Imports for the static plot
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
import contextily as ctx # For basemaps
import numpy as np
import matplotlib.colors as mpl_colors
# Imports needed for cluster map logic
import scipy.spatial # For hulls if using that option (kept for focus map)
import warnings # To suppress hull warnings if using that option

# --- Page Configuration ---
st.set_page_config(layout="wide")

# --- Constants ---
# Default Map Zoom (Center is calculated dynamically)
DEFAULT_ZOOM_LEVEL = 9 # Start more zoomed out for wider area view
SAMPLING_THRESHOLD = 5000 # Number of points above which sampling is applied
SAMPLING_SIZE = 2000      # Number of points to sample
MIN_POINTS_FOR_HULL = 3 # Min points needed to attempt drawing a hull (for focus map)
# Features for the feature map dropdown
FEATURES_TO_PLOT = ["nwi_score", "price", "aqi"]
# Columns needed from the main data file
BASE_REQUIRED_COLS = ["listing_db_id", "latitude", "longitude", "price", "aqi", "nwi_score"]
# Columns needed from the cluster file
CLUSTER_REQUIRED_COLS = ["listing_db_id", "cluster"]

# --- Data Loading Functions ---
@st.cache_data
def load_main_data(main_csv_path):
    """Loads the main dataset."""
    try:
        df = pd.read_csv(main_csv_path)
        if not all(col in df.columns for col in BASE_REQUIRED_COLS):
             st.error(f"Main data file '{main_csv_path}' missing required columns. Need: {BASE_REQUIRED_COLS}")
             return None
        df_out = df[BASE_REQUIRED_COLS].copy()
        df_out = df_out.dropna(subset=["latitude", "longitude"])
        return df_out
    except FileNotFoundError:
        st.error(f"Main data file '{main_csv_path}' not found.")
        return None
    except Exception as e:
        st.error(f"Error loading main data: {e}")
        return None

@st.cache_data
def load_cluster_data(cluster_csv_path):
    """Loads the cluster results CSV."""
    try:
        df = pd.read_csv(cluster_csv_path)
        if not all(col in df.columns for col in CLUSTER_REQUIRED_COLS):
             st.error(f"Cluster data file '{cluster_csv_path}' missing required columns: {CLUSTER_REQUIRED_COLS}")
             return None
        return df[CLUSTER_REQUIRED_COLS]
    except FileNotFoundError:
        st.error(f"Cluster data file '{cluster_csv_path}' not found.")
        return None
    except Exception as e:
        st.error(f"Error loading cluster data: {e}")
        return None

# --- Map Generation Function for Features (Folium) ---
def create_feature_map(df, feature, center_lat, center_lon, zoom):
    """Creates an INTERACTIVE Folium map with points colored by feature."""
    m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom)
    plot_df = df
    if len(df) > SAMPLING_THRESHOLD:
        plot_df = df.sample(n=SAMPLING_SIZE, random_state=42)

    min_val = plot_df[feature].min()
    max_val = plot_df[feature].quantile(0.95)
    mid_val = plot_df[feature].median()

    if feature == "nwi_score":
        colormap = cm.LinearColormap(["blue", "yellow", "green"], index=[min_val, mid_val, max_val], vmin=min_val, vmax=max_val)
        colormap.caption = f"Color based on {feature} (Higher is Better)"
    elif feature == "price":
        colormap = cm.LinearColormap(["yellow", "orange", "red"], index=[min_val, mid_val, max_val], vmin=min_val, vmax=max_val)
        colormap.caption = f"Color based on {feature} (Higher Price = Redder)"
    elif feature == "aqi":
        colormap = cm.LinearColormap(["green", "yellow", "red"], index=[min_val, mid_val, max_val], vmin=min_val, vmax=max_val)
        colormap.caption = f"Color based on {feature} (Lower AQI is Better)"
    else:
        colormap = cm.linear.YlGnBu_09
        colormap.caption = f"Color based on {feature}"
    m.add_child(colormap)

    for index, row in plot_df.iterrows():
        feat_val = row.get(feature, np.nan)
        price_val = row.get('price', 0)
        aqi_val = row.get('aqi', 'N/A')
        nwi_val = row.get('nwi_score', 'N/A')
        cluster_val = int(row.get('cluster', -1)) # Default cluster to -1 if missing

        popup_text = f"{feature}: {feat_val:.2f}<br>Price: ${price_val:.0f}"
        if feature != 'aqi': popup_text += f"<br>AQI: {aqi_val}"
        if feature != 'nwi_score': popup_text += f"<br>NWI Score: {nwi_val:.2f}" if isinstance(nwi_val, (int, float)) else nwi_val
        popup_text += f"<br>Cluster: {cluster_val}"

        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=4,
            popup=popup_text,
            color=colormap(feat_val) if pd.notna(feat_val) else 'grey',
            fill=True,
            fill_color=colormap(feat_val) if pd.notna(feat_val) else 'grey',
            fill_opacity=0.7
        ).add_to(m)
    return m

# --- Map Function for Focused Cluster View (Folium Dots + Opt Hull) ---
# Using Folium for this as well for consistency and interactivity,
# replacing the static plot function.
def create_cluster_focus_map(df, all_cluster_ids, selected_cluster_id, show_hull, center_lat, center_lon, zoom):
    """Creates an INTERACTIVE Folium map focusing on a selected cluster or all clusters."""
    m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom)
    plot_df_full = df # Use the full, filtered data passed in

    # --- Setup Colors and Legend for ALL potential clusters ---
    num_total_clusters = len(all_cluster_ids)
    color_dict = {}
    legend_html = "<b>Cluster Legend:</b><br>"
    if num_total_clusters > 0:
        if num_total_clusters <= 10: palette = sns.color_palette("tab10", n_colors=num_total_clusters)
        elif num_total_clusters <= 20: palette = sns.color_palette("tab20", n_colors=num_total_clusters)
        else: palette = sns.color_palette("husl", n_colors=num_total_clusters)

        for i, cluster_id in enumerate(all_cluster_ids):
            rgb_color = palette[i % len(palette)]
            hex_color = mpl_colors.to_hex(rgb_color)
            color_dict[cluster_id] = hex_color
            # Use circle symbol in legend now
            legend_html += f'<span style="color: {hex_color}">&#9679;</span> Cluster {cluster_id}<br>'

    # --- Filter Data Based on Selection ---
    is_showing_all = (selected_cluster_id == "Show All Clusters (Colored Dots)")
    plot_df_display = plot_df_full # Default to display all

    if not is_showing_all:
        # Filter to the specific cluster selected
        plot_df_display = plot_df_full[plot_df_full['cluster'] == selected_cluster_id].copy()
        if plot_df_display.empty:
             st.warning(f"No data points found for selected cluster {selected_cluster_id}.")
             return m # Return empty map
        # Recenter map on selected cluster's centroid
        selected_center_lat = plot_df_display['latitude'].mean()
        selected_center_lon = plot_df_display['longitude'].mean()
        m.location = [selected_center_lat, selected_center_lon]
        m.zoom_start = max(zoom, 13) # Zoom in a bit more when focused


    # --- Apply Sampling only if showing all clusters ---
    if is_showing_all and len(plot_df_display) > SAMPLING_THRESHOLD:
        plot_df_display = plot_df_display.sample(n=SAMPLING_SIZE, random_state=42)


    # --- Add Points to Map ---
    for index, row in plot_df_display.iterrows():
        cluster_id = int(row["cluster"])
        point_color = color_dict.get(cluster_id, "#000000")
        radius_val = 3
        opacity_val = 0.7

        price_val = row.get('price', 0)
        aqi_val = row.get('aqi', 'N/A')
        nwi_val = row.get('nwi_score', 'N/A')

        popup_text = f"Cluster: {cluster_id}<br>Price: ${price_val:.0f}<br>NWI: {nwi_val:.2f}<br>AQI: {aqi_val}"

        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=radius_val,
            popup=popup_text,
            color=point_color, # Outline color
            fill=True,
            fill_color=point_color, # Fill color
            fill_opacity=opacity_val
        ).add_to(m)

    # --- Add Optional Hull for SELECTED Cluster ---
    if show_hull and not is_showing_all:
        points = plot_df_display[['latitude', 'longitude']].values
        if len(points) >= MIN_POINTS_FOR_HULL:
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    hull = scipy.spatial.ConvexHull(points)
                hull_points = points[hull.vertices]
                hull_coords = hull_points.tolist()
                cluster_color = color_dict.get(selected_cluster_id, "#000000")

                folium.Polygon(
                    locations=hull_coords,
                    color=cluster_color,
                    weight=2,
                    fill=True,
                    fill_color=cluster_color,
                    fill_opacity=0.2,
                    tooltip=f"Cluster {selected_cluster_id}<br>Points: {len(points)}"
                ).add_to(m)
            except (scipy.spatial.QhullError, Exception):
                 pass # Silently skip hull if error occurs


    # --- Add Legend ---
    if num_total_clusters > 0:
        legend_div = folium.Element(f'<div style="position: fixed; bottom: 50px; left: 50px; width: 150px; height: auto; background-color: white; border:2px solid grey; z-index:9999; font-size:12px; overflow-y: auto; max-height: 150px;">{legend_html}</div>')
        m.get_root().html.add_child(legend_div)

    return m


# --- Streamlit App Layout ---
st.title("Rental Listing Explorer (Full Dataset)")

# --- Define File Paths ---
main_data_path = "temp.csv"
# !!! IMPORTANT: Change this to the actual path/filename for your cluster results !!!
cluster_data_path = "../HDBSCAN/final_clustering_results.csv"

# --- Load Data ---
df_main = load_main_data(main_data_path)
df_clusters = load_cluster_data(cluster_data_path)

# --- Initialize Variables ---
data = None
has_cluster_data = False
all_cluster_ids = []
map_center_lat = 38.9 # Fallback Map Center (Approx DC)
map_center_lon = -77.0
map_zoom = DEFAULT_ZOOM_LEVEL

# --- Process Loaded Data ---
if df_main is not None:
    data = df_main
    map_center_lat = df_main['latitude'].mean()
    map_center_lon = df_main['longitude'].mean()

    if df_clusters is not None:
        data = pd.merge(df_main, df_clusters, on="listing_db_id", how="left")
        # Drop rows where cluster info didn't merge (optional, assumes cluster file covers all main listings)
        data = data.dropna(subset=['cluster'])
        data['cluster'] = data['cluster'].astype(int) # Ensure integer type
        has_cluster_data = True
        # Get unique cluster IDs from the final 'data' dataframe
        all_cluster_ids = sorted(data['cluster'].unique())
    # else: No cluster data loaded, 'data' remains df_main

    # --- NO Geographic Filtering Applied ---

# --- App Display ---
if data is not None and not data.empty:
    # --- Sidebar Controls ---
    st.sidebar.header("View Options")
    map_type_options = ['Feature Map (Interactive)']
    if has_cluster_data:
        map_type_options.append('Cluster Exploration (Interactive)') # Changed label
    map_type = st.sidebar.radio(
        "Select Map Type:",
        options=map_type_options
    )

    selected_feature = None
    selected_cluster_id = None
    show_hull_checkbox = False

    if map_type == 'Feature Map (Interactive)':
        selected_feature = st.sidebar.selectbox(
            "Select feature to visualize:",
            FEATURES_TO_PLOT,
            key='feature_select'
        )
    elif map_type == 'Cluster Exploration (Interactive)':
        if has_cluster_data and all_cluster_ids:
            cluster_options = ["Show All Clusters (Colored Dots)"] + all_cluster_ids # Sorted IDs already
            selected_cluster_id = st.sidebar.selectbox(
                "Select Cluster View:",
                options=cluster_options,
                key='cluster_select'
            )
            if selected_cluster_id != "Show All Clusters (Colored Dots)":
                 show_hull_checkbox = st.sidebar.checkbox("Show Convex Hull for Selected Cluster", key='hull_check')
        # else: No clusters to select

    # Optional: Display sample in sidebar
    # st.sidebar.header("Data Sample")
    # st.sidebar.dataframe(data.head())

    # --- Main Panel Display Logic ---
    st.header(f"{map_type} Visualization") # Dynamically update header

    if map_type == 'Feature Map (Interactive)' and selected_feature:
        feature_map = create_feature_map(data.copy(), selected_feature, map_center_lat, map_center_lon, map_zoom)
        st_folium(feature_map, key="feature_map", width=1000, height=600, returned_objects=[])

    elif map_type == 'Cluster Exploration (Interactive)' and has_cluster_data:
        if selected_cluster_id is not None:
            cluster_map = create_cluster_focus_map(data.copy(), all_cluster_ids, selected_cluster_id, show_hull_checkbox, map_center_lat, map_center_lon, map_zoom)
            st_folium(cluster_map, key="cluster_focus_map", width=1000, height=600, returned_objects=[])

            # Cluster Statistics (Show all clusters found in data)
            st.subheader("Cluster Statistics")
            if 'cluster' in data.columns:
                 cluster_stats = data.groupby('cluster').agg(
                     count=('cluster', 'size'),
                     avg_price=('price', 'mean'),
                     avg_aqi=('aqi', 'mean'),
                     avg_nwi=('nwi_score', 'mean')
                 ).reset_index().round(2)
                 st.dataframe(cluster_stats)

    elif map_type == 'Cluster Exploration (Interactive)' and not has_cluster_data:
         pass # Should be disabled, but do nothing if somehow selected

# Handle cases where data loading failed or resulted in empty dataframe
elif df_main is None:
    # Error message was already shown by loading function
    pass
else: # Data is None or became empty after potential processing steps
    st.error("No data available to display (check file paths and content).")