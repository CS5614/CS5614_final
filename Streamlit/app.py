import streamlit as st
import pandas as pd
import folium
import math
import branca.colormap as cm
from streamlit_folium import st_folium
import seaborn as sns
import matplotlib.colors as mpl_colors
import numpy as np
import scipy.spatial
import warnings
import streamlit.components.v1 as components # <-- Import components

# --- Page Configuration ---
st.set_page_config(layout="wide")

# --- Constants ---
# Center/Zoom for interactive maps
DEFAULT_MAP_CENTER_LAT = 38.9
DEFAULT_MAP_CENTER_LON = -77.0
DEFAULT_ZOOM_LEVEL = 9
SAMPLING_THRESHOLD = 5000
SAMPLING_SIZE = 2000
MIN_POINTS_FOR_HULL = 3
FEATURES_TO_PLOT = ["QoL_index", "nwi_score", "price", "aqi"]
BASE_REQUIRED_COLS = ["listing_db_id", "latitude", "longitude", "price", "aqi", "nwi_score", "QoL_index"]
CLUSTER_REQUIRED_COLS = ["listing_db_id", "cluster"]
# Define paths/names for your pre-generated HTML heatmaps
HEATMAP_FILES = {
    "# of Nearby Parks": "../EDA/heatmap_nearby_parks.html",
    "# of Nearby Bus Stops": "../EDA/heatmap_nearby_bus_stops.html",
    # "Distance of Nearest Bus Stop": "../EDA/nearest_bus_stop_heatmap.html",
    # "Distance of Nearest Park": "../EDA/nearest_park_heatmap.html",
    # Add more heatmap file paths/names here as needed
}


# --- Data Loading Functions (Unchanged) ---
@st.cache_data
def load_main_data(main_csv_path):
    # ... (previous function code) ...
    try:
        df = pd.read_csv(main_csv_path)
        if not all(col in df.columns for col in BASE_REQUIRED_COLS):
             missing_cols = [col for col in BASE_REQUIRED_COLS if col not in df.columns]
             st.error(f"Main data file '{main_csv_path}' missing required columns: {missing_cols}")
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
    # ... (previous function code) ...
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


# --- Map Generation Function for Features (Folium - Unchanged) ---
def create_feature_map(df, feature, center_lat, center_lon, zoom):
    # ... (previous function code) ...
    m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom)
    plot_df = df
    if len(df) > SAMPLING_THRESHOLD:
        plot_df = df.sample(n=SAMPLING_SIZE, random_state=42)

    plot_df = plot_df.replace([np.inf, -np.inf], np.nan).dropna(subset=[feature])
    if plot_df.empty:
         return m # Return empty map if no valid points

    min_val = plot_df[feature].min()
    max_val = plot_df[feature].quantile(0.95)
    mid_val = plot_df[feature].median()

    if feature == "QoL_index":
        colormap = cm.linear.viridis.scale(min_val, max_val) # Using Viridis now
        colormap.caption = f"Color based on {feature} (Higher is Yellower)"
    elif feature == "nwi_score":
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
        qol_val = row.get('QoL_index', 'N/A')
        cluster_val = int(row.get('cluster', -1))

        popup_text = f"<b>{feature}: {feat_val:.3f}</b><br>"
        if feature != 'QoL_index': popup_text += f"QoL Index: {qol_val:.3f}<br>"
        if feature != 'price': popup_text += f"Price: ${price_val:.0f}<br>"
        if feature != 'aqi': popup_text += f"AQI: {aqi_val}<br>"
        if feature != 'nwi_score': popup_text += f"NWI Score: {nwi_val:.2f}<br>" if isinstance(nwi_val, (int, float)) else ""
        popup_text += f"Cluster: {cluster_val}"

        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]], radius=4, popup=popup_text,
            color=colormap(feat_val) if pd.notna(feat_val) else 'grey', fill=True,
            fill_color=colormap(feat_val) if pd.notna(feat_val) else 'grey', fill_opacity=0.7
        ).add_to(m)
    return m

# --- Map Function for Focused Cluster View (Folium Dots + Opt Hull - Unchanged) ---
def create_cluster_focus_map(df, all_cluster_ids, selected_cluster_id, show_hull, center_lat, center_lon, zoom):
    # ... (previous function code) ...
    m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom)
    plot_df_full = df

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
            legend_html += f'<span style="color: {hex_color}">&#9679;</span> Cluster {cluster_id}<br>'

    is_showing_all = (selected_cluster_id == "Show All Clusters (Colored Dots)")
    plot_df_display = plot_df_full

    if not is_showing_all:
        plot_df_display = plot_df_full[plot_df_full['cluster'] == selected_cluster_id].copy()
        if plot_df_display.empty:
             return m
        selected_center_lat = plot_df_display['latitude'].mean()
        selected_center_lon = plot_df_display['longitude'].mean()
        m.location = [selected_center_lat, selected_center_lon]
        m.zoom_start = max(zoom, 13)

    if is_showing_all and len(plot_df_display) > SAMPLING_THRESHOLD:
        plot_df_display = plot_df_display.sample(n=SAMPLING_SIZE, random_state=42)

    for index, row in plot_df_display.iterrows():
        cluster_id = int(row["cluster"])
        point_color = color_dict.get(cluster_id, "#000000")
        radius_val = 3
        opacity_val = 0.7

        price_val = row.get('price', 0)
        aqi_val = row.get('aqi', 'N/A')
        nwi_val = row.get('nwi_score', 'N/A')
        qol_val = row.get('QoL_index', 'N/A')

        popup_text = f"Cluster: {cluster_id}<br>QoL Index: {qol_val:.3f}<br>Price: ${price_val:.0f}<br>NWI: {nwi_val:.2f}<br>AQI: {aqi_val}"

        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]], radius=radius_val, popup=popup_text,
            color=point_color, fill=True, fill_color=point_color, fill_opacity=opacity_val
        ).add_to(m)

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
                    locations=hull_coords, color=cluster_color, weight=2, fill=True,
                    fill_color=cluster_color, fill_opacity=0.2,
                    tooltip=f"Cluster {selected_cluster_id}<br>Points: {len(points)}"
                ).add_to(m)
            except (scipy.spatial.QhullError, Exception):
                 pass

    if num_total_clusters > 0:
        legend_div = folium.Element(f'<div style="position: fixed; bottom: 50px; left: 50px; width: 150px; height: auto; background-color: white; border:2px solid grey; z-index:9999; font-size:12px; overflow-y: auto; max-height: 150px;">{legend_html}</div>')
        m.get_root().html.add_child(legend_div)

    return m


# --- Streamlit App Layout ---
st.title("Rental Listing Explorer with QoL Index")

# --- Define File Paths ---
main_data_path = "../EDA/final_rental_listings_with_qol.csv"
cluster_data_path = "../HDBSCAN/final_clustering_results.csv" # UPDATE IF NEEDED

# --- Load and Merge Data ---
df_main_qol = load_main_data(main_data_path)
df_clusters = load_cluster_data(cluster_data_path)

# --- Initialize ---
data = None
has_cluster_data = False
all_cluster_ids = []
map_center_lat = 38.9 # Fallback Map Center
map_center_lon = -77.0
map_zoom = DEFAULT_ZOOM_LEVEL

# --- Process Loaded Data ---
if df_main_qol is not None:
    data = df_main_qol
    map_center_lat = data['latitude'].mean()
    map_center_lon = data['longitude'].mean()

    if df_clusters is not None:
        data = pd.merge(data, df_clusters, on="listing_db_id", how="left")
        data = data.dropna(subset=['cluster'])
        data['cluster'] = data['cluster'].astype(int)
        has_cluster_data = True
        all_cluster_ids = sorted(data['cluster'].unique())
    # --- No Geographic Filtering ---

# --- Sidebar Controls ---
st.sidebar.header("View Options")
map_type_options = ['Feature Map']
if has_cluster_data:
    map_type_options.append('Cluster Exploration')
# --- Add new option for static maps ---
map_type_options.append('Static Heatmaps')
# ---------------------------------------
map_type = st.sidebar.radio(
    "Select Map Type:",
    options=map_type_options
)

selected_feature = None
selected_cluster_id = None
show_hull_checkbox = False
selected_heatmap = None # Variable for heatmap selection

if map_type == 'Feature Map':
    selected_feature = st.sidebar.selectbox(
        "Select feature to visualize:", FEATURES_TO_PLOT, key='feature_select'
    )
elif map_type == 'Cluster Exploration':
    if has_cluster_data and all_cluster_ids:
        cluster_options = ["Show All Clusters (Colored Dots)"] + all_cluster_ids
        selected_cluster_id = st.sidebar.selectbox(
            "Select Cluster View:", options=cluster_options, key='cluster_select'
        )
        if selected_cluster_id != "Show All Clusters (Colored Dots)":
             show_hull_checkbox = st.sidebar.checkbox("Show Convex Hull", key='hull_check')
# --- Add Heatmap Selection ---
elif map_type == 'Static Heatmaps':
     selected_heatmap = st.sidebar.selectbox(
         "Select heatmap file to display:",
         options=list(HEATMAP_FILES.keys()), # Use keys from the dict defined earlier
         key='heatmap_select'
     )
# ---------------------------

# --- Main Panel Display Logic ---
if data is not None and not data.empty:

    st.header(f"{map_type} Visualization") # Dynamically update header

    if map_type == 'Feature Map' and selected_feature:
        feature_map = create_feature_map(data.copy(), selected_feature, map_center_lat, map_center_lon, map_zoom)
        st_folium(feature_map, key="feature_map", width=1000, height=600, returned_objects=[])

        # --- Display Formatted Data Table ---
        st.subheader("Total number of rental units: 12,795")
        st.subheader("Selected Listing Features")
        # Create a view copy to avoid modifying the main 'data'
        view = data.copy()
        # Define columns to display - Use correct, separate column names
        columns_to_display = [
            "listing_db_id", "latitude", "longitude", "price", "aqi",
            "nwi_score", "nearest_bus_stop_miles", "nearby_bus_stops",
            "nearby_parks",  # Corrected name
            "nearest_park_miles", # Corrected name
            "QoL_index"
        ]
        # Select only the columns that actually exist in the dataframe
        existing_columns_to_display = [col for col in columns_to_display if col in view.columns]
        view = view[existing_columns_to_display]

        # Rename columns for display - Use correct original names as keys
        view = view.rename(columns={
            "listing_db_id": "Listing ID",
            "latitude": "Latitude",
            "longitude": "Longitude",
            "price": "Price ($)",
            "aqi": "Air Quality Index",
            "nwi_score": "National Walkability Index",
            "nearest_bus_stop_miles": "Nearest Bus Stop (Miles)",
            "nearby_bus_stops": "# Nearby Bus Stops",
            "nearby_parks": "# Nearby Parks", # Corrected name
            "nearest_park_miles": "Nearest Park (Miles)", # Corrected name
            "QoL_index": "Quality of Life Index"
        })
        # Actually display the dataframe
        st.dataframe(view)

    elif map_type == 'Cluster Exploration' and has_cluster_data:
        if selected_cluster_id is not None:
            cluster_map = create_cluster_focus_map(data.copy(), all_cluster_ids, selected_cluster_id, show_hull_checkbox, map_center_lat, map_center_lon, map_zoom)
            st_folium(cluster_map, key="cluster_focus_map", width=1000, height=600, returned_objects=[])

            st.subheader("Cluster Statistics (Total number of clusters: 1,329)")
            if 'cluster' in data.columns:
                 agg_dict = {
                     'count': ('cluster', 'size'), 'avg_price': ('price', 'mean'),
                     'avg_aqi': ('aqi', 'mean'), 'avg_nwi': ('nwi_score', 'mean'),
                     'avg_QoL': ('QoL_index', 'mean')
                 }
                 valid_agg_cols = {k: v for k, v in agg_dict.items() if v[0] in data.columns}
                 if valid_agg_cols:
                     cluster_stats = data.groupby('cluster').agg(**valid_agg_cols).reset_index().round(3)
                     st.dataframe(cluster_stats)

    # --- Add Logic to Display Static HTML Heatmap ---
    elif map_type == 'Static Heatmaps' and selected_heatmap:
         heatmap_file_path = HEATMAP_FILES.get(selected_heatmap)
         if heatmap_file_path:
             try:
                 with open(heatmap_file_path, 'r', encoding='utf-8') as f:
                     html_content = f.read()
                 # Use st.components.v1.html to display the content
                 components.html(html_content, height=600, scrolling=True) # Adjust height as needed
             except FileNotFoundError:
                  st.error(f"Heatmap file not found: {heatmap_file_path}")
             except Exception as e:
                  st.error(f"Error reading or displaying heatmap file: {e}")
    # ----------------------------------------------

    elif map_type == 'Cluster Exploration' and not has_cluster_data:
         pass # Radio button should be disabled

# Handle cases where data loading failed or resulted in empty dataframe
elif df_main_qol is None:
    pass # Error already shown
else:
    st.error("No data available to display (check file paths and content).")