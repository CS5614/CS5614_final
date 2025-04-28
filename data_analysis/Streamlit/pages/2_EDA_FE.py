import streamlit.components.v1 as components

with open("../EDA/eda.html", 'r', encoding='utf-8') as f:
    html_content = f.read()
# Use st.components.v1.html to display the content
components.html(html_content, height=600, scrolling=True)  # Adjust height as needed