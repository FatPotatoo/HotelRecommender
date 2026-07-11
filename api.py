import os
import sys
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import data_processor
import recommender

app = FastAPI(title="Expedia Hotel Review Sentinel API")

# Path configs
REVIEWS_PATH = "hotel_reviews.json"
PROFILES_PATH = "user_profiles.json"

# Global Recommender cache
rec_engine = None

@app.on_event("startup")
def startup_event():
    global rec_engine
    try:
        print("Initializing Recommender Engine...")
        rec_engine = recommender.Recommender(REVIEWS_PATH, PROFILES_PATH)
        print("Recommender initialized successfully!")
    except Exception as e:
        print(f"Critical error loading recommender engine: {e}")

class RecommendationRequest(BaseModel):
    query: str
    top_n: int = 5

@app.get("/api/profiles")
def get_profiles():
    if rec_engine is None:
        raise HTTPException(status_code=500, detail="Recommender engine not loaded")
    return rec_engine.profiles

@app.get("/api/hotels")
def get_hotels():
    if rec_engine is None:
        raise HTTPException(status_code=500, detail="Recommender engine not loaded")
    return [
        {"hotel_id": hid, "hotel_name": meta["hotel_name"]}
        for hid, meta in rec_engine.hotel_meta.items()
    ]

@app.post("/api/recommend")
def get_recommendations(req: RecommendationRequest):
    if rec_engine is None:
        raise HTTPException(status_code=500, detail="Recommender engine not loaded")
    try:
        recs = rec_engine.get_recommendations(req.query, top_n=req.top_n)
        
        # Extract weight mappings for the aspect progress bars
        desc = rec_engine.profiles.get(req.query, req.query)
        weights = recommender.extract_aspect_weights(desc)
        
        return {
            "query": req.query,
            "weights": weights,
            "recommendations": recs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/anomalies")
def get_anomalies():
    if rec_engine is None:
        raise HTTPException(status_code=500, detail="Recommender engine not loaded")
    try:
        anomalies = data_processor.detect_quality_anomalies(rec_engine.reviews)
        return anomalies
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/seasonality/{hotel_id}")
def get_hotel_seasonality(hotel_id: str):
    if rec_engine is None:
        raise HTTPException(status_code=500, detail="Recommender engine not loaded")
    if hotel_id not in rec_engine.hotel_meta:
        raise HTTPException(status_code=404, detail="Hotel not found")
    try:
        trends = data_processor.analyze_seasonal_trends(rec_engine.reviews)
        hotel_trend = trends.get(hotel_id, {
            "seasonal_aspect": None,
            "explanation": "No seasonal trends found."
        })
        
        streams = data_processor.compile_temporal_rating_stream(rec_engine.reviews)
        hotel_stream = streams.get(hotel_id, {})
        
        return {
            "hotel_id": hotel_id,
            "hotel_name": rec_engine.hotel_meta[hotel_id]["hotel_name"],
            "trend": hotel_trend,
            "ratings_stream": hotel_stream
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



if __name__ == "__main__":
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)
