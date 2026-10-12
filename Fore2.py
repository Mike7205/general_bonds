import streamlit as st

st.set_page_config(layout="wide", page_title="Forecast Desktop", page_icon="🔮")

st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #a8d4e8; }
    details > summary { background-color: #85c1d9; color: #1a1a2e; border-radius: 6px; padding: 4px 8px; }
</style>
""", unsafe_allow_html=True)

pg = st.navigation([
    st.Page("pages/Forecast_Desktop.py", title="Forecast Desktop", icon="🔮"),
    st.Page("pages/Tech_Analytical_Desktop.py", title="Tech Analytical Desktop", icon="📊"),
    st.Page("pages/Bonds_Desktop.py", title="Obligacje Skarbowe", icon="🇵🇱"),
])
pg.run()
