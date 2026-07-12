# -*- coding: utf-8 -*-
import streamlit as st
import requests
import pandas as pd

# Page Configuration
st.set_page_config(
    page_title="Expedia Sentinel — Hotel Review Intelligence Engine",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Endpoint URL
API_URL = "http://127.0.0.1:8000/api"

# Custom Premium Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Outfit:wght@400;500;600;700;800&display=swap');

    /* Obsidian Premium styling */
    .stApp {
        background-color: #0A0D16;
        color: #CBD5E1;
        font-family: 'Plus Jakarta Sans', 'Inter', sans-serif;
    }
    .stSidebar {
        background-color: #111625 !important;
        border-right: 1px solid #1E293B;
    }

    /* Main Headers */
    h1, h2, h3 {
        font-family: 'Outfit', sans-serif !important;
        color: #F8FAFC !important;
        font-weight: 800 !important;
        letter-spacing: -0.02em;
    }
    
    .gradient-title {
        background: linear-gradient(90deg, #60A5FA 0%, #C084FC 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem;
        font-weight: 800;
    }

    /* Cards for Hotels */
    .hotel-card {
        background-color: rgba(21, 27, 44, 0.75);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(16px);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .hotel-card:hover {
        transform: translateY(-2px);
        border-color: rgba(96, 165, 250, 0.3);
        box-shadow: 0 12px 40px 0 rgba(96, 165, 250, 0.12);
    }
    .hotel-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 18px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        padding-bottom: 12px;
    }
    .hotel-title {
        font-size: 22px;
        font-weight: 700;
        color: #60A5FA;
    }
    .score-badge {
        background: linear-gradient(135deg, #2563EB 0%, #7C3AED 100%);
        color: white;
        padding: 8px 18px;
        border-radius: 30px;
        font-weight: 800;
        font-size: 15px;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        box-shadow: 0 4px 15px rgba(37, 99, 235, 0.35);
    }
    
    /* Ratings grid pills */
    .rating-pill {
        background-color: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 10px 14px;
        display: flex;
        flex-direction: column;
        gap: 4px;
        transition: background-color 0.2s ease;
    }
    .rating-pill:hover {
        background-color: rgba(255, 255, 255, 0.06);
    }
    .rating-label {
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748B;
    }
    .rating-val-high {
        font-size: 16px;
        font-weight: 700;
        color: #34D399; /* Emerald green */
        text-shadow: 0 0 8px rgba(52, 211, 153, 0.15);
    }
    .rating-val-normal {
        font-size: 16px;
        font-weight: 700;
        color: #F1F5F9;
    }
    .rating-val-na {
        font-size: 16px;
        font-weight: 700;
        color: #475569; /* Slate gray */
    }

    /* Alert styling for anomalies */
    .anomaly-alert {
        background: linear-gradient(135deg, rgba(127, 29, 29, 0.25) 0%, rgba(69, 26, 34, 0.25) 100%);
        border-left: 4px solid #EF4444;
        border-top: 1px solid rgba(239, 68, 68, 0.15);
        border-right: 1px solid rgba(239, 68, 68, 0.15);
        border-bottom: 1px solid rgba(239, 68, 68, 0.15);
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 16px;
        color: #FCA5A5;
    }
    
    /* Hide Streamlit default header, main menu, deploy button, and footer */
    header, [data-testid="stHeader"] {
        visibility: hidden !important;
        height: 0px !important;
    }
    .stDeployButton, div[data-testid="stConnectionStatus"] {
        display: none !important;
    }
    footer {
        visibility: hidden !important;
    }
    #MainMenu {
        visibility: hidden !important;
    }
</style>
""", unsafe_allow_html=True)



import re

def get_desired_dimensions(desc: str) -> list[str]:
    """Extracts key travel dimensions from a traveler profile description."""
    dimensions = []
    desc_lower = desc.lower()
    
    if "safety" in desc_lower or "safe" in desc_lower:
        dimensions.append("safety")
    if "culture" in desc_lower or "market" in desc_lower:
        dimensions.append("local_culture")
    if "central" in desc_lower or "office district" in desc_lower or "walkable" in desc_lower:
        dimensions.append("location_central")
    if "wifi" in desc_lower or "internet" in desc_lower:
        dimensions.append("wifi")
    if "meeting" in desc_lower or "workspace" in desc_lower:
        dimensions.append("meeting_space")
    if "quiet" in desc_lower or "peaceful" in desc_lower or "noise" in desc_lower:
        dimensions.append("quiet_room")
    if "budget" in desc_lower or "cheap" in desc_lower or "shoestring" in desc_lower:
        if "tight" in desc_lower or "low" in desc_lower or "cheap" in desc_lower:
            dimensions.append("low_budget")
        elif "mid-range" in desc_lower or "mid_range" in desc_lower:
            dimensions.append("mid_range_budget")
        else:
            dimensions.append("value_for_money")
    if "luxury" in desc_lower or "discerning" in desc_lower or "five-star" in desc_lower or "refinement" in desc_lower:
        dimensions.append("luxury_service")
    if "spa" in desc_lower or "wellness" in desc_lower:
        dimensions.append("spa_and_wellness")
    if "kid" in desc_lower or "child" in desc_lower or "toddler" in desc_lower or "family" in desc_lower:
        dimensions.append("family_friendly")
    if "direct flight" in desc_lower:
        dimensions.append("direct_flights")
    if "accessibility" in desc_lower or "wheelchair" in desc_lower or "mobility" in desc_lower or "step-free" in desc_lower:
        dimensions.append("accessibility")
    if "pool" in desc_lower:
        dimensions.append("pool")
        
    if not dimensions:
        parts = [p.strip() for p in desc.split(",") if len(p.strip()) > 3]
        for part in parts[:4]:
            clean = re.sub(r'[^a-z0-9\s]', '', part.lower())
            clean = "_".join(clean.split())
            dimensions.append(clean)
    return dimensions

def format_aspect_score(val) -> str:
    """Formats an aspect score to 1 decimal place, or returns 'N/A' if None."""
    if val is None:
        return "N/A"
    return f"{val:.1f}"

def render_pill_value_html(val) -> str:
    """Formats aspect score to custom styled HTML depending on score rating."""
    if val is None:
        return '<span class="rating-val-na">N/A</span>'
    elif val >= 4.5:
        return f'<span class="rating-val-high">&#9733; {val:.1f}</span>'
    else:
        return f'<span class="rating-val-normal">{val:.1f}</span>'

def check_api_status():
    """Verify if the backend API server is running."""
    try:
        requests.get(f"{API_URL}/profiles")
        return True
    except requests.exceptions.ConnectionError:
        return False


# Main Sidebar
st.sidebar.title("Hotel Review Sentinel")
st.sidebar.markdown("*AI-Powered Hotel Intelligence Engine*")
st.sidebar.divider()

# Verify Backend Connection
api_active = check_api_status()
if not api_active:
    st.sidebar.error("🔴 Backend API is Offline")
    st.sidebar.info("Run `python api.py` from the project terminal to start the FastAPI server on port 8000.")
else:
    st.sidebar.success("🟢 Backend API is Online")

page = st.sidebar.radio("Navigate Pages", [
    "🔍 Personalized Recommender", 
    "📈 Operations Monitor", 
    "🌦️ Seasonality Explorer"
])

st.sidebar.divider()
st.sidebar.info("Sentinel parses review sentences to calculate aspect scorecard ratings, detect operational drops, and find semantic RAG evidence.")

# PAGE 1: Personalized Recommender
if page == "🔍 Personalized Recommender":
    st.title("🔍 Personalized Recommender & Structured RAG")
    st.markdown("Enter your travel persona or select one of the predefined profiles to receive Multi-Criteria Decision (MCDA) recommendations supported by semantic RAG evidence citations.")
    
    if api_active:
        # Load predefined profiles
        profiles = requests.get(f"{API_URL}/profiles").json()
        
        # Profile Select Choice
        mode = st.radio("Choose Input Mode", ["Select Predefined Profile", "Enter Custom Query"], horizontal=True)
        
        if mode == "Select Predefined Profile":
            selected_profile_id = st.selectbox("Predefined Profile", list(profiles.keys()), 
                                               format_func=lambda x: f"{x}: {profiles[x]}")
            query_str = selected_profile_id
            description = profiles[selected_profile_id]
            
            # Show full description in case it is clipped in the selectbox UI
            st.info(f"📋 **Full Description:** {description}")
            
            desired_dims = get_desired_dimensions(description)
            st.markdown("**Desired Dimensions:** " + " ".join([f"`{dim}`" for dim in desired_dims]))
        else:
            query_str = st.text_area("Traveler Needs Description", 
                                     placeholder="Describe who you are, what you need (e.g. fast wifi, quiet room), and any mobility constraints (e.g. wheelchair access)...")
            st.caption("Example: *I am a digital nomad on a budget who needs super fast internet for video calls and step-free wheelchair access.*")
            
        top_n = st.slider("Top Recommendations Count", min_value=1, max_value=10, value=5)
        
        if st.button("Generate Recommendations", type="primary", disabled=(mode == "Enter Custom Query" and not query_str)):
            with st.spinner("Classifying weights and ranking hotels..."):
                response = requests.post(f"{API_URL}/recommend", json={"query": query_str, "top_n": top_n}).json()
                
            weights = response["weights"]
            recs = response["recommendations"]
            
            # Display Match Weights
            st.subheader("Determined Aspect Priority Weights")
            st.markdown("The system classified the traveler prompt and distributed importance weights among the 7 target aspects:")
            cols = st.columns(7)
            for idx, (aspect, w) in enumerate(weights.items()):
                with cols[idx]:
                    st.metric(label=aspect, value=f"{w*100:.0f}%")
                    st.progress(float(w))
                    
            st.divider()
            
            # Display Recommended Hotels
            st.subheader("Ranked Hotel Recommendations")
            for idx, hotel in enumerate(recs):
                match_score_str = f"{hotel['match_score']:.2f}"
                overall_rating_str = f"{hotel['overall_rating']:.2f}"
                # Custom Hotel Card Card
                st.markdown(f"""
                <div class="hotel-card">
                    <div class="hotel-header">
                        <div>
                            <span style="font-size: 20px; font-weight: 700; color: #60A5FA;">#{idx+1} {hotel['hotel_name']}</span>
                            <span style="background-color: #2D3748; padding: 3px 8px; border-radius: 4px; font-size: 12px; margin-left: 10px; color: #CBD5E1;">{hotel['hotel_category']}</span>
                        </div>
                        <div class="score-badge">Match Score: {match_score_str}</div>
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 15px;">
                        <div class="rating-pill">
                            <span class="rating-label">Overall Rating</span> 
                            <span class="rating-val-normal">&#9733; {overall_rating_str}</span>
                        </div>
                        <div class="rating-pill">
                            <span class="rating-label">Cleanliness</span> 
                            {render_pill_value_html(hotel['aspect_scores']['Cleanliness'])}
                        </div>
                        <div class="rating-pill">
                            <span class="rating-label">Service</span> 
                            {render_pill_value_html(hotel['aspect_scores']['Service'])}
                        </div>
                        <div class="rating-pill">
                            <span class="rating-label">Location</span> 
                            {render_pill_value_html(hotel['aspect_scores']['Location'])}
                        </div>
                        <div class="rating-pill">
                            <span class="rating-label">Value</span> 
                            {render_pill_value_html(hotel['aspect_scores']['Value'])}
                        </div>
                        <div class="rating-pill">
                            <span class="rating-label">WiFi / Quietness</span> 
                            {render_pill_value_html(hotel['aspect_scores']['WiFi/Quietness'])}
                        </div>
                        <div class="rating-pill">
                            <span class="rating-label">Family Friendliness</span> 
                            {render_pill_value_html(hotel['aspect_scores']['Family-Friendliness'])}
                        </div>
                        <div class="rating-pill">
                            <span class="rating-label">Accessibility</span> 
                            {render_pill_value_html(hotel['aspect_scores']['Accessibility'])}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Render Accessibility Hard Filter Warning if applicable
                if hotel.get("accessibility_penalty", 0.0) > 0:
                    st.warning(f"⚠️ **Accessibility hard filter penalty applied (-{hotel['accessibility_penalty']:.2f} points)**. This hotel has negative accessibility reviews.")
                
                # Render Aspect Quality Floor Penalty if applicable
                if hotel.get("quality_penalty", 0.0) > 0:
                    st.warning(f"⚠️ **Aspect quality floor penalty applied (-{hotel['quality_penalty']:.2f} points)**. Aspect ratings fall below the 2.5 baseline.")
                
                # Evidence citations expander
                with st.expander(f"💬 Read Verified Evidence Citations (Structured RAG matches) for {hotel['hotel_name']}"):
                    if hotel.get("evidence"):
                        for cit_idx, citation in enumerate(hotel["evidence"]):
                            st.markdown(f"**Evidence #{cit_idx+1} (Review ID: `{citation['review_id']}`):**")
                            # Highlight accessibility or wifi keywords if applicable
                            st.info(f"\"{citation['text']}\"")
                    else:
                        st.write("No positive reviews matching your core aspects were found.")
                        
    else:
        st.warning("Please connect the backend API server first.")

# PAGE 2: Operations Monitor
elif page == "📈 Operations Monitor":
    st.title("📈 Operations Monitor")
    st.markdown("Inspect operational quality indicators: drift-isolated quality anomalies.")
    
    if api_active:
        st.subheader("Drift-Isolated Quality Anomalies (Last 60 Days)")
        st.markdown("These alerts highlight hotels whose cleanliness or service ratings dropped by >20% in the last 60 days, excluding drops that occurred in the previous year (treating them as seasonal drift).")
        
        with st.spinner("Fetching anomalies..."):
            anomalies = requests.get(f"{API_URL}/anomalies").json()
            
        if anomalies:
            for idx, a in enumerate(anomalies):
                with st.expander(f"🚨 Operations Alert: {a['hotel_name']} ({a['hotel_id']}) — Aspect: {a['aspect']} Drop: {a['drop_percentage']}%"):
                    st.write(f"**Historic Average Aspect Score:** {a['historic_score']:.2f} | **Recent 60 Days Aspect Score:** {a['recent_score']:.2f}")
                    
                    # Fetch monthly rating stream of this hotel
                    try:
                        hist_res = requests.get(f"{API_URL}/seasonality/{a['hotel_id']}").json()
                        ratings_stream = hist_res.get("ratings_stream")
                        aspect = a['aspect']
                        if ratings_stream and aspect in ratings_stream:
                            st.markdown(f"**Monthly rating stream for {aspect}:**")
                            aspect_data = ratings_stream[aspect]
                            df_aspect = pd.DataFrame(list(aspect_data.items()), columns=["Month", f"{aspect} Rating"])
                            df_aspect = df_aspect.sort_values(by="Month").reset_index(drop=True)
                            st.line_chart(df_aspect.set_index("Month"), height=220)
                        else:
                            st.info("No rating stream timeline data available for this aspect.")
                    except Exception as e:
                        st.error(f"Could not load rating stream timeline chart: {e}")
        else:
            st.success("✅ No recent operational quality anomalies detected. All recent dips are classified as seasonal drifts.")
    else:
        st.warning("Please connect the backend API server first.")

# PAGE 3: Seasonality Explorer
elif page == "🌦️ Seasonality Explorer":
    st.title("🌦️ Seasonality Explorer")
    st.markdown("Select a hotel to analyze its 24-month monthly ratings stream and view its climate seasonality narrative.")
    
    if api_active:
        # Load hotel options
        hotels = requests.get(f"{API_URL}/hotels").json()
        hotel_map = {h["hotel_id"]: h["hotel_name"] for h in hotels}
        
        selected_hotel_id = st.selectbox("Select Hotel", list(hotel_map.keys()), 
                                         format_func=lambda x: f"{hotel_map[x]} ({x})")
        
        if selected_hotel_id:
            with st.spinner("Generating seasonality profiles..."):
                response = requests.get(f"{API_URL}/seasonality/{selected_hotel_id}").json()
                
            hotel_name = response["hotel_name"]
            trend = response["trend"]
            ratings_stream = response["ratings_stream"]
            
            # Line Chart of temporal ratings stream (always overall rating at the top)
            st.subheader("Monthly Customer Ratings Stream (Overall)")
            if ratings_stream and "Overall" in ratings_stream:
                overall_data = ratings_stream["Overall"]
                df_stream = pd.DataFrame(list(overall_data.items()), columns=["Month", "Overall Rating"])
                df_stream = df_stream.sort_values(by="Month").reset_index(drop=True)
                st.line_chart(df_stream.set_index("Month"), height=250)
            else:
                st.write("No temporal ratings timeline data available for this hotel.")
                
            # Seasonality Explanation Narrative
            st.subheader("Operational Seasonality Analysis")
            if trend.get("seasonal_aspect"):
                st.info(f"🎯 **Identified Seasonal Aspect:** `{trend['seasonal_aspect']}`")
                
                # Show the specific aspect plot alongside the narrative
                seasonal_aspect = trend["seasonal_aspect"]
                if ratings_stream and seasonal_aspect in ratings_stream:
                    st.markdown(f"**Monthly ratings stream for seasonal aspect: {seasonal_aspect}**")
                    aspect_data = ratings_stream[seasonal_aspect]
                    df_aspect = pd.DataFrame(list(aspect_data.items()), columns=["Month", f"{seasonal_aspect} Rating"])
                    df_aspect = df_aspect.sort_values(by="Month").reset_index(drop=True)
                    st.line_chart(df_aspect.set_index("Month"), height=250)
                
                st.markdown(f"""
                <div style="background-color: #1E293B; border-left: 4px solid #3B82F6; padding: 18px; border-radius: 4px; font-size: 15px; line-height: 1.6;">
                    {trend['explanation']}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.write(trend["explanation"])
                
    else:
        st.warning("Please connect the backend API server first.")
