import streamlit as st

# --- Define Workflow Steps ---
# Each item in the list is a dictionary representing one "slide"
workflow_steps = [
    {
        "title": "Project Goal",
        "content": """
        ### This project aims to estimate the **Quality of Life (QoL)** in the **Washington D.C. Metro Area**, with a focus on housing-related challenges often faced by residents, especially international students.
        """
    },
    {
        "title": "Step 1: Data Acquisition and Integration",
        "content": """
        ### We gathered data from multiple sources:
        #### 1. Rental Listings: Prices and locations (RentCast).
        #### 2. Public Transit: Accessibility information (WMATA).
        #### 3. Air Quality: Air Pollution Index data (OpenWeatherMap API).
        #### 4. Walkability: Scores (EPA National Walkability Index).
        #### 5. Green Space & Amenities: Parks, etc. (OpenStreetMap).
        """
    },
    {
        "title": "Step 2: Geographic Clustering (HDBSCAN)",
        "content": """
        ### To better analyze spatially varying factors like Air Quality, we applied the **HDBSCAN** clustering algorithm.
        #### This grouped rental listings based on their geographic proximity (latitude/longitude).
        #### It helped identify distinct neighborhoods or areas for localized analysis.
        """
    },
    {
        "title": "Step 3: QoL Index Calculation (PCA)",
        "content": """
        ### To combine the different indicators into a single QoL score objectively, we used **Principal Component Analysis (PCA)**:
        #### PCA analyzes correlations between indicators (price, transit, AQI, walkability, green space).
        #### It determines data-driven weights for each indicator based on the variance they explain.
        #### This avoids subjective weighting and provides a statistically grounded score.
        #### The final `QoL_index` represents the composite score.
        """
    },
    {
        "title": "Step 4: Visualization",
        "content": """
        ### This Streamlit application serves as a demonstration platform to:
        #### Explore raw features (Price, AQI, Walkability, QoL Index) on an interactive map.
        #### Visualize the geographic clusters identified by HDBSCAN interactively.
        #### Analyze statistics aggregated by cluster.
        """
    }
]
TOTAL_STEPS = len(workflow_steps)

# --- Initialize Session State ---
if 'workflow_step' not in st.session_state:
    st.session_state.workflow_step = 0

# --- Helper Functions for Navigation ---
def next_step():
    st.session_state.workflow_step += 1
    # No rerun needed here, button click handles it implicitly usually,
    # but add if state doesn't update visually on first click
    # st.rerun()

def prev_step():
    st.session_state.workflow_step -= 1
    # No rerun needed here usually
    # st.rerun()


# --- Page Layout ---
st.title("Project Workflow")

# Get current step number
current_step = st.session_state.workflow_step

# Display the content for the current step
st.header(f"({current_step + 1}/{TOTAL_STEPS}) {workflow_steps[current_step]['title']}")
st.markdown(workflow_steps[current_step]['content'])

st.write("---") # Separator

# --- Navigation Buttons ---
col1, col2, col3 = st.columns([1, 1, 1]) # Adjust column ratios if needed

with col1:
    st.button(
        "Previous Step",
        on_click=prev_step,
        disabled=(current_step <= 0), # Disable if on first step
        use_container_width=True
    )

with col3:
    st.button(
        "Next Step",
        on_click=next_step,
        disabled=(current_step >= TOTAL_STEPS - 1), # Disable if on last step
        use_container_width=True
    )

# Optional: Add a progress bar
progress_percentage = (current_step + 1) / TOTAL_STEPS
st.progress(progress_percentage)