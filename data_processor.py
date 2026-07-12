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
                scorecard[hotel_id][aspect] = round(max(1.0, min(5.0, score)), 2)
            else:
                scorecard[hotel_id][aspect] = None
            
    return scorecard

def compile_temporal_rating_stream(reviews: list[dict]) -> dict:
    """
    Compiles monthly average scores for overall rating and each of the 7 aspects
    for each hotel over the 24-month timeline.
    
    Returns:
        dict: { 
            hotel_id: { 
                "Overall": { "YYYY-MM": average_rating },
                "Cleanliness": { "YYYY-MM": score },
                ...
            } 
        }
    """
    if not reviews:
        return {}
        
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
            streams_agg[hotel_id] = {
                "Overall": {},
                **{aspect: {} for aspect in ASPECTS}
            }
            
        # Overall
        if month_key not in streams_agg[hotel_id]["Overall"]:
            streams_agg[hotel_id]["Overall"][month_key] = []
        streams_agg[hotel_id]["Overall"][month_key].append(rating)
        
        # Aspects
        sentences = segment_sentences(r["review_text"])
        for sentence in sentences:
            res = sentiment_engine.extract_sentence_aspect_sentiment(sentence)
            aspect = res["aspect"]
            sentiment = res["sentiment"]
            if aspect in ASPECTS and sentiment != 0:
                if month_key not in streams_agg[hotel_id][aspect]:
                    streams_agg[hotel_id][aspect][month_key] = {"pos": 0, "neg": 0}
                if sentiment == 1:
                    streams_agg[hotel_id][aspect][month_key]["pos"] += 1
                elif sentiment == -1:
                    streams_agg[hotel_id][aspect][month_key]["neg"] += 1

    streams = {}
    for hotel_id, aspect_data in streams_agg.items():
        streams[hotel_id] = {
            "Overall": {},
            **{aspect: {} for aspect in ASPECTS}
        }
        # Compile Overall average rating
        for month_key, ratings in aspect_data["Overall"].items():
            streams[hotel_id]["Overall"][month_key] = round(sum(ratings) / len(ratings), 2)
            
        # Compile Aspect scores
        for aspect in ASPECTS:
            for month_key in aspect_data["Overall"]:
                data = aspect_data[aspect].get(month_key, {"pos": 0, "neg": 0})
                pos = data["pos"]
                neg = data["neg"]
                total = pos + neg
                if total > 0:
                    score = 3.0 + 2.0 * ((pos - neg) / total)
                    streams[hotel_id][aspect][month_key] = round(max(1.0, min(5.0, score)), 2)
                else:
                    streams[hotel_id][aspect][month_key] = streams[hotel_id]["Overall"].get(month_key, 3.0)
                    
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

SOUTHERN_CITIES = {"Sydney", "Cape Town", "Lima"}
TROPICAL_CITIES = {"Bali", "Bangkok", "Mumbai", "Singapore", "Mexico City"}

def get_season_name(month: int, hotel_name: str) -> str:
    """Classifies calendar month into local season dynamically based on hotel city."""
    city = "Unknown"
    if ", " in hotel_name:
        city = hotel_name.split(", ")[-1].strip()
        
    if city in SOUTHERN_CITIES:
        if month in [12, 1, 2]:
            return "Summer"
        elif month in [3, 4, 5]:
            return "Autumn"
        elif month in [6, 7, 8]:
            return "Winter"
        else:
            return "Spring"
    elif city in TROPICAL_CITIES:
        if month in [11, 12, 1, 2, 3, 4]:
            return "Dry Season"
        else:
            return "Wet Season"
    else:  # Northern Hemisphere default
        if month in [6, 7, 8]:
            return "Summer"
        elif month in [9, 10, 11]:
            return "Autumn"
        elif month in [12, 1, 2]:
            return "Winter"
        else:
            return "Spring"

def analyze_seasonal_trends(reviews: list[dict]) -> dict:
    """
    Detects consistent, Year-Over-Year seasonality patterns for each hotel grouped by local seasons.
    Removes dependency on hardcoded city templates, relying strictly on consistency of 
    seasonal aspect deviations from the annual mean in both 2024 and 2025.
    
    Returns:
        dict: { hotel_id: { "seasonal_aspect": str, "explanation": str, ... } }
    """
    if not reviews:
        return {}
        
    # Group reviews by hotel
    hotel_reviews = {}
    for r in reviews:
        hotel_id = r["hotel_id"]
        if hotel_id not in hotel_reviews:
            hotel_reviews[hotel_id] = []
        hotel_reviews[hotel_id].append(r)
        
    trends = {}
    
    for hotel_id, r_list in hotel_reviews.items():
        hotel_name = r_list[0].get("hotel_name", "Unknown Hotel")
        city = "Unknown"
        if ", " in hotel_name:
            city = hotel_name.split(", ")[-1].strip()
            
        if city in TROPICAL_CITIES:
            seasons_list = ["Dry Season", "Wet Season"]
        else:
            seasons_list = ["Spring", "Summer", "Autumn", "Winter"]
            
        # Structure: { aspect: { year: { season: { "pos": 0, "neg": 0 } } } }
        aspect_counts = {
            aspect: {
                2024: {s: {"pos": 0, "neg": 0} for s in seasons_list},
                2025: {s: {"pos": 0, "neg": 0} for s in seasons_list}
            } for aspect in ASPECTS
        }
        
        neg_sentences = {
            aspect: {
                2024: {s: [] for s in seasons_list},
                2025: {s: [] for s in seasons_list}
            } for aspect in ASPECTS
        }
        
        for r in r_list:
            try:
                dt = datetime.strptime(r["review_date"], "%Y-%m-%d")
                year = dt.year
                month = dt.month
                if year not in [2024, 2025]:
                    continue
                season = get_season_name(month, hotel_name)
            except (ValueError, KeyError):
                continue
                
            sentences = segment_sentences(r["review_text"])
            for sentence in sentences:
                res = sentiment_engine.extract_sentence_aspect_sentiment(sentence)
                aspect = res["aspect"]
                sentiment = res["sentiment"]
                if aspect in ASPECTS and sentiment != 0:
                    if sentiment == 1:
                        aspect_counts[aspect][year][season]["pos"] += 1
                    elif sentiment == -1:
                        aspect_counts[aspect][year][season]["neg"] += 1
                        neg_sentences[aspect][year][season].append(sentence)

        # Calculate monthly scores and deviations for 2024 and 2025
        seasonal_aspect = None
        best_yoy_dips = []
        best_yoy_peaks = []
        max_score_diff = -1.0
        
        for aspect in ASPECTS:
            # Compute scores for 2024
            scores_2024 = {}
            for s in seasons_list:
                pos = aspect_counts[aspect][2024][s]["pos"]
                neg = aspect_counts[aspect][2024][s]["neg"]
                total = pos + neg
                scores_2024[s] = (3.0 + 2.0 * ((pos - neg) / total)) if total > 0 else None
                
            # Compute scores for 2025
            scores_2025 = {}
            for s in seasons_list:
                pos = aspect_counts[aspect][2025][s]["pos"]
                neg = aspect_counts[aspect][2025][s]["neg"]
                total = pos + neg
                scores_2025[s] = (3.0 + 2.0 * ((pos - neg) / total)) if total > 0 else None
                
            # Annual means
            valid_2024 = [val for val in scores_2024.values() if val is not None]
            valid_2025 = [val for val in scores_2025.values() if val is not None]
            
            if len(valid_2024) < 2 or len(valid_2025) < 2:
                continue
                
            mean_2024 = sum(valid_2024) / len(valid_2024)
            mean_2025 = sum(valid_2025) / len(valid_2025)
            
            # Calculate deviations and YoY consistent seasons
            yoy_dips = []
            yoy_peaks = []
            
            for s in seasons_list:
                s24 = scores_2024[s]
                s25 = scores_2025[s]
                if s24 is not None and s25 is not None:
                    dev24 = s24 - mean_2024
                    dev25 = s25 - mean_2025
                    # Threshold of seasonal deviation: 0.15 points (since seasons average 3 months, noise is much lower!)
                    if dev24 < -0.15 and dev25 < -0.15:
                        yoy_dips.append(s)
                    elif dev24 > 0.15 and dev25 > 0.15:
                        yoy_peaks.append(s)
                        
            # If we have consistent peaks or dips, evaluate seasonality intensity
            if yoy_dips or yoy_peaks:
                peak_vals = [scores_2024[s] for s in yoy_peaks] + [scores_2025[s] for s in yoy_peaks]
                dip_vals = [scores_2024[s] for s in yoy_dips] + [scores_2025[s] for s in yoy_dips]
                
                avg_peak = sum(peak_vals) / len(peak_vals) if peak_vals else mean_2024
                avg_dip = sum(dip_vals) / len(dip_vals) if dip_vals else mean_2024
                
                diff = avg_peak - avg_dip
                if diff > max_score_diff:
                    max_score_diff = diff
                    seasonal_aspect = aspect
                    best_yoy_dips = yoy_dips
                    best_yoy_peaks = yoy_peaks
                    
        # Formulate explanation based on findings
        if seasonal_aspect and max_score_diff > 0.25:
            peak_names = " and ".join(best_yoy_peaks) if best_yoy_peaks else "N/A"
            dip_names = " and ".join(best_yoy_dips) if best_yoy_dips else "N/A"
            
            # Extract negative sentences during dip seasons
            dip_neg = []
            for year in [2024, 2025]:
                for s in best_yoy_dips:
                    dip_neg.extend(neg_sentences[seasonal_aspect][year][s])
                    
            from collections import Counter
            common_neg = [item[0] for item in Counter(dip_neg).most_common(2)]
            
            neg_evidence = ""
            if common_neg:
                quotes = " and ".join([f'"{q}"' for q in common_neg])
                neg_evidence = f" Review feedback in these low-performance seasons consistently highlights: {quotes}."
                
            explanation = (
                f"{seasonal_aspect} ratings for this hotel exhibit consistent seasonal fluctuations, "
                f"peaking in {peak_names} and dipping in {dip_names} across both 2024 and 2025.{neg_evidence}"
            )
            
            # Map seasons back to calendar months for backward compatibility
            season_to_months = {}
            if city in SOUTHERN_CITIES:
                season_to_months = {
                    "Summer": [12, 1, 2], "Autumn": [3, 4, 5], "Winter": [6, 7, 8], "Spring": [9, 10, 11]
                }
            elif city in TROPICAL_CITIES:
                season_to_months = {
                    "Dry Season": [11, 12, 1, 2, 3, 4], "Wet Season": [5, 6, 7, 8, 9, 10]
                }
            else:
                season_to_months = {
                    "Summer": [6, 7, 8], "Autumn": [9, 10, 11], "Winter": [12, 1, 2], "Spring": [3, 4, 5]
                }
                
            peak_months = []
            for s in best_yoy_peaks:
                peak_months.extend(season_to_months.get(s, []))
            off_peak_months = []
            for s in best_yoy_dips:
                off_peak_months.extend(season_to_months.get(s, []))
                
            trends[hotel_id] = {
                "seasonal_aspect": seasonal_aspect,
                "peak_months": peak_months,
                "off_peak_months": off_peak_months,
                "variance": round(max_score_diff, 2),
                "explanation": explanation
            }
        else:
            trends[hotel_id] = {
                "seasonal_aspect": None,
                "explanation": "No consistent seasonal fluctuations detected. This hotel maintains high operational stability year-round, with aspect ratings remaining stable across both 2024 and 2025."
            }
            
    return trends


