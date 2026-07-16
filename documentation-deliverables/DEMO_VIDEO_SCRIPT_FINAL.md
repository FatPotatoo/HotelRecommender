# Expedia Hotel Review Sentinel (Sentinel)
## Final Demo Video Script (Voiceover / Captions)

This script is structured to match the three primary navigation pages in your Streamlit application:
1. **Personalized Recommender** (Predefined Profile & Custom Query)
2. **Operations Monitor** (Quality Anomaly Detection)
3. **Seasonality Explorer** (Seasonal Drift & Local Climatic Impact)

---

### Page 1: Personalized Recommender & Structured RAG

**[Screen: Streamlit Recommender page, Select Predefined Profile P44, click Generate]**

> *"Hello, and welcome to the demonstration of Expedia Hotel Review Sentinel—an advanced, AI-powered hotel recommendation and quality intelligence system built for the Innovation Round of the Expedia Hackathon.*
> 
> *Modern travelers struggle with review fatigue. Sifting through thousands of reviews to verify safety, walkability, or accessibility features is tedious, and static hotel rating averages often hide recent declines in service quality. Sentinel solves this by transforming unstructured review text into verified, personalized hotel scorecards.*
> 
> *Let's select traveler profile P-44—a wheelchair user who requires step-free accessibility. In milliseconds, Sentinel maps this persona to specific aspect weights and ranks the hotels using a Multi-Criteria Decision Analysis model.*
> 
> *Here, we see the top ranked hotels. Sentinel displays a detailed 7-Aspect Scorecard for each hotel, showing a visual fingerprint of the hotel's performance, from cleanliness to value. Our top recommendation, The Boulevard Onyx, Istanbul, shows a customized match score and lists direct, clickable citations to the exact review IDs, like review R-3-7-3-8-0, proving step-free access. Furthermore, if a hotel has reviews detailing accessibility obstacles, Sentinel's hard-rank penalty automatically demotes it, ensuring traveler safety."*

**[Screen: Click 'Enter Custom Query', type in: 'I want a luxury room with a great spa, five-star service, but it must be quiet for sleep']**

> *"But what if the traveler has a unique, custom request? We switch input modes to 'Enter Custom Query' and type in our custom needs. 
> 
> Under the hood, Sentinel runs a two-stage weight-generation pipeline. First, it performs a fast vector similarity match using Sentence-Transformers against our 11 predefined traveler archetypes. If no direct match is found, it falls back to a zero-shot natural language inference model to generate personalized aspect weights dynamically. 
> 
> As you can see, the engine has dynamically prioritized 'Service', 'Cleanliness', and 'Quietness' weights, recommending premium quiet retreats with verified reviews confirming outstanding spa facilities and solid soundproofing."*

---

### Page 2: Operations Monitor (Quality Anomalies)

**[Screen: Click 'Operations Monitor' in the sidebar. Scroll to see the active alerts. Expand the alert for 'The Heights, Barcelona (H115)']**

> *"Next, we navigate to the **Operations Monitor** page. 
> 
> Traditional ratings are lagging indicators. If a hotel's quality collapses today, it remains hidden behind historical ratings. Sentinel’s Longitudinal Anomaly Detector scans the review stream and flags recent drops in cleanliness or service in the last 60 days.
> 
> Here, the system has raised an Operations Alert for **The Heights, Barcelona**, detecting a severe **30.8% drop in its Service aspect**. Looking at the monthly rating stream chart, we can see the rating plummeting at the end of 2025. Crucially, Sentinel compares this YoY against historical data to ensure this is an operational failure, and not just seasonal drift, alerting travelers before they book a declining property."*

---

### Page 3: Seasonality Explorer

**[Screen: Click 'Seasonality Explorer' in the sidebar. Select 'The Royal Solana, Rome (HOO5)' in the dropdown. Scroll down to show the two charts and the narrative card at the bottom]**

> *"Finally, we open the **Seasonality Explorer**. 
> 
> Hotels perform differently depending on the season, but standard platforms ignore this temporal variation. Sentinel’s Geography-Aware Seasonality Engine groups reviews by hemisphere and local climate patterns. 
> 
> For **The Royal Solana, Rome**, Sentinel has identified **Location** as a highly seasonal aspect. Looking at the ratings stream for Location, we see recurring dips during the Summer months across both 2024 and 2025. 
> 
> Sentinel automatically extracts the reviews behind these seasonal dips. The narrative highlights that during Rome's peak summer heat, guests complain that 'everything shuts early and it's sleepy' and that 'poorly lit surroundings' made them feel uneasy walking back at night. This provides travelers with critical seasonal context before booking.
> 
> In summary, Expedia Hotel Review Sentinel provides fast, transparent, and evidence-backed recommendations that protect travelers. Thank you for watching!"*
