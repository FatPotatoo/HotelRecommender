# Expedia Hotel Review Sentinel (Sentinel)

Sentinel is an AI-powered hotel intelligence and recommendation system built for the Innovation Round of the Expedia Hackathon. It translates unstructured customer reviews into personalized, evidence-backed hotel recommendations, analyzes quality trends over time, detects seasonal drift, and resolves conflicting cohort opinions.

---

## 🏗️ Codebase Architecture

The project is structured into modular Python components:

- **`requirements.txt`**: Project dependencies (Streamlit, FastAPI, SentenceTransformers, Plotly, PyTorch).
- **`sentiment_engine.py`**: Handles aspect and sentiment classification using a **Dual-Path Hybrid Pipeline** (exact match cache $\rightarrow$ semantic cosine similarity fallback $\rightarrow$ zero-shot classification).
- **`data_processor.py`**: Precomputes hotel aspect scorecards, extracts monthly rating trends, and performs geography-aware seasonal drift analysis.
- **`recommender.py`**: Maps traveler profiles (P01-P50) or custom search queries to aspect weights, ranks hotels using Multi-Criteria Decision Analysis (MCDA), and retrieves relevant cohort-specific review citations.
- **`app.py`**: The Streamlit user dashboard featuring Plotly radar charts, longitudinal time-series trends, and contradiction panels.
- **`api.py`**: FastAPI REST server exposing recommendation endpoints.
- **`run.py`**: Orchestrates starting the Streamlit app and FastAPI uvicorn server concurrently.

---

## 🚀 Setup & Execution Instructions

### Prerequisites
Ensure you have **Python 3.8+** installed on your system.

### 1. Clone & Set Up Virtual Environment
Navigate to the project root directory and create a virtual environment:
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
.\venv\Scripts\activate

# Activate virtual environment (macOS/Linux)
source venv/bin/activate
```

### 2. Install Dependencies
Install all required libraries. The models (SentenceTransformers and zero-shot NLI classifier) will download automatically on the first run.
```bash
pip install -r requirements.txt
```

### 3. Run the Application
Start both the FastAPI backend and the Streamlit frontend concurrently using the helper runner:
```bash
python run.py
```
- **Streamlit UI**: Opens automatically at `http://localhost:8501`.
- **FastAPI Documentation**: Available at `http://localhost:8000/docs`.

---

## 📌 Assumptions Made

1. **Semantic Anchoring Stability**: The 87 unique sentences identified in the reviews represent stable semantic templates. Any slight variations (e.g., typos, formatting) can be safely mapped to these anchors via SentenceTransformer cosine similarity.
2. **Hemisphere-Based Seasons**: Hotels are classified into Northern, Southern, or Tropical Monsoonal zones based on their city location to ensure YoY seasonal deviations are calculated against accurate local seasons.
3. **Cohort Coherence**: Travelers within the same cohort (e.g. families, solo travelers, corporate road-warriors) share similar grading scales and values, making traveler-type weighting highly effective for personalization.
4. **Universal Quality Floor**: Aspects like *Cleanliness* and *Service* represent universal baselines. Regardless of traveler weight preferences, scorecards dropping below $2.5$ in these areas warrant a quality penalty.

---

## ⚠️ System Limitations

1. **Model Ingestion Latency (First Run Only)**: The first time the system runs, it downloads `all-MiniLM-L6-v2` and `distilbart-mnli-12-3` from Hugging Face, which requires an active internet connection. Subsequents runs are fully offline.
2. **Binary Sentiment Granularity**: Sentence sentiment is mapped to a binary scale (`-1` or `+1`). It does not distinguish the intensity of expressions (e.g., *"extremely dirty"* vs *"a bit dusty"*).
3. **Data Dependency on Review Frequency**: Hotels with very few reviews may have sparser seasonal or temporal trend graphs, leading to default neutral scores (3.00) for aspects with no historical feedback.

---

## 🔮 Future Improvements

1. **Online Ingestion & Streaming**: Extend `data_processor.py` to ingest reviews via Kafka/RabbitMQ, updating the aspect scorecard matrix incrementally without re-processing historical files.
2. **Multimodal Review Verification**: Ingest customer-uploaded photos to cross-verify review aspects (e.g., using computer vision to check cleanliness or room size matches claims).
3. **Locally Hosted Small LLMs**: Transition the zero-shot fallback to a locally hosted GGUF model (like Llama-3-8B) to run entirely offline on standard laptops, removing external Hugging Face downloads.
