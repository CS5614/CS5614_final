import streamlit as st
import pandas as pd
import folium
import math
import branca.colormap as cm
from streamlit_folium import st_folium
import seaborn as sns
import matplotlib.colors as mpl_colors
import numpy as np
import scipy.spatial # For hulls if using that option (kept for focus map)
import warnings # To suppress hull warnings if using that option

# --- Page Configuration ---
st.set_page_config(layout="wide")

# --- Constants ---
# Center/Zoom calculated dynamically
DEFAULT_ZOOM_LEVEL = 9
SAMPLING_THRESHOLD = 5000
SAMPLING_SIZE = 2000
MIN_POINTS_FOR_HULL = 3
# Add 'QoL_index' to features
FEATURES_TO_PLOT = ["QoL_index", "nwi_score", "price", "aqi"]
# Update base required columns to reflect the new main file
BASE_REQUIRED_COLS = ["listing_db_id", "latitude", "longitude", "price", "aqi", "nwi_score", "QoL_index"] # Add QoL_index
CLUSTER_REQUIRED_COLS = ["listing_db_id", "cluster"]

# --- Data Loading Functions ---
@st.cache_data
def load_main_data(main_csv_path):
    """Loads the main dataset (now with QoL scores)."""
    try:
        df = pd.read_csv(main_csv_path)
        # Check for base columns including QoL_index now
        if not all(col in df.columns for col in BASE_REQUIRED_COLS):
             # Check which ones are missing
             missing_cols = [col for col in BASE_REQUIRED_COLS if col not in df.columns]
             st.error(f"Main data file '{main_csv_path}' missing required columns: {missing_cols}")
             return None
        df_out = df[BASE_REQUIRED_COLS].copy() # Keep only necessary columns
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

# --- Map Generation Function for Features ---
def create_feature_map(df, feature, center_lat, center_lon, zoom):
    """Creates an INTERACTIVE Folium map with points colored by feature."""
    m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom)
    plot_df = df
    if len(df) > SAMPLING_THRESHOLD:
        plot_df = df.sample(n=SAMPLING_SIZE, random_state=42)

    # Add handling for potential NaN/inf in feature column before min/max/median
    plot_df = plot_df.replace([np.inf, -np.inf], np.nan).dropna(subset=[feature])
    if plot_df.empty:
         st.warning(f"No valid data points found for feature '{feature}' after cleaning.")
         return m # Return empty map if no valid points for this feature

    min_val = plot_df[feature].min()
    max_val = plot_df[feature].quantile(0.95) # Use quantile for robustness
    mid_val = plot_df[feature].median()

    # --- Define Colormaps ---
    if feature == "QoL_index":
        colormap = cm.linear.viridis.scale(min_val, max_val)
        colormap.caption = f"Color based on {feature} (Higher is Better)"
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
        colormap = cm.linear.YlGnBu_09 # Default sequential
        colormap.caption = f"Color based on {feature}"
    m.add_child(colormap)

    # --- Add Points ---
    for index, row in plot_df.iterrows():
        feat_val = row.get(feature, np.nan)
        # Get other values for popup, checking if they exist
        price_val = row.get('price', 0)
        aqi_val = row.get('aqi', 'N/A')
        nwi_val = row.get('nwi_score', 'N/A')
        qol_val = row.get('QoL_index', 'N/A') # Get QoL score
        cluster_val = int(row.get('cluster', -1))

        # Create popup, including QoL score
        popup_text = f"<b>{feature}: {feat_val:.3f}</b><br>" # Highlight selected feature
        if feature != 'QoL_index': popup_text += f"QoL Index: {qol_val:.3f}<br>"
        if feature != 'price': popup_text += f"Price: ${price_val:.0f}<br>"
        if feature != 'aqi': popup_text += f"AQI: {aqi_val}<br>"
        if feature != 'nwi_score': popup_text += f"NWI Score: {nwi_val:.2f}<br>" if isinstance(nwi_val, (int, float)) else ""
        popup_text += f"Cluster: {cluster_val}"

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
def create_cluster_focus_map(df, all_cluster_ids, selected_cluster_id, show_hull, center_lat, center_lon, zoom):
    """Creates an INTERACTIVE Folium map focusing on a selected cluster or all clusters."""
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
        qol_val = row.get('QoL_index', 'N/A') # Get QoL score for popup

        popup_text = f"Cluster: {cluster_id}<br>QoL Index: {qol_val:.3f}<br>Price: ${price_val:.0f}<br>NWI: {nwi_val:.2f}<br>AQI: {aqi_val}"

        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=radius_val,
            popup=popup_text,
            color=point_color,
            fill=True,
            fill_color=point_color,
            fill_opacity=opacity_val
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
                 pass # Silently skip hull

    if num_total_clusters > 0:
        legend_div = folium.Element(f'<div style="position: fixed; bottom: 50px; left: 50px; width: 150px; height: auto; background-color: white; border:2px solid grey; z-index:9999; font-size:12px; overflow-y: auto; max-height: 150px;">{legend_html}</div>')
        m.get_root().html.add_child(legend_div)

    return m


# --- Streamlit App Layout ---
st.title("Rental Listing Explorer with QoL Index")

# --- Define File Paths ---
# !!! IMPORTANT: Update these paths if needed !!!
main_data_path = "../EDA/final_rental_listings_with_qol.csv"
cluster_data_path = "../HDBSCAN/final_clustering_results.csv"

# --- Load and Merge Data ---
df_main_qol = load_main_data(main_data_path)
df_clusters = load_cluster_data(cluster_data_path)

# --- Initialize Variables ---
data = None
has_cluster_data = False
all_cluster_ids = []
map_center_lat = 38.9 # Fallback Map Center (Approx DC)
map_center_lon = -77.0
map_zoom = DEFAULT_ZOOM_LEVEL

# --- Process Loaded Data ---
if df_main_qol is not None:
    data = df_main_qol # Start with main QoL data
    map_center_lat = data['latitude'].mean()
    map_center_lon = data['longitude'].mean()

    if df_clusters is not None:
        # Merge cluster data into the main QoL dataframe
        data = pd.merge(data, df_clusters, on="listing_db_id", how="left")
        # Handle potential missing matches if needed (e.g., fillna or dropna)
        data = data.dropna(subset=['cluster']) # Drop listings not found in cluster results
        data['cluster'] = data['cluster'].astype(int)
        has_cluster_data = True
        # Get unique cluster IDs from the final merged dataframe
        all_cluster_ids = sorted(data['cluster'].unique())
    # else: No cluster data loaded, 'data' remains df_main_qol without cluster info

    # --- NO Geographic Filtering Applied ---

# --- App Display ---
if data is not None and not data.empty:
    # --- Sidebar Controls ---
    st.sidebar.header("View Options")
    map_type_options = ['Feature Map (Interactive)']
    if has_cluster_data:
        map_type_options.append('Cluster Exploration (Interactive)')
    map_type = st.sidebar.radio(
        "Select Map Type:",
        options=map_type_options
    )

    selected_feature = None
    selected_cluster_id = None
    show_hull_checkbox = False

    if map_type == 'Feature Map (Interactive)':
        # Use the updated FEATURES_TO_PLOT list which includes 'QoL_index'
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

    # --- Main Panel Display Logic ---
    st.header(f"{map_type} Visualization")

    if map_type == 'Feature Map (Interactive)' and selected_feature:
        feature_map = create_feature_map(data.copy(), selected_feature, map_center_lat, map_center_lon, map_zoom)
        st_folium(feature_map, key="feature_map", width=1000, height=600, returned_objects=[])

    elif map_type == 'Cluster Exploration (Interactive)' and has_cluster_data:
        if selected_cluster_id is not None:
            cluster_map = create_cluster_focus_map(data.copy(), all_cluster_ids, selected_cluster_id, show_hull_checkbox, map_center_lat, map_center_lon, map_zoom)
            st_folium(cluster_map, key="cluster_focus_map", width=1000, height=600, returned_objects=[])

            # Cluster Statistics (Show all clusters found in data, now include avg QoL)
            st.subheader("Cluster Statistics")
            if 'cluster' in data.columns:
                 agg_dict = {
                     'count': ('cluster', 'size'),
                     'avg_price': ('price', 'mean'),
                     'avg_aqi': ('aqi', 'mean'),
                     'avg_nwi': ('nwi_score', 'mean'),
                     'avg_QoL': ('QoL_index', 'mean') # Add QoL average
                 }
                 # Filter out potential missing columns before aggregation if necessary
                 valid_agg_cols = {k: v for k, v in agg_dict.items() if v[0] in data.columns}
                 if valid_agg_cols:
                     cluster_stats = data.groupby('cluster').agg(**valid_agg_cols).reset_index().round(3) # Round QoL nicely
                     st.dataframe(cluster_stats)
                 else:
                     st.write("Required columns for statistics calculation are missing.")

    elif map_type == 'Cluster Exploration (Interactive)' and not has_cluster_data:
         pass # Radio button should be disabled

# Handle cases where data loading failed or resulted in empty dataframe
elif df_main_qol is None:
    pass # Error already shown
else:
    st.error("No data available to display (check file paths and content).")