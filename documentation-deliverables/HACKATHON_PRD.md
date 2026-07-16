# Product Requirement Document (PRD)
## Project: Expedia Hotel Review Intelligence Engine (Sentinel)

---

## 1. Executive Summary & Objective

This PRD outlines the requirements for building the **Expedia Hotel Review Sentinel**, an AI-powered hotel intelligence and recommendation system. The system processes 50,000 hotel reviews and 50 traveler profiles to generate personalized, evidence-backed hotel recommendations, analyze aspect-level sentiments, detect quality trends, and identify review contradictions.

The target solution consists of:
1. A **Hybrid Aspect-Sentiment Extraction Engine** (highly generalizable and fast).
2. A **Personalized Recommender Engine** using Multi-Criteria Decision Analysis (MCDA).
3. An interactive **Streamlit Frontend Dashboard** displaying Plotly analytics.
4. A **FastAPI Server** exposing recommendation APIs.

---

## 2. Core Datasets & Technical Insights

### Input Files
- **`hotel_reviews.json`**: ~50,000 reviews across 120 hotels (fields: `review_id`, `hotel_id`, `hotel_name`, `hotel_category`, `rating`, `review_date`, `review_text`, `verified`, `traveler_type`).
- **`user_profiles.json`**: 50 pre-defined travel personas (fields: `profile_id`, `description`).

### The "87-Sentence Template" Breakthrough
- Analysis of the review corpus reveals it is synthetically compiled using exactly **87 unique sentences** in different permutations.
- **Requirement**: The system must utilize a **Dual-Path Hybrid Sentiment Engine**:
  - **Fast Path**: Exact-match lookup of text against a dictionary mapping the 87 sentences to their respective aspect/sentiment labels (runs in milliseconds for the offline dataset).
  - **General Path**: For custom/unseen text, it must embed the sentence using `SentenceTransformer` (`all-MiniLM-L6-v2`) and check cosine similarity against the 87 anchor templates. If similarity is $> 0.80$, map it to the closest anchor.
  - **Fallback Path**: Route any sentence below $0.80$ similarity to a zero-shot classification pipeline (`valhalla/distilbart-mnli-12-3` or `facebook/bart-large-mnli`) to dynamically extract the aspect and sentiment.

---

## 3. Codebase Architecture & File Specification

The codebase must be structured into the following files:

### 3.1. `requirements.txt`
Dependencies to install:
```text
pandas
numpy
streamlit
plotly
fastapi
uvicorn
sentence-transformers
torch
transformers
```

### 3.2. `sentiment_engine.py`
Contains the NLP logic:
- Maps the 87 template sentences to their aspect and sentiment labels.
- Initializes the `SentenceTransformer('all-MiniLM-L6-v2')` model.
- Exposes `extract_sentence_aspect_sentiment(text: str) -> dict`:
  - Returns `{"aspect": str, "sentiment": int}` (where sentiment is `1` for positive, `-1` for negative).
  - Implements the Fast Path (Exact Cache) $\rightarrow$ General Path (Cosine Similarity Fallback) $\rightarrow$ Zero-Shot Classifier.

### 3.3. `data_processor.py`
Ingests the dataset and precomputes hotel metrics:
- Parses `hotel_reviews.json` and splits reviews into sentences.
- Runs them through `sentiment_engine.py` to extract aspects/sentiments.
- Computes and caches three matrices:
  1. **Aspect Scorecard Matrix**: Compiles scores from 1.0 to 5.0 for each of the 7 aspects (Cleanliness, Service, Location, Value, Accessibility, WiFi/Quietness, Family-Friendliness) using the formula:
     $$\text{Aspect Score} = 3.0 + 2.0 \times \left( \frac{\text{Positive Count} - \text{Negative Count}}{\text{Total Count}} \right)$$
     *(Default to hotel overall rating or 3.0 if no mentions exist).*
  2. **Temporal Rating Stream**: Monthly average rating trends over the 24-month timeline (Jan 2024 to Dec 2025) for each hotel.
  3. **Contradiction Matrix**: Group reviews by traveler type and identify hotels where different cohorts have opposing sentiments (e.g. families rate it 5.0 for pool, business travelers rate it 2.0 for lobby noise).

### 3.4. `recommender.py`
Maps user profiles to recommended hotels:
- Parses the 50 user profiles from `user_profiles.json` and maps their text description to aspect weights using a pre-defined map (or NLP keyword extractor). E.g.:
  - *solo female, safety-conscious, walkable base* $\rightarrow$ Location: 0.4, Service: 0.3, Value: 0.3.
  - *wheelchair user, step-free access* $\rightarrow$ Accessibility: 0.8, Service: 0.2 (with Accessibility acting as a hard filter).
- Exposes `get_recommendations(profile_id: str, top_n: int = 5) -> list[dict]`:
  - Ranks hotels based on a **Weighted Utility Match Score**:
    $$ \text{Match Score} = \sum (\text{Hotel Aspect Score} \times \text{User Aspect Weight}) $$
  - Extracts **Evidence Citations**: Find the top 3 positive reviews matching the user's weighted aspects, returning their `review_id` and raw text as evidence.

### 3.5. `app.py`
The Streamlit application frontend:
- **Expedia Themed Layout**: Dark mode or premium curated HSL color palette with custom fonts.
- **Persona Selector Dropdown**: Select profiles `P01` to `P50`. Instantly triggers the recommender and updates the page.
- **Top 5 Recommendation Cards**: Displays hotel cards containing:
  - Hotel name, star category, and match score.
  - **Evidence Summary**: Custom written pitch stating why this hotel fits their profile with clickable citations to review IDs.
- **Detailed Analytics Dashboard (per selected hotel)**:
  - **Plotly Radar Chart**: Visualizing the 7 aspect scores.
  - **Quality Trend Line Chart**: Visualizing monthly rating trends, flagging quality anomalies (e.g. cleanliness drops).
  - **Contradiction Panel**: Highlighting clashing review quotes between traveler types.

### 3.6. `api.py`
Exposes the recommendation logic via REST endpoints:
- Exposes `GET /recommend?profile_id={profile_id}` returning a JSON response matching this schema:
  ```json
  {
    "profile_id": "P01",
    "recommendations": [
      {
        "hotel_id": "H051",
        "hotel_name": "Casa Harbour, Istanbul",
        "hotel_category": "5-star",
        "match_score": 4.62,
        "aspect_scores": {
          "Cleanliness": 4.2,
          "Service": 4.8,
          "Value": 3.9,
          "Location": 4.5,
          "Accessibility": 5.0,
          "WiFi/Quietness": 3.0,
          "Family-Friendliness": 3.0
        },
        "evidence": [
          {
            "review_id": "R31838",
            "text": "Fully step-free with a spacious, well-designed accessible room."
          }
        ]
      }
    ]
  }
  ```

### 3.7. `run.py`
Helper script to start Streamlit and FastAPI concurrently:
```python
import subprocess
import sys

def main():
    api_process = subprocess.Popen([sys.executable, "-m", "uvicorn", "api:app", "--port", "8000"])
    streamlit_process = subprocess.Popen([sys.executable, "-m", "streamlit", "run", "app.py"])
    try:
        api_process.wait()
        streamlit_process.wait()
    except KeyboardInterrupt:
        api_process.terminate()
        streamlit_process.terminate()

if __name__ == "__main__":
    main()
```

---

## 4. Uniqueness & Advanced ML Features

To ensure this solution stands out to the Expedia judges, the following features must be implemented in the logic:
1. **Aspect-Sentiment Decoupling**: Aspect sentiments must be aggregated from individual sentences, keeping them separate from the review's overall rating.
2. **Accessibility Hard Filters**: If a profile requires accessibility (e.g., wheelchair users P08, P20, P32, P44), any hotel with a negative accessibility mention is heavily penalized or filtered out.
3. **Longitudinal Anomaly Detector**: Detect and flag hotels whose average cleanliness or service scores dropped by more than 20% in the last 60 days of the dataset compared to their historic mean.
4. **Trust Index Rating**: Calculate a verifiability score based on the ratio of verified purchases and consistency between verified and unverified ratings.

---

## 5. Verification Plan
1. **Schema Check**: Implement a validation test ensuring recommendations match the JSON output schema exactly.
2. **Profile Coverage**: Verify that all 50 profiles load recommendations successfully.
3. **Latency Benchmarking**: Ensure cached fast-path runs the 50,000 reviews in under 5 seconds.
