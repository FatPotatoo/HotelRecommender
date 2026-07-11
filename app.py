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
    /* Dark elegant styling components */
    .stApp {
        background-color: #0F121C;
        color: #E2E8F0;
        font-family: 'Outfit', 'Inter', sans-serif;
    }
    .stSidebar {
        background-color: #171E30 !important;
    }
    /* Main Headers */
    h1, h2, h3 {
        color: #F8FAFC !important;
        font-weight: 700 !important;
    }
    /* Cards for Hotels */
    .hotel-card {
        background-color: #1A233A;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        border: 1px solid #2A3655;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .hotel-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        border-bottom: 1px solid #2A3655;
        padding-bottom: 8px;
    }
    .hotel-title {
        font-size: 20px;
        font-weight: 600;
        color: #60A5FA;
    }
    .score-badge {
        background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%);
        color: white;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 16px;
    }
    .rating-label {
        font-size: 14px;
        color: #94A3B8;
    }
    .rating-val {
        font-weight: 600;
        color: #F8FAFC;
    }
    /* Alert styling for anomalies */
    .anomaly-alert {
        background-color: #451A22;
        border: 1px solid #7F1D1D;
        border-radius: 8px;
        padding: 15px;
        color: #FECACA;
        margin-bottom: 12px;
    }
    .anomaly-title {
        font-weight: 700;
        font-size: 16px;
        color: #EF4444;
        margin-bottom: 4px;
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
        
    if not dimensions:
        parts = [p.strip() for p in desc.split(",") if len(p.strip()) > 3]
        for part in parts[:4]:
            clean = re.sub(r'[^a-z0-9\s]', '', part.lower())
            clean = "_".join(clean.split())
            dimensions.append(clean)
    return dimensions

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
                # Custom Hotel Card Card
                st.markdown(f"""
                <div class="hotel-card">
                    <div class="hotel-header">
                        <div>
                            <span style="font-size: 20px; font-weight: 700; color: #60A5FA;">#{idx+1} {hotel['hotel_name']}</span>
                            <span style="background-color: #2D3748; padding: 3px 8px; border-radius: 4px; font-size: 12px; margin-left: 10px; color: #CBD5E1;">{hotel['hotel_category']}</span>
                        </div>
                        <div class="score-badge">Match Score: {hotel['match_score']:.2f}</div>
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 15px;">
                        <div>
                            <span class="rating-label">Overall Rating:</span> 
                            <span class="rating-val">★ {hotel['overall_rating']:.2f}</span>
                        </div>
                        <div>
                            <span class="rating-label">Cleanliness:</span> 
                            <span class="rating-val">{hotel['aspect_scores']['Cleanliness']:.1f}</span>
                        </div>
                        <div>
                            <span class="rating-label">Service:</span> 
                            <span class="rating-val">{hotel['aspect_scores']['Service']:.1f}</span>
                        </div>
                        <div>
                            <span class="rating-label">Location:</span> 
                            <span class="rating-val">{hotel['aspect_scores']['Location']:.1f}</span>
                        </div>
                        <div>
                            <span class="rating-label">Value:</span> 
                            <span class="rating-val">{hotel['aspect_scores']['Value']:.1f}</span>
                        </div>
                        <div>
                            <span class="rating-label">WiFi/Quietness:</span> 
                            <span class="rating-val">{hotel['aspect_scores']['WiFi/Quietness']:.1f}</span>
                        </div>
                        <div>
                            <span class="rating-label">Family-Friendliness:</span> 
                            <span class="rating-val">{hotel['aspect_scores']['Family-Friendliness']:.1f}</span>
                        </div>
                        <div>
                            <span class="rating-label">Accessibility:</span> 
                            <span class="rating-val">{hotel['aspect_scores']['Accessibility']:.1f}</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Render Accessibility Hard Filter Warning if Penalty applied
                if hotel.get("applied_penalty", 0.0) > 0:
                    st.warning(f"⚠️ **Accessibility hard filter penalty applied (-{hotel['applied_penalty']} points)**. This hotel has negative accessibility reviews.")
                
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
            for a in anomalies:
                st.markdown(f"""
                <div class="anomaly-alert">
                    <div class="anomaly-title">🚨 Operations Alert: {a['hotel_name']} ({a['hotel_id']})</div>
                    <div>Aspect: <b>{a['aspect']}</b> | Rating Drop: <b style="color: #EF4444;">{a['drop_percentage']}%</b></div>
                    <div style="font-size: 13px; margin-top: 4px; color: #FCA5A5;">
                        Historic Average Aspect Score: {a['historic_score']:.2f} | Recent 60 Days Aspect Score: {a['recent_score']:.2f}
                    </div>
                </div>
                """, unsafe_allow_html=True)
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
