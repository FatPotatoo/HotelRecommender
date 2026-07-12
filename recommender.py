import json
import re
import sentiment_engine
import data_processor

# Predefined traveler archetypes and their curated aspect weights (summing to 1.0)
ARCHETYPES = {
    "Mobility-Needs": {
        "desc": "Traveler with mobility needs, requires helpful, attentive staff and full step-free accessibility.",
        "weights": {"Accessibility": 0.7, "Location": 0.15, "Service": 0.15, "Cleanliness": 0.0, "Value": 0.0, "WiFi/Quietness": 0.0, "Family-Friendliness": 0.0}
    },
    "Business": {
        "desc": "Corporate road-warrior, frequent business traveler, remote worker or long-stay freelancer, needs rock-solid WiFi, workspace, quiet room for calls, and central location near the office district.",
        "weights": {"WiFi/Quietness": 0.6, "Location": 0.3, "Value": 0.1, "Cleanliness": 0.0, "Service": 0.0, "Accessibility": 0.0, "Family-Friendliness": 0.0}
    },
    "Family": {
        "desc": "Family with children, parents traveling with toddlers, values connecting rooms, clean, spacious rooms, family-friendly facilities and pool.",
        "weights": {"Family-Friendliness": 0.7, "Value": 0.2, "Cleanliness": 0.1, "Service": 0.0, "Location": 0.0, "Accessibility": 0.0, "WiFi/Quietness": 0.0}
    },
    "Budget": {
        "desc": "Budget backpacker, shoestring traveler, tight budget, value is everything, loves local culture cheaply, open to multi-city routing to save money.",
        "weights": {"Value": 0.7, "Location": 0.2, "Service": 0.1, "Cleanliness": 0.0, "Accessibility": 0.0, "WiFi/Quietness": 0.0, "Family-Friendliness": 0.0}
    },
    "Luxury": {
        "desc": "Discerning traveler expecting luxury, privacy and refinement, wants a world-class spa, expects impeccable five-star service, budget is no object.",
        "weights": {"Service": 0.6, "Cleanliness": 0.2, "Location": 0.2, "Value": 0.0, "Accessibility": 0.0, "WiFi/Quietness": 0.0, "Family-Friendliness": 0.0}
    },
    "Wellness": {
        "desc": "Guest on a self-care retreat, solo wellness traveler, seeking a spa and wellness retreat, values spotless cleanliness.",
        "weights": {"Cleanliness": 0.5, "Service": 0.4, "WiFi/Quietness": 0.1, "Location": 0.0, "Value": 0.0, "Accessibility": 0.0, "Family-Friendliness": 0.0}
    },
    "Solo-Traveler": {
        "desc": "Solo traveler, solo female traveler, safety-conscious, wants a central, walkable, and safe neighborhood base.",
        "weights": {"Location": 0.6, "WiFi/Quietness": 0.2, "Value": 0.2, "Cleanliness": 0.0, "Service": 0.0, "Accessibility": 0.0, "Family-Friendliness": 0.0}
    },
    "Foodie": {
        "desc": "Culinary traveler, avid foodie, food-and-wine enthusiast, wants to be central to the restaurant scene, chasing great food and local dining.",
        "weights": {"Location": 0.5, "Service": 0.3, "Value": 0.2, "Cleanliness": 0.0, "Accessibility": 0.0, "WiFi/Quietness": 0.0, "Family-Friendliness": 0.0}
    },
    "Beach-Holiday": {
        "desc": "Couple looking for beach breaks, beach-holiday traveler, sun-seeker, direct beach access, coastal relaxation, would love a spa to unwind, prefers direct flights.",
        "weights": {"Location": 0.6, "Service": 0.3, "Cleanliness": 0.1, "Value": 0.0, "Accessibility": 0.0, "WiFi/Quietness": 0.0, "Family-Friendliness": 0.0}
    },
    "Remote-Worker": {
        "desc": "Digital nomad needing fast WiFi, workspace, and quiet room for calls.",
        "weights": {"WiFi/Quietness": 0.7, "Value": 0.2, "Location": 0.1, "Cleanliness": 0.0, "Service": 0.0, "Accessibility": 0.0, "Family-Friendliness": 0.0}
    },
    "Group-Leisure": {
        "desc": "Bachelor/bachelorette group, group of friends on a city break, fine with multi-city legs, wants to be central to the action, near nightlife and bars, splitting costs so value matters.",
        "weights": {"Value": 0.4, "Location": 0.4, "Service": 0.2, "Cleanliness": 0.0, "Accessibility": 0.0, "WiFi/Quietness": 0.0, "Family-Friendliness": 0.0}
    },
    "Romantic": {
        "desc": "Honeymooning couple on a romantic getaway, wants a spa and wellness facilities, appreciates attentive personal service, prefers a quiet, peaceful room, happy with a higher budget for the right vibe.",
        "weights": {"Service": 0.4, "Cleanliness": 0.3, "WiFi/Quietness": 0.3, "Location": 0.0, "Value": 0.0, "Accessibility": 0.0, "Family-Friendliness": 0.0}
    }
}

_archetype_embeddings = None
_archetype_names = list(ARCHETYPES.keys())

def get_archetype_embeddings():
    """Lazy load and cache embeddings of the 11 archetype descriptions."""
    global _archetype_embeddings
    if _archetype_embeddings is None:
        model = sentiment_engine.get_sentence_transformer()
        descs = [ARCHETYPES[name]["desc"] for name in _archetype_names]
        _archetype_embeddings = model.encode(descs, convert_to_tensor=True)
    return _archetype_embeddings

def extract_user_required_dimensions(desc: str) -> set[str]:
    """Scans the traveler description to extract required dimensions as a set."""
    dims = set()
    desc_clean = desc.lower()
    
    if any(w in desc_clean for w in ["safety", "safe"]):
        dims.add("safety")
    if any(w in desc_clean for w in ["culture", "market"]):
        dims.add("local_culture")
    if any(w in desc_clean for w in ["central", "office district", "walkable"]):
        dims.add("location_central")
    if any(w in desc_clean for w in ["wifi", "internet", "connection"]):
        dims.add("wifi")
    if any(w in desc_clean for w in ["meeting", "workspace", "conference"]):
        dims.add("meeting_space")
    if any(w in desc_clean for w in ["quiet", "peaceful", "noise", "sleep", "sound"]):
        dims.add("quiet_room")
    if any(w in desc_clean for w in ["budget", "cheap", "shoestring", "value", "price"]):
        dims.add("value_for_money")
    if any(w in desc_clean for w in ["luxury", "discerning", "five-star", "refinement", "service"]):
        dims.add("luxury_service")
    if any(w in desc_clean for w in ["spa", "wellness", "massage", "sauna"]):
        dims.add("spa_and_wellness")
    if any(w in desc_clean for w in ["kid", "child", "toddler", "family"]):
        dims.add("family_friendly")
    if "direct flight" in desc_clean:
        dims.add("direct_flights")
    if any(w in desc_clean for w in ["accessibility", "wheelchair", "mobility", "step-free", "handicap", "elevator"]):
        dims.add("accessibility")
    if "pool" in desc_clean:
        dims.add("pool")
        
    return dims

def calculate_review_dimension_score(review: dict, required_dims: set[str]) -> float:
    """Calculates graded score [0, 1] based on overlap and net sentiment of review text and required dimensions."""
    if not required_dims:
        return 1.0
        
    import data_processor
    import sentiment_engine
    
    sentences = data_processor.segment_sentences(review.get("review_text", ""))
    dim_hits = {d: [] for d in required_dims}
    
    for sentence in sentences:
        res = sentiment_engine.extract_sentence_aspect_sentiment(sentence)
        s_text = sentence.lower()
        
        for d in required_dims:
            matched = False
            if d == "safety" and any(w in s_text for w in ["safety", "safe"]):
                matched = True
            elif d == "local_culture" and any(w in s_text for w in ["culture", "market"]):
                matched = True
            elif d == "location_central" and (res["aspect"] == "Location" or any(w in s_text for w in ["central", "walkable"])):
                matched = True
            elif d == "wifi" and (res["aspect"] == "WiFi/Quietness" and any(w in s_text for w in ["wifi", "internet", "connection"])):
                matched = True
            elif d == "meeting_space" and any(w in s_text for w in ["meeting", "workspace", "conference"]):
                matched = True
            elif d == "quiet_room" and (res["aspect"] == "WiFi/Quietness" and any(w in s_text for w in ["quiet", "peaceful", "noise", "sleep", "sound"])):
                matched = True
            elif d == "value_for_money" and (res["aspect"] == "Value" or any(w in s_text for w in ["budget", "cheap", "value", "price"])):
                matched = True
            elif d == "luxury_service" and (res["aspect"] == "Service" or any(w in s_text for w in ["luxury", "five-star", "impeccable", "service"])):
                matched = True
            elif d == "spa_and_wellness" and any(w in s_text for w in ["spa", "wellness", "massage", "sauna"]):
                matched = True
            elif d == "family_friendly" and (res["aspect"] == "Family-Friendliness" or any(w in s_text for w in ["kid", "child", "toddler", "family"])):
                matched = True
            elif d == "direct_flights" and "direct flight" in s_text:
                matched = True
            elif d == "accessibility" and (res["aspect"] == "Accessibility" or any(w in s_text for w in ["accessibility", "wheelchair", "mobility", "step-free", "handicap", "elevator"])):
                matched = True
            elif d == "pool" and "pool" in s_text:
                matched = True
                
            if matched:
                dim_hits[d].append(res["sentiment"])
                
    scores = []
    for d in required_dims:
        hits = dim_hits[d]
        if hits:
            if -1 in hits:
                scores.append(-1.0)
            elif 1 in hits:
                scores.append(1.0)
            else:
                scores.append(0.0)
        else:
            scores.append(0.0)
            
    avg_score = sum(scores) / len(required_dims)
    return max(0.0, min(1.0, (avg_score + 1.0) / 2.0))



def get_user_profiles(profiles_path: str) -> dict:
    """Load and parse traveler profiles from JSON file."""
    with open(profiles_path, "r", encoding="utf-8") as f:
        profiles_list = json.load(f)
    return {p["profile_id"]: p["description"] for p in profiles_list}

def extract_aspect_weights(desc: str) -> dict:
    """
    Classifies a traveler description into aspect weights.
    1. Cosine similarity match against pre-embedded archetypes (> 0.85).
    2. Zero-Shot classification pipeline.
    3. Rule-based keyword count fallback.
    """
    desc_clean = desc.lower()
    
    # Check if accessibility needs to be prioritized
    is_mobility = any(kw in desc_clean for kw in ["wheelchair", "step-free", "mobility", "accessibility", "handicap", "elevator"])
    
    # 1. Cosine similarity against archetypes
    try:
        model = sentiment_engine.get_sentence_transformer()
        from sentence_transformers import util
        import torch
        
        query_emb = model.encode(desc, convert_to_tensor=True)
        arch_embs = get_archetype_embeddings()
        cos_scores = util.cos_sim(query_emb, arch_embs)[0]
        max_idx = torch.argmax(cos_scores).item()
        max_score = cos_scores[max_idx].item()
        
        if max_score > 0.60:
            matched_arch = _archetype_names[max_idx]
            weights = ARCHETYPES[matched_arch]["weights"].copy()
            
            if is_mobility:
                weights["Accessibility"] = max(0.40, weights.get("Accessibility", 0.0))
                total = sum(weights.values())
                weights = {k: v / total for k, v in weights.items()}
            return weights
    except Exception:
        pass
        
    # 2. Zero-Shot classification pipeline
    try:
        classifier = sentiment_engine.get_zero_shot_classifier()
        labels = data_processor.ASPECTS
        res = classifier(desc, candidate_labels=labels)
        raw_weights = {label: score for label, score in zip(res["labels"], res["scores"])}
        
        if is_mobility:
            raw_weights["Accessibility"] = max(0.40, raw_weights.get("Accessibility", 0.0))
            
        total = sum(raw_weights.values())
        weights = {k: round(v / total, 2) for k, v in raw_weights.items()}
        return weights
    except Exception:
        pass
        
    # 3. Rule-based keyword count fallback
    keywords = {
        "Cleanliness": ["clean", "dirty", "spotless", "immaculate", "housekeeping", "hygiene"],
        "Service": ["staff", "service", "team", "host", "receptionist", "spa", "pool", "wellness", "breakfast", "dining", "food", "restaurant", "massage"],
        "Location": ["location", "beach", "walking", "distance", "neighborhood", "view", "central", "sights", "transit", "safe", "secure", "markets", "eateries", "nightlife"],
        "Value": ["value", "price", "budget", "money", "cost", "expensive", "cheap", "affordable", "overpriced", "rate", "billing"],
        "Accessibility": ["accessibility", "wheelchair", "ramp", "lift", "step-free", "handicap", "elevator", "mobility"],
        "WiFi/Quietness": ["wifi", "internet", "connection", "zoom", "call", "noise", "quiet", "soundproofing", "sleep", "construction"],
        "Family-Friendliness": ["family", "kids", "children", "toddler", "baby", "club", "suites", "pool"]
    }
    
    scores = {aspect: 0.05 for aspect in data_processor.ASPECTS}  # Base weight
    for aspect, kws in keywords.items():
        for kw in kws:
            if kw in desc_clean:
                scores[aspect] += 1.0
                
    if is_mobility:
        scores["Accessibility"] = max(2.0, scores["Accessibility"])
        
    total = sum(scores.values())
    weights = {k: round(v / total, 2) for k, v in scores.items()}
    return weights


class Recommender:
    def __init__(self, reviews_path: str, profiles_path: str):
        """Precompute hotel scorecard matrix and load profiles."""
        self.reviews = data_processor.load_data(reviews_path)
        self.profiles = get_user_profiles(profiles_path)
        self.review_embeddings_cache = {}
        
        # Precompute scorecards
        self.scorecard = data_processor.compile_aspect_scorecard(self.reviews)
        
        # Precompute hotel metadata (name, category, overall rating)
        self.hotel_meta = {}
        hotel_total_ratings = {}
        hotel_review_counts = {}
        
        # Track if a hotel has negative accessibility reviews
        # Structure: { hotel_id: count of negative accessibility mentions }
        self.hotel_neg_accessibility = {}
        
        for r in self.reviews:
            hotel_id = r["hotel_id"]
            rating = float(r["rating"])
            
            if hotel_id not in self.hotel_meta:
                self.hotel_meta[hotel_id] = {
                    "hotel_id": hotel_id,
                    "hotel_name": r.get("hotel_name", "Unknown Hotel"),
                    "hotel_category": r.get("hotel_category", "3-star")
                }
                hotel_total_ratings[hotel_id] = 0.0
                hotel_review_counts[hotel_id] = 0
                self.hotel_neg_accessibility[hotel_id] = 0
                
            hotel_total_ratings[hotel_id] += rating
            hotel_review_counts[hotel_id] += 1
            
            # Count negative accessibility mentions for hard filter
            sentences = data_processor.segment_sentences(r["review_text"])
            for sentence in sentences:
                res = sentiment_engine.extract_sentence_aspect_sentiment(sentence)
                if res["aspect"] == "Accessibility" and res["sentiment"] == -1:
                    self.hotel_neg_accessibility[hotel_id] += 1
                    
        # Compute average overall ratings
        self.hotel_avg_ratings = {}
        for hotel_id, total in hotel_total_ratings.items():
            count = hotel_review_counts[hotel_id]
            self.hotel_avg_ratings[hotel_id] = round(total / count, 2) if count > 0 else 3.0

    def get_recommendations(self, profile_id_or_desc: str, top_n: int = 5) -> list[dict]:
        """
        Ranks hotels using a blended MCDA score:
        Final Score = 0.8 * (weighted aspects) + 0.2 * overall_rating
        Applies a penalty of 2.5 points if a mobility user chooses a hotel with negative accessibility mentions.
        """
        # 1. Resolve traveler description
        if profile_id_or_desc in self.profiles:
            desc = self.profiles[profile_id_or_desc]
        else:
            desc = profile_id_or_desc
            
        # 2. Extract weights
        weights = extract_aspect_weights(desc)
        
        # Check mobility constraint
        is_mobility_profile = any(kw in desc.lower() for kw in ["wheelchair", "step-free", "mobility", "accessibility", "handicap", "elevator"])
        
        # 3. Calculate match scores for all hotels
        hotel_scores = []
        for hotel_id, aspect_scores in self.scorecard.items():
            meta = self.hotel_meta[hotel_id]
            avg_rating = self.hotel_avg_ratings[hotel_id]
            
            # A. Aspect-specific utility score
            aspect_utility = 0.0
            for aspect, weight in weights.items():
                aspect_utility += aspect_scores.get(aspect, 3.0) * weight
                
            # B. Blended final score (80% aspect match + 20% overall reputation)
            final_score = 0.80 * aspect_utility + 0.20 * avg_rating
            
            applied_penalty = 0.0
            
            # C. Apply baseline quality penalty for aspect ratings below 2.5
            # Exclude Accessibility and Family-Friendliness from general penalties
            quality_penalty = 0.0
            for aspect, score in aspect_scores.items():
                if aspect in ["Accessibility", "Family-Friendliness"]:
                    continue
                if score is not None and score < 2.5:
                    quality_penalty += 1.5 * (2.5 - score)
            if quality_penalty > 0:
                final_score -= quality_penalty
                applied_penalty += quality_penalty
            
            # D. Apply accessibility penalty if applicable
            has_negative_access = self.hotel_neg_accessibility.get(hotel_id, 0) > 0
            if is_mobility_profile and has_negative_access:
                final_score -= 2.50
                applied_penalty += 2.50
                
            hotel_scores.append({
                "hotel_id": hotel_id,
                "hotel_name": meta["hotel_name"],
                "hotel_category": meta["hotel_category"],
                "match_score": round(max(1.0, min(5.0, final_score)), 2),
                "aspect_scores": aspect_scores,
                "overall_rating": avg_rating,
                "applied_penalty": round(applied_penalty, 2)
            })
            
        # Sort descending by match score, secondary sorting by overall rating
        hotel_scores.sort(key=lambda x: (x["match_score"], x["overall_rating"]), reverse=True)
        recommended = hotel_scores[:top_n]
        
        # 4. Fetch Evidence Citations using Structured RAG
        required_dims = extract_user_required_dimensions(desc)
        
        # Precompute query embedding for vector similarity ranking
        try:
            model = sentiment_engine.get_sentence_transformer()
            query_emb = model.encode(desc, convert_to_tensor=True)
            from sentence_transformers import util
            import torch
        except Exception:
            model = None
            
        for rec in recommended:
            hotel_id = rec["hotel_id"]
            hotel_reviews = [r for r in self.reviews if r["hotel_id"] == hotel_id]
            
            # Precompute hotel-specific date bounds for freshness normalization
            from datetime import datetime
            hotel_dates = []
            for r in hotel_reviews:
                try:
                    hotel_dates.append(datetime.strptime(r["review_date"], "%Y-%m-%d"))
                except Exception:
                    pass
            if hotel_dates:
                min_date = min(hotel_dates)
                max_date = max(hotel_dates)
                total_days = (max_date - min_date).days
            else:
                min_date = max_date = None
                total_days = 0
            
            # B. Scorer (Vector Search Similarity + Traveler Type + Freshness + Positive Sentiment)
            scored_candidates = []
            
            if model is not None and hotel_reviews:
                try:
                    # Find which review IDs are not in cache
                    uncached_reviews = [r for r in hotel_reviews if r["review_id"] not in self.review_embeddings_cache]
                    if uncached_reviews:
                        uncached_texts = [r["review_text"] for r in uncached_reviews]
                        uncached_embs = model.encode(uncached_texts, convert_to_tensor=True)
                        for idx, r in enumerate(uncached_reviews):
                            self.review_embeddings_cache[r["review_id"]] = uncached_embs[idx]
                            
                    # Load embeddings from cache and stack
                    import torch
                    review_embs = torch.stack([self.review_embeddings_cache[r["review_id"]] for r in hotel_reviews])
                    
                    cos_scores = util.cos_sim(query_emb, review_embs)[0]
                    for idx, r in enumerate(hotel_reviews):
                        sim_score = max(0.0, min(1.0, cos_scores[idx].item()))
                        
                        # Traveler type matching score (set-based Jaccard similarity)
                        dimension_match_score = calculate_review_dimension_score(r, required_dims)
                        
                        # Freshness score
                        try:
                            r_date = datetime.strptime(r["review_date"], "%Y-%m-%d")
                            freshness = (r_date - min_date).days / total_days if total_days > 0 else 1.0
                        except Exception:
                            freshness = 1.0
                            
                        # Positive sentiment ratio score
                        sentences = data_processor.segment_sentences(r["review_text"])
                        pos_count = sum(1 for s in sentences if sentiment_engine.extract_sentence_aspect_sentiment(s)["sentiment"] == 1)
                        pos_sentiment_score = pos_count / len(sentences) if sentences else 0.0
                        
                        final_score = (
                            0.50 * sim_score +
                            0.25 * dimension_match_score +
                            0.15 * freshness +
                            0.10 * pos_sentiment_score
                        )
                        scored_candidates.append((r, final_score))
                except Exception:
                    for r in hotel_reviews:
                        sim_score = (float(r["rating"]) - 1.0) / 4.0
                        dimension_match_score = calculate_review_dimension_score(r, required_dims)
                        try:
                            r_date = datetime.strptime(r["review_date"], "%Y-%m-%d")
                            freshness = (r_date - min_date).days / total_days if total_days > 0 else 1.0
                        except Exception:
                            freshness = 1.0
                        sentences = data_processor.segment_sentences(r["review_text"])
                        pos_count = sum(1 for s in sentences if sentiment_engine.extract_sentence_aspect_sentiment(s)["sentiment"] == 1)
                        pos_sentiment_score = pos_count / len(sentences) if sentences else 0.0
                        
                        final_score = (
                            0.50 * sim_score +
                            0.25 * dimension_match_score +
                            0.15 * freshness +
                            0.10 * pos_sentiment_score
                        )
                        scored_candidates.append((r, final_score))
            else:
                for r in hotel_reviews:
                    sim_score = (float(r["rating"]) - 1.0) / 4.0
                    dimension_match_score = calculate_review_dimension_score(r, required_dims)
                    try:
                        r_date = datetime.strptime(r["review_date"], "%Y-%m-%d")
                        freshness = (r_date - min_date).days / total_days if total_days > 0 else 1.0
                    except Exception:
                        freshness = 1.0
                    sentences = data_processor.segment_sentences(r["review_text"])
                    pos_count = sum(1 for s in sentences if sentiment_engine.extract_sentence_aspect_sentiment(s)["sentiment"] == 1)
                    pos_sentiment_score = pos_count / len(sentences) if sentences else 0.0
                    
                    final_score = (
                        0.50 * sim_score +
                        0.25 * dimension_match_score +
                        0.15 * freshness +
                        0.10 * pos_sentiment_score
                    )
                    scored_candidates.append((r, final_score))
                    
            scored_candidates.sort(key=lambda x: x[1], reverse=True)
            
            # Select top 3 citations
            citations = []
            for r, score in scored_candidates[:3]:
                citations.append({
                    "review_id": r["review_id"],
                    "text": r["review_text"]
                })
                
            rec["evidence"] = citations
            
        return recommended
