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

# Seasonality Profiles for the 20 actual cities in the dataset
CITY_PROFILES = {
    "Istanbul": {"zone": "Northern", "desc": "Mediterranean summer peak weather with high tourism demand; winter brings cold, rainy weather that limits walking and outdoor sights."},
    "Barcelona": {"zone": "Northern", "desc": "Mediterranean climate peaking in summer with beach tourism; winter brings chilly, overcast weather that reduces outdoor activities."},
    "Lisbon": {"zone": "Northern", "desc": "Sunny coastal summer peaks with beach demand; wet, windy winter weather represents the off-season."},
    "Tokyo": {"zone": "Northern", "desc": "Spring cherry blossom and autumn foliage peaks; humid summer heatwaves and cold winter winds affect transit and comfort."},
    "Rome": {"zone": "Northern", "desc": "Peak tourism in spring and summer sightseeing periods; colder, rainy winter conditions represent the off-peak season."},
    "Sydney": {"zone": "Southern", "desc": "Southern Hemisphere summer beach season peaking in Dec-Feb; cooler winter off-peak months occur in Jun-Aug."},
    "Bali": {"zone": "Tropical", "desc": "Dry sunny season peaking in May-Sep with diving and beach tourism; heavy tropical monsoons arrive in Nov-Mar."},
    "New York": {"zone": "Northern", "desc": "High summer tourism and holiday winter season; freezing winter winds limit walkability and outdoor transit."},
    "Lima": {"zone": "Southern", "desc": "Warm, sunny summer beach season in Dec-Apr; grey, humid, overcast winter conditions (Gua) occur in Jun-Oct."},
    "Mexico City": {"zone": "Tropical", "desc": "Dry spring season peak; heavy summer afternoon rains (Jun-Sep) disrupt sightseeing and historical walks."},
    "Bangkok": {"zone": "Tropical", "desc": "Cool, dry winter peak in Nov-Feb; heavy monsoon rains and high humidity occur during May-Oct."},
    "Amsterdam": {"zone": "Northern", "desc": "Summer canal walks and peak travel; cold, wet, windy winters restrict outdoor exploration."},
    "Paris": {"zone": "Northern", "desc": "Pleasant spring and summer leisure peaks; chilly, overcast winters limit outdoor dining and sightseeing."},
    "London": {"zone": "Northern", "desc": "Sunny summer parks and city walks peak; cold, rainy winters reduce outdoor walkability."},
    "San Francisco": {"zone": "Northern", "desc": "Mild, foggy summers and rainy winters; cool coastal winds affect bay walks and outdoor activities."},
    "Dubai": {"zone": "Northern", "desc": "Pleasant winter weather in Nov-Mar; blistering summer heatwaves (May-Sep) limit outdoor tours and force indoor activities."},
    "Seoul": {"zone": "Northern", "desc": "Spring blossom and autumn foliage peaks; freezing sub-zero winter temperatures affect walkability and transit."},
    "Singapore": {"zone": "Tropical", "desc": "Year-round hot climate; heavier rainfall during the Northeast Monsoon (Nov-Jan) affects transit and outdoor sights."},
    "Cape Town": {"zone": "Southern", "desc": "Stunning Southern Hemisphere summer beaches; cold, wet, windy winters (Jun-Aug) limit coastal access."},
    "Mumbai": {"zone": "Tropical", "desc": "Dry winter season (Nov-Feb) peak; severe monsoon rains (Jun-Sep) disrupt transport and outdoor activities."}
}

def load_data(reviews_path: str) -> list[dict]:
    """Load reviews from JSON file."""
    with open(reviews_path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_hotel_city(hotel_name: str) -> str:
    """Parse city name from hotel name field."""
    if ", " in hotel_name:
        return hotel_name.split(", ")[-1].strip()
    return "Unknown"

def segment_sentences(review_text: str) -> list[str]:
    """Split review text into individual sentences using punctuation boundaries."""
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
    hotel_overall_ratings = {}
    hotel_review_counts = {}
    
    # Structure: { hotel_id: { aspect: { "pos": 0, "neg": 0 } } }
    scores_agg = {}
    
    for review in reviews:
        hotel_id = review["hotel_id"]
        rating = float(review["rating"])
        
        if hotel_id not in scores_agg:
            scores_agg[hotel_id] = {aspect: {"pos": 0, "neg": 0} for aspect in ASPECTS}
            hotel_overall_ratings[hotel_id] = 0.0
            hotel_review_counts[hotel_id] = 0
            
        hotel_overall_ratings[hotel_id] += rating
        hotel_review_counts[hotel_id] += 1
        
        sentences = segment_sentences(review["review_text"])
        for sentence in sentences:
            res = sentiment_engine.extract_sentence_aspect_sentiment(sentence)
            aspect = res["aspect"]
            sentiment = res["sentiment"]
            
            if aspect in ASPECTS and sentiment != 0:
                if sentiment == 1:
                    scores_agg[hotel_id][aspect]["pos"] += 1
                elif sentiment == -1:
                    scores_agg[hotel_id][aspect]["neg"] += 1

    scorecard = {}
    for hotel_id, aspects_data in scores_agg.items():
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
                
            scorecard[hotel_id][aspect] = round(max(1.0, min(5.0, score)), 2)
            
    return scorecard

def compile_temporal_rating_stream(reviews: list[dict]) -> dict:
    """
    Compiles monthly average overall ratings for each hotel over the 24-month timeline.
    
    Returns:
        dict: { hotel_id: { "YYYY-MM": average_rating } }
    """
    # Group ratings by hotel and month
    # Structure: { hotel_id: { "YYYY-MM": [ratings] } }
    streams_agg = {}
    
    for r in reviews:
        hotel_id = r["hotel_id"]
        rating = float(r["rating"])
        try:
            dt = datetime.strptime(r["review_date"], "%Y-%m-%d")
            month_key = dt.strftime("%Y-%m")
        except (ValueError, KeyError):
            continue
            
        if hotel_id not in streams_agg:
            streams_agg[hotel_id] = {}
        if month_key not in streams_agg[hotel_id]:
            streams_agg[hotel_id][month_key] = []
        streams_agg[hotel_id][month_key].append(rating)
        
    # Calculate averages
    streams = {}
    for hotel_id, monthly_data in streams_agg.items():
        streams[hotel_id] = {}
        for month_key, ratings in monthly_data.items():
            streams[hotel_id][month_key] = round(sum(ratings) / len(ratings), 2)
            
    return streams

def detect_quality_anomalies(reviews: list[dict], threshold: float = -0.20) -> list[dict]:
    """
    Detects and flags hotels whose average cleanliness or service scores dropped by more
    than 20% (threshold = -0.20) in the last 60 days of the dataset compared to their historic mean.
    
    Excludes cases where the same period of the previous year (e.g. Nov-Dec 2024 vs Jan-Oct 2024)
    exhibited a similar drop, classifying them as seasonal drift instead of real operational quality anomalies.
    
    Returns:
        list[dict]: List of verified quality anomalies.
    """
    if not reviews:
        return []
        
    # 1. Parse review dates and find max date
    parsed_reviews = []
    max_date = None
    for r in reviews:
        try:
            dt = datetime.strptime(r["review_date"], "%Y-%m-%d").date()
            parsed_reviews.append((dt, r))
            if max_date is None or dt > max_date:
                max_date = dt
        except (ValueError, KeyError):
            pass
            
    if not max_date:
        return []
        
    # 60 days cutoff for recent window
    recent_cutoff = max_date - timedelta(days=60)
    
    # 2. Split reviews into splits
    recent_reviews = [r for dt, r in parsed_reviews if dt >= recent_cutoff]
    historic_reviews = [r for dt, r in parsed_reviews if dt < recent_cutoff]
    
    # Identify which calendar months are in the recent window (e.g., [11, 12])
    recent_months = set(dt.month for dt, r in parsed_reviews if dt >= recent_cutoff)
    prev_year = max_date.year - 1
    
    # Previous year's counterpart split (e.g. Nov-Dec 2024 vs Jan-Oct 2024)
    prev_year_recent = [r for dt, r in parsed_reviews if dt.year == prev_year and dt.month in recent_months]
    prev_year_historic = [r for dt, r in parsed_reviews if dt.year == prev_year and dt.month not in recent_months]

    # Helper function to compute aspect scores
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

    # Compute scores for all splits
    recent_scores = get_period_aspect_scores(recent_reviews)
    historic_scores = get_period_aspect_scores(historic_reviews)
    prev_recent_scores = get_period_aspect_scores(prev_year_recent)
    prev_historic_scores = get_period_aspect_scores(prev_year_historic)
    
    # 4. Check for quality drops
    anomalies = []
    all_hotels = set(recent_scores.keys()).union(set(historic_scores.keys()))
    
    for hotel_id in all_hotels:
        for aspect in ["Cleanliness", "Service"]:
            h_score = historic_scores.get(hotel_id, {}).get(aspect)
            r_score = recent_scores.get(hotel_id, {}).get(aspect)
            
            if h_score is not None and r_score is not None and h_score > 0:
                drop_ratio = (r_score - h_score) / h_score
                if drop_ratio < threshold:
                    # Check if this drop is seasonal (existed in previous year counterpart months)
                    prev_h = prev_historic_scores.get(hotel_id, {}).get(aspect)
                    prev_r = prev_recent_scores.get(hotel_id, {}).get(aspect)
                    
                    is_seasonal = False
                    if prev_h is not None and prev_r is not None and prev_h > 0:
                        prev_drop = (prev_r - prev_h) / prev_h
                        # If counterpart months in 2024 also had a drop of >15%, treat as seasonal drift
                        if prev_drop < -0.15:
                            is_seasonal = True
                            
                    if not is_seasonal:
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

def analyze_seasonal_trends(reviews: list[dict]) -> dict:
    """
    Groups reviews by hotel, calculates monthly aspect averages, and evaluates
    if seasonality exists for the hotel. Generates a natural language explanation
    pinpointing the aspect, peak/off-peak months, evidence quotes, and geographical context.
    
    Returns:
        dict: { hotel_id: { "seasonal_aspect": str, "explanation": str, ... } }
    """
    hotel_reviews = {}
    for r in reviews:
        hotel_id = r["hotel_id"]
        if hotel_id not in hotel_reviews:
            hotel_reviews[hotel_id] = []
        hotel_reviews[hotel_id].append(r)
        
    trends = {}
    
    for hotel_id, r_list in hotel_reviews.items():
        hotel_name = r_list[0].get("hotel_name", "Unknown Hotel")
        city = get_hotel_city(hotel_name)
        profile = CITY_PROFILES.get(city, {"zone": "Unknown", "desc": "General local weather conditions apply."})
        
        # Aggregate aspect counts by calendar month (1 to 12)
        # Structure: { aspect: { month: { "pos": 0, "neg": 0 } } }
        aspect_monthly = {aspect: {m: {"pos": 0, "neg": 0} for m in range(1, 13)} for aspect in ASPECTS}
        neg_sentences = {aspect: {m: [] for m in range(1, 13)} for aspect in ASPECTS}
        
        for r in r_list:
            try:
                dt = datetime.strptime(r["review_date"], "%Y-%m-%d")
                month = dt.month
            except (ValueError, KeyError):
                continue
                
            sentences = segment_sentences(r["review_text"])
            for sentence in sentences:
                res = sentiment_engine.extract_sentence_aspect_sentiment(sentence)
                aspect = res["aspect"]
                sentiment = res["sentiment"]
                if aspect in ASPECTS and sentiment != 0:
                    if sentiment == 1:
                        aspect_monthly[aspect][month]["pos"] += 1
                    elif sentiment == -1:
                        aspect_monthly[aspect][month]["neg"] += 1
                        neg_sentences[aspect][month].append(sentence)

        # Calculate scores and find the aspect with the maximum variance
        seasonal_aspect = None
        max_variance = -1.0
        aspect_scores = {}
        
        for aspect in ASPECTS:
            aspect_scores[aspect] = {}
            scores_list = []
            for month in range(1, 13):
                pos = aspect_monthly[aspect][month]["pos"]
                neg = aspect_monthly[aspect][month]["neg"]
                total = pos + neg
                if total > 0:
                    score = 3.0 + 2.0 * ((pos - neg) / total)
                    aspect_scores[aspect][month] = round(score, 2)
                    scores_list.append(score)
                else:
                    aspect_scores[aspect][month] = None
                    
            valid_scores = [s for s in scores_list if s is not None]
            if len(valid_scores) >= 4:  # Require at least 4 months of data to compute variance
                variance = max(valid_scores) - min(valid_scores)
                if variance > max_variance:
                    max_variance = variance
                    seasonal_aspect = aspect
                    
        # Check if seasonality is significant (variance threshold = 0.40)
        if seasonal_aspect and max_variance > 0.40:
            valid_scores = [aspect_scores[seasonal_aspect][m] for m in range(1, 13) if aspect_scores[seasonal_aspect][m] is not None]
            valid_months_scores = [(m, aspect_scores[seasonal_aspect][m]) for m in range(1, 13) if aspect_scores[seasonal_aspect][m] is not None]
            valid_months_scores.sort(key=lambda x: x[1])
            
            # Identify top 3 and bottom 3 months
            off_peak_months = [m for m, s in valid_months_scores[:3]]
            peak_months = [m for m, s in valid_months_scores[-3:]]
            
            # Find the most common complaints (negative sentences) in off-peak months
            off_peak_neg = []
            for m in off_peak_months:
                off_peak_neg.extend(neg_sentences[seasonal_aspect][m])
                
            from collections import Counter
            common_neg = [item[0] for item in Counter(off_peak_neg).most_common(2)]
            
            month_names = {
                1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June",
                7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December"
            }
            
            peak_names = ", ".join([month_names[m] for m in peak_months])
            off_peak_names = ", ".join([month_names[m] for m in off_peak_months])
            
            neg_evidence = ""
            if common_neg:
                quotes = " and ".join([f'"{q}"' for q in common_neg])
                neg_evidence = f" Review feedback in low months highlights issues such as: {quotes}."
                
            explanation = (
                f"{seasonal_aspect} scores for this hotel exhibit clear seasonality, peaking in {peak_names} "
                f"and dipping in {off_peak_names}.{neg_evidence} This pattern aligns with "
                f"{city}'s seasonality: {profile['desc']}"
            )
            
            trends[hotel_id] = {
                "seasonal_aspect": seasonal_aspect,
                "peak_months": peak_months,
                "off_peak_months": off_peak_months,
                "max_score": round(max(valid_scores), 2),
                "min_score": round(min(valid_scores), 2),
                "variance": round(max_variance, 2),
                "explanation": explanation
            }
        else:
            trends[hotel_id] = {
                "seasonal_aspect": None,
                "explanation": f"No strong seasonal fluctuations detected. Ratings for this hotel remain stable throughout the year, matching {city}'s general climate profile."
            }
            
    return trends

def calculate_trust_indices(reviews: list[dict]) -> dict:
    """
    Calculates a verifiability Trust Index score (from 0.0 to 1.0) for each hotel based on:
    1. The ratio of verified purchases.
    2. Consistency (rating difference) between verified and unverified ratings.
    
    Formula:
        Trust Index = 0.5 * Verified_Ratio + 0.5 * (1.0 - Rating_Discrepancy / 4.0)
    """
    if not reviews:
        return {}
        
    hotel_groups = {}
    for r in reviews:
        hotel_id = r["hotel_id"]
        if hotel_id not in hotel_groups:
            hotel_groups[hotel_id] = []
        hotel_groups[hotel_id].append(r)
        
    trust_indices = {}
    for hotel_id, r_list in hotel_groups.items():
        total_count = len(r_list)
        if total_count == 0:
            trust_indices[hotel_id] = 1.0
            continue
            
        verified_count = 0
        verified_ratings = []
        unverified_ratings = []
        
        for r in r_list:
            v_val = r.get("verified")
            is_verified = False
            if isinstance(v_val, bool):
                is_verified = v_val
            elif isinstance(v_val, str):
                is_verified = v_val.lower() in ["true", "yes", "1"]
            elif isinstance(v_val, (int, float)):
                is_verified = bool(v_val)
                
            rating = float(r["rating"])
            
            if is_verified:
                verified_count += 1
                verified_ratings.append(rating)
            else:
                unverified_ratings.append(rating)
                
        # 1. Verified Ratio
        verified_ratio = verified_count / total_count
        
        # 2. Rating Discrepancy
        if verified_ratings and unverified_ratings:
            avg_verified = sum(verified_ratings) / len(verified_ratings)
            avg_unverified = sum(unverified_ratings) / len(unverified_ratings)
            discrepancy = abs(avg_verified - avg_unverified)
        else:
            # If we don't have reviews in both groups, there's no discrepancy to penalize
            discrepancy = 0.0
            
        # 3. Combine scores
        # Max discrepancy is 4.0 (5.0 - 1.0)
        consistency_score = 1.0 - (discrepancy / 4.0)
        
        trust_score = 0.5 * verified_ratio + 0.5 * consistency_score
        
        # Clamp and round
        trust_indices[hotel_id] = round(max(0.0, min(1.0, trust_score)), 2)
        
    return trust_indices
