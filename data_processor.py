import json
import re
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
