import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="SOC Management Map – Kano + Kaduna", page_icon="🌱", layout="wide")

# ----------------------------- LOAD DATA (ONCE) -----------------------------
@st.cache_data
def load_data():
    df = pd.read_csv('Kano_Kaduna_Environmental_Covariates_2018_2024 (1).csv')
    return df.dropna(subset=['Long', 'Lat', 'SOC']).copy()

df = load_data()

# ----------------------------- CLASSIFICATION (YOUR THRESHOLDS) -----------------------------
def get_soc_zone(soc_value):
    if soc_value < 0.5:
        return {
            'zone': 'Severely Degraded / Low Carbon',
            'color': '#d73027',      # red
            'recommendation': (
                "🔴 <b>Immediate intervention required:</b><br>"
                "- Implement conservation agriculture (no‑till, cover crops, residue retention).<br>"
                "- Apply compost or manure at 5‑10 t/ha.<br>"
                "- Establish agroforestry (nitrogen‑fixing trees).<br>"
                "- Priority for carbon credit funding."
            )
        }
    elif soc_value < 1.2:
        return {
            'zone': 'Medium Carbon',
            'color': '#fc8d59',      # orange
            'recommendation': (
                "🟠 <b>Maintenance & Restoration:</b><br>"
                "- Adopt cover cropping and crop rotation with legumes.<br>"
                "- Reduce tillage intensity and retain crop residues.<br>"
                "- Apply biochar or compost to boost SOC.<br>"
                "- Monitor SOC every 2-3 years."
            )
        }
    else:
        return {
            'zone': 'High Carbon',
            'color': '#1a9850',      # green
            'recommendation': (
                "🌲 <b>Protection & Incentives:</b><br>"
                "- No land‑use conversion. Protect from erosion.<br>"
                "- Eligible for Payment for Ecosystem Services (PES).<br>"
                "- Establish as reference site.<br>"
                "- Continue current management."
            )
        }

df['Zone'] = df['SOC'].apply(lambda x: get_soc_zone(x)['zone'])

# ----------------------------- MAIN APP ------------------------------
st.title("Soil Organic Carbon (SOC) – Management Map")
st.markdown("**Click on any coloured dot** to see the measured SOC value and a tailored land management recommendation.")

# --- SIDEBAR FILTERS (OUTSIDE THE FRAGMENT) ---
st.sidebar.header("🔍 Filter Map by SOC Class")
class_options = ["All"] + sorted(df['Zone'].unique())
selected_class = st.sidebar.selectbox("Show points by SOC class:", class_options)

st.sidebar.markdown("---")
st.sidebar.header("📍 Filter Map by Location")

# State Filter
states = ["All"] + sorted(df['State'].dropna().unique().tolist())
selected_state = st.sidebar.selectbox("Select State:", states)

# LGA Filter (Only shows LGAs in the selected State)
if selected_state != "All":
    available_lgas = df[df['State'] == selected_state]['LGA'].dropna().unique().tolist()
else:
    available_lgas = df['LGA'].dropna().unique().tolist()

lgas = ["All"] + sorted(available_lgas)
selected_lga = st.sidebar.selectbox("Select Local Government Area (LGA):", lgas)

# --- Statistics Expander ---
with st.sidebar.expander("Summary Statistics"):
    st.write(f"**Total Samples:** {len(df)}")
    st.write(f"**Mean SOC:** {df['SOC'].mean():.2f} %")
    st.write(f"**Std dev:** {df['SOC'].std():.2f} %")
    st.write(f"**Min – Max:** {df['SOC'].min():.2f} – {df['SOC'].max():.2f} %")
    st.write("**Class distribution:**")
    for zone, cnt in df['Zone'].value_counts().items():
        st.write(f"- {zone}: {cnt} points ({cnt/len(df)*100:.1f}%)")

# --- MAP RENDERING (INSIDE FRAGMENT) ---
# The @st.fragment wraps ONLY the map. 
# This ensures ONLY the map redraws when filters change, and NOTHING redraws when you click a dot.
@st.fragment
def render_map():
    df_filtered = df.copy()
    if selected_state != "All":
        df_filtered = df_filtered[df_filtered['State'] == selected_state]
    if selected_lga != "All":
        df_filtered = df_filtered[df_filtered['LGA'] == selected_lga]
    if selected_class != "All":
        df_filtered = df_filtered[df_filtered['Zone'] == selected_class]
        
    center_lat = df['Lat'].mean()
    center_lon = df['Long'].mean()
    m = folium.Map(location=[center_lat, center_lon], zoom_start=8, tiles='OpenStreetMap')
    
    for _, row in df_filtered.iterrows():
        zone_info = get_soc_zone(row['SOC'])
        popup_html = f"""
        <div style="font-family: Arial; font-size: 13px; max-width: 300px;">
            <b style="color:{zone_info['color']}">{zone_info['zone']}</b><br>
            <b>SOC:</b> {row['SOC']:.2f} %<br>
            <hr style="margin: 5px 0;">
            {zone_info['recommendation']}
        </div>
        """
        folium.CircleMarker(
            location=[row['Lat'], row['Long']],
            radius=5,
            popup=folium.Popup(popup_html, max_width=350),
            color=zone_info['color'],
            fill=True,
            fill_color=zone_info['color'],
            fill_opacity=0.8,
            weight=1
        ).add_to(m)

    # returned_objects=[] tells Streamlit NOT to listen to clicks
    st_folium(m, use_container_width=True, height=700, returned_objects=[])

# Run the map function
render_map()

st.markdown("---")
st.caption("**Recommendations are based on the SOC value only. Local field validation may refine these suggestions.**")