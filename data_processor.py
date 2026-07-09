import json
import re
from datetime import datetime, timedelta
import sentiment_engine

# The 7 target aspects specified in the PRD
ASPECTS = [
    "Cleanliness",
    "Service",
    "Location",
    "Value",
    "Accessibility",
    "WiFi/Quietness",
    "Family-Friendliness"
]

def load_data(reviews_path: str) -> list[dict]:
    """Load reviews from JSON file."""
    with open(reviews_path, "r", encoding="utf-8") as f:
        return json.load(f)

def segment_sentences(review_text: str) -> list[str]:
    """Split review text into individual sentences using punctuation boundaries."""
    # Split on terminal punctuation followed by space or end-of-string
    sentence_end = re.compile(r'(?<=[.!?])\s+')
    return [s.strip() for s in sentence_end.split(review_text) if s.strip()]

def compile_aspect_scorecard(reviews: list[dict]) -> dict:
    """
    Groups reviews by hotel_id, splits into sentences, classifies sentiments,
    and aggregates scores from 1.0 to 5.0 for each of the 7 aspects.
    
    Formula:
        Aspect Score = 3.0 + 2.0 * ((Positive Count - Negative Count) / Total Count)
        
    Defaults to the hotel's average overall rating (or 3.0 if no reviews exist) if Total Count is 0.
    
    Returns:
        dict: { hotel_id: { aspect_name: float_score } }
    """
    # Compute overall hotel average ratings for fallback
    hotel_overall_ratings = {}
    hotel_review_counts = {}
    
    # Store positive/negative counts per aspect per hotel
    # Structure: { hotel_id: { aspect: { "pos": 0, "neg": 0 } } }
    scores_agg = {}
    
    for review in reviews:
        hotel_id = review["hotel_id"]
        rating = float(review["rating"])
        
        # Initialize aggregates for hotel
        if hotel_id not in scores_agg:
            scores_agg[hotel_id] = {aspect: {"pos": 0, "neg": 0} for aspect in ASPECTS}
            hotel_overall_ratings[hotel_id] = 0.0
            hotel_review_counts[hotel_id] = 0
            
        # Update overall rating aggregate
        hotel_overall_ratings[hotel_id] += rating
        hotel_review_counts[hotel_id] += 1
        
        # Segment and process sentences
        sentences = segment_sentences(review["review_text"])
        for sentence in sentences:
            res = sentiment_engine.extract_sentence_aspect_sentiment(sentence)
            aspect = res["aspect"]
            sentiment = res["sentiment"]
            
            # Map only if it matches our 7 target aspects and has non-zero sentiment
            if aspect in ASPECTS and sentiment != 0:
                if sentiment == 1:
                    scores_agg[hotel_id][aspect]["pos"] += 1
                elif sentiment == -1:
                    scores_agg[hotel_id][aspect]["neg"] += 1

    # Calculate final scorecard
    scorecard = {}
    for hotel_id, aspects_data in scores_agg.items():
        # Calculate overall rating fallback
        review_count = hotel_review_counts[hotel_id]
        overall_rating_fallback = (hotel_overall_ratings[hotel_id] / review_count) if review_count > 0 else 3.0
        
        scorecard[hotel_id] = {}
        for aspect in ASPECTS:
            pos = aspects_data[aspect]["pos"]
            neg = aspects_data[aspect]["neg"]
            total = pos + neg
            
            if total > 0:
                score = 3.0 + 2.0 * ((pos - neg) / total)
            else:
                score = overall_rating_fallback
                
            # Clamp the score between 1.0 and 5.0 and round to 2 decimal places
            scorecard[hotel_id][aspect] = round(max(1.0, min(5.0, score)), 2)
            
    return scorecard

def detect_quality_anomalies(reviews: list[dict], threshold: float = -0.20) -> list[dict]:
    """
    Detects and flags hotels whose average cleanliness or service scores dropped by more
    than 20% (threshold = -0.20) in the last 60 days of the dataset compared to their historic mean.
    
    Returns:
        list[dict]: List of detected anomalies with details.
    """
    if not reviews:
        return []
        
    # 1. Parse review dates and find max date
    parsed_reviews = []
    max_date = None
    for r in reviews:
        try:
            # Expect YYYY-MM-DD
            dt = datetime.strptime(r["review_date"], "%Y-%m-%d").date()
            parsed_reviews.append((dt, r))
            if max_date is None or dt > max_date:
                max_date = dt
        except (ValueError, KeyError):
            # Ignore invalid dates
            pass
            
    if not max_date:
        return []
        
    # 2. Split into Recent (last 60 days) and Historic
    cutoff_date = max_date - timedelta(days=60)
    recent_reviews = [r for dt, r in parsed_reviews if dt >= cutoff_date]
    historic_reviews = [r for dt, r in parsed_reviews if dt < cutoff_date]
    
    # 3. Compute cleanliness and service scores for both periods
    def get_period_aspect_scores(period_reviews):
        scores_agg = {}
        for r in period_reviews:
            hotel_id = r["hotel_id"]
            if hotel_id not in scores_agg:
                scores_agg[hotel_id] = {aspect: {"pos": 0, "neg": 0} for aspect in ["Cleanliness", "Service"]}
                
            sentences = segment_sentences(r["review_text"])
            for sentence in sentences:
                res = sentiment_engine.extract_sentence_aspect_sentiment(sentence)
                aspect = res["aspect"]
                sentiment = res["sentiment"]
                if aspect in ["Cleanliness", "Service"] and sentiment != 0:
                    if sentiment == 1:
                        scores_agg[hotel_id][aspect]["pos"] += 1
                    elif sentiment == -1:
                        scores_agg[hotel_id][aspect]["neg"] += 1
                        
        # Convert to final scores
        period_scores = {}
        for hotel_id, data in scores_agg.items():
            period_scores[hotel_id] = {}
            for aspect in ["Cleanliness", "Service"]:
                pos = data[aspect]["pos"]
                neg = data[aspect]["neg"]
                total = pos + neg
                if total > 0:
                    period_scores[hotel_id][aspect] = round(3.0 + 2.0 * ((pos - neg) / total), 2)
                else:
                    period_scores[hotel_id][aspect] = None
        return period_scores

    recent_scores = get_period_aspect_scores(recent_reviews)
    historic_scores = get_period_aspect_scores(historic_reviews)
    
    # 4. Check for drops in Cleanliness and Service
    anomalies = []
    # Find all unique hotels across both splits
    all_hotels = set(recent_scores.keys()).union(set(historic_scores.keys()))
    
    for hotel_id in all_hotels:
        for aspect in ["Cleanliness", "Service"]:
            h_score = historic_scores.get(hotel_id, {}).get(aspect)
            r_score = recent_scores.get(hotel_id, {}).get(aspect)
            
            if h_score is not None and r_score is not None and h_score > 0:
                drop_ratio = (r_score - h_score) / h_score
                if drop_ratio < threshold:
                    # Extract hotel name
                    hotel_name = "Unknown Hotel"
                    for dt, r in parsed_reviews:
                        if r["hotel_id"] == hotel_id:
                            hotel_name = r.get("hotel_name", "Unknown Hotel")
                            break
                    anomalies.append({
                        "hotel_id": hotel_id,
                        "hotel_name": hotel_name,
                        "aspect": aspect,
                        "historic_score": h_score,
                        "recent_score": r_score,
                        "drop_percentage": round(drop_ratio * 100, 2)
                    })
                    
    return anomalies
