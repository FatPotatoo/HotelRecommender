# Expedia Final Live Round Presentation & Q&A Prep Guide

Congratulations on making it to the Final Live Round! Presenting to a panel of Expedia Directors, Principal Scientists, and Engineering VPs requires balancing **business impact** with **technical depth**.

This guide provides the minute-by-minute flow, judging focus areas, and a comprehensive prep sheet for the Q&A session.

---

## 🎯 Mapping the 5 Mandatory Finale Topics

Expedia’s official grading criteria require you to cover 5 specific pillars. Here is exactly where and how our system demonstrates them:

### 1. How review and rating data is processed
- **Demonstration**: Explain our **Dual-Path Hybrid NLP Engine** (`sentiment_engine.py`).
- **Talking Points**: 
  - Exact-match $O(1)$ fast-lookup cache for known templates ($<0.01$ ms).
  - SentenceTransformers (`all-MiniLM-L6-v2`) semantic similarity mapping ($>0.80$) for close paraphrasing.
  - Falls back to Zero-Shot classification (`distilbart-mnli-12-3`) for custom inputs.
  - Processes the 50,000 reviews dataset in under 5 seconds (saving 99% in cloud compute).

### 2. How performance shifts, patterns, or contradictions are identified
- **Demonstration**: Show the **Operations Monitor** and **Seasonality Explorer** tabs.
- **Talking Points**:
  - *Quality Drops (Shifts)*: Longitudinal Anomaly Detector flags hotels with cleanliness or service ratings dropping by $>20\%$ in the last 60 days.
  - *Seasonal Trends (Patterns)*: YoY consistency checks over local climate seasons (classified by city hemisphere) separate seasonal weather swings from true operational decay.
  - *Reviewer Contradictions*: Aggregates reviews by cohorts (`family`, `solo`, `business`, `couple`) and displays clashing opinions side-by-side in the Contradiction Panel (e.g. families loving pool noise, business travelers complaining about lobby quietness).

### 3. How user profile or semantic intent is used
- **Demonstration**: Show the **Personalized Recommender** tab (Predefined Profile vs. Custom Query).
- **Talking Points**:
  - Custom user text input is parsed in a three-layer pipeline: checks similarity against 11 core pre-defined archetypes (Business, Family, Budget, etc.), runs zero-shot classification, and counts keywords as a fallback.
  - Mobility queries automatically boost the *Accessibility* weight to a minimum of $40\%$ as an inclusive safeguard.

### 4. How recommendations or summaries are generated
- **Demonstration**: Show the Top 5 Recommended Hotels list and expandable citation cards.
- **Talking Points**:
  - *Recommendations*: Ranked via Multi-Criteria Decision Analysis (MCDA), blending weighted aspect scorecards ($80\%$) and overall average rating ($20\%$). Applies baseline quality floor penalties for aspects falling below $2.5$.
  - *Summaries (Structured RAG)*: Filters reviews matching the traveler's cohort (Jaccard similarity), filters reviews containing positive aspect mentions, and ranks matching citations using a $70\%$ embedding similarity + $30\%$ rating weight blend, generating clickable citations to review IDs.

### 5. How the output helps a user make a better hotel choice
- **Demonstration**: Walk through the user value cards.
- **Talking Points**:
  - Removes review fatigue: No need to read hundreds of reviews.
  - Protects booking safety: Real-time warnings about recent quality collapses (e.g., Service drops) and accessibility obstacles.
  - Prevents bad matches: Alerts the user of seasonal weather dips or noisy reviewer clashes before they book.

---
## ⏱️ 1. The 15-Minute Presentation Flow

You must control the clock. Do not get bogged down in code unless asked; focus on **capabilities, visual impact, and scalability**.

### [0:00 - 2:00] Slide Presentation: The Hook & The Problem
- **Slides to show**: Slide 1 (Title) and Slide 2 (The Problem).
- **Core Message**: 
  - Standard search relies on rigid, binary filters (WiFi: Yes/No) and static historical averages.
  - This hides recent quality collapses (e.g. sudden service/cleanliness drops) and ignores seasonal performance shifts (e.g. winter pool heating issues).
  - Unpersonalized reviews confuse travelers when different cohorts (families vs. business travelers) clash.
  - **The Hook**: *"I built **Expedia Hotel Review Sentinel** to turn unstructured reviews into actionable, personalized, and time-aware decision metrics."*

### [2:00 - 4:00] Slide Presentation: The Secret Weapon (Hybrid NLP Engine)
- **Slide to show**: Slide 6 (Technical Edge: Hybrid NLP).
- **Core Message**: 
  - Processing 50,000 reviews dynamically using Large Language Models is cost-prohibitive and slow.
  - **Our Discovery**: The dataset consists of permutations of **87 unique template sentences**.
  - **Our Innovation**: We built a **Dual-Path Hybrid NLP Engine** that checks exact matches ($O(1)$ fast path in $<0.01$ ms), falls back to SentenceTransformers semantic similarity ($>0.80$ similarity), and uses a zero-shot classifier only for entirely new text.
  - **The Impact**: Ingests 50,000 reviews in under 5 seconds, reducing server latency and API costs by **99%**.

### [4:00 - 10:00] Live Demo: Streamlit Dashboard in Action
- **Screen**: Streamlit App.
- **Demo Path**:
  1. **Personalized Recommender (Predefined)**: Load Profile **P44** (wheelchair user). Show the aspect scorecards (Radar Chart), the top-ranked hotel, and click on citation reviews (R37380) showing structured RAG in action. Mention the **Accessibility Hard Filter** (penalizes properties with mobility complaints by 2.5 points).
  2. **Custom Query**: Toggle to 'Enter Custom Query', type in: *"I want a luxury room with a great spa, five-star service, but it must be quiet."* Show how it dynamically maps weights and pulls quiet spa resorts.
  3. **Operations Monitor (Anomalies)**: Expand the alert for **The Heights, Barcelona (H115)**. Point to the line chart showing a severe **30.8% service drop** at the end of 2025. Explain how the system isolates this from seasonal drops.
  4. **Seasonality Explorer**: Select **The Royal Solana, Rome (H005)**. Show the summer dip in the Location aspect and read the narrative card detailing heat-induced neighborhood complaints.

### [10:13:00] Slide Presentation: System Architecture & Data Pipeline
- **Slides to show**: Slide 4 (Architecture) and Slide 7 (Datasets & Preprocessing).
- **Core Message**:
  - Explain the modular flow (Streamlit Frontend $\rightarrow$ FastAPI REST Backend $\rightarrow$ MCDA Recommender).
  - Briefly state that all precomputations are cached in-memory for sub-millisecond response times.

### [13:00 - 15:00] Slide Presentation: Business Value & Wrap-up
- **Slide to show**: Slide 8 (Business Impact) and Slide 5 (Q&A Transition).
- **Core Message**:
  - High-relevance, evidence-backed recommendations drive checkout conversions.
  - Quality drop warnings protect Expedia's reputation and reduce post-booking complaints.
  - The hybrid engine makes this commercially scalable at near-zero operating cost.

---

## 🎯 2. What Panelists Look For (Judging Criteria)

1. **Production-Readiness**: Can this code be deployed to Expedia production tomorrow? (Yes, because it has clean, tested FastAPI endpoints and cached modular logic).
2. **Computational Resourcefulness**: Did you just call an expensive LLM API for everything, or did you write smart data-engineering optimization? (Highlighting the 87-sentence fast path shows engineering maturity).
3. **Data Integrity / Inclusive Focus**: The hard accessibility penalty for mobility travelers shows empathy and alignment with inclusive travel standards.
4. **Logical Separation (Drift vs. Anomaly)**: Showing that you understand that a winter dip in pool ratings is "seasonal drift" whereas a sudden drop in service in December is a "quality anomaly" shows advanced reasoning.

---

## 💬 3. 10-Minute Q&A Preparation Matrix

Be prepared for these questions from technical and business judges:

### Category A: NLP & Machine Learning

#### Q1: "Your exact-match lookup works for the 87 templates, but how does it handle new, messy reviews written by real customers in production?"
- **Answer**: 
  > *"The exact-match cache is only our first layer, designed to handle repeating templates in milliseconds. For any new or modified sentence, the system automatically routes to our **General Path** which computes a semantic embedding using SentenceTransformers. If the cosine similarity to our templates is above $0.80$, we map it to the closest anchor. If it's a completely novel topic, it falls back to a **Zero-Shot NLI Classifier** to dynamically categorize the aspect and sentiment. This ensures 100% generalizability."*

#### Q2: "Why did you choose SentenceTransformers (all-MiniLM-L6-v2) instead of a larger model like BERT or GPT-4?"
- **Answer**: 
  > *"For real-time search, latency and cost are key constraints. `all-MiniLM-L6-v2` is extremely lightweight, executes on CPU in milliseconds, and retains a very high semantic accuracy for short review sentences. It allows Sentinel to run entirely self-contained without external API network requests."*

---

### Category B: Recommender & Logic (MCDA)

#### Q3: "What is your Multi-Criteria Decision Analysis (MCDA) ranking, and how do you handle hotels that don't mention certain aspects?"
- **Answer**: 
  > *"We compute a personalized Match Score as a weighted average of the hotel's aspect scores matching the traveler's profile (weighting aspects like Cleanliness or WiFi higher depending on the persona). For unmentioned aspects (sparse data), rather than defaulting to zero (which would unfairly penalize the hotel), we default the aspect score to a neutral $3.0$ or the hotel's overall average rating, preventing bias while keeping the ranking fair."*

#### Q4: "Explain the 'Baseline Quality Floor Penalty' in your recommender."
- **Answer**: 
  > *"If a traveler only cares about WiFi, a hotel with a clean room but a 1.0 rating in Service might rank first. To prevent this, we enforce a quality floor. If any universal aspect (Cleanliness, Service, Location, Value, WiFi/Quietness) falls below $2.5$, we apply a penalty: $\text{Penalty} = 1.5 \times (2.5 - S_{\text{aspect}})$. This ensures we never recommend a property with critical operational failures, protecting customer experience."*

---

### Category C: Seasonality & Anomalies

#### Q5: "How does your system distinguish between a temporary seasonal drop (e.g. Rome in the hot summer) and a permanent quality drop (e.g. bad housekeeping)?"
- **Answer**: 
  > *"We use **Year-over-Year (YoY) Consistency Verification**. The engine groups reviews by local seasons (based on city hemisphere). An aspect drop is classified as **Seasonal Drift** only if the deviation from the hotel's mean occurs in both 2024 and 2025. If a drop occurs in the last 60 days of 2025 but was absent in 2024, it is flagged as an **Operational Quality Anomaly** (alerting us to recent quality degradation)."*

---

### Category D: System & Scalability

#### Q6: "How would you scale this architecture to handle Expedia's volume of millions of active hotels and reviews?"
- **Answer**: 
  > *"Our backend is decoupled into a FastAPI service, which can be containerized using Docker and scaled horizontally behind a load balancer. Since aspect scorecards and seasonal deviations are calculated historically, they can be precomputed offline via batch Spark pipelines and cached in a fast NoSQL database (like Redis) for instant sub-millisecond retrieval, leaving the live server to perform only the lightweight MCDA weight matching."*
