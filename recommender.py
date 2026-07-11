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
        # Identify core aspects the user cares about (weight > 0.15)
        core_aspects = [aspect for aspect, w in weights.items() if w > 0.15]
        
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
            
            # A. Structured Filter: keep reviews that contain positive mentions of core aspects
            candidate_reviews = []
            for r in hotel_reviews:
                match_count = 0
                sentences = data_processor.segment_sentences(r["review_text"])
                for sentence in sentences:
                    res = sentiment_engine.extract_sentence_aspect_sentiment(sentence)
                    if res["aspect"] in core_aspects and res["sentiment"] == 1:
                        match_count += 1
                if match_count > 0:
                    candidate_reviews.append((r, match_count))
                    
            # Sort candidates by match intensity and review rating first
            candidate_reviews.sort(key=lambda x: (x[1], float(x[0]["rating"])), reverse=True)
            
            # Slice to only the top 15 candidates for vector search
            candidate_reviews = [r for r, count in candidate_reviews[:15]]
            
            # Fallback if no reviews matched the positive aspect filter
            if not candidate_reviews:
                candidate_reviews = hotel_reviews
                
            # B. Semantic Ranker (Vector Search + Review Rating)
            scored_candidates = []
            if model is not None and candidate_reviews:
                try:
                    # Find which review IDs are not in cache
                    uncached_reviews = [r for r in candidate_reviews if r["review_id"] not in self.review_embeddings_cache]
                    if uncached_reviews:
                        uncached_texts = [r["review_text"] for r in uncached_reviews]
                        uncached_embs = model.encode(uncached_texts, convert_to_tensor=True)
                        for idx, r in enumerate(uncached_reviews):
                            self.review_embeddings_cache[r["review_id"]] = uncached_embs[idx]
                            
                    # Load embeddings from cache and stack
                    import torch
                    review_embs = torch.stack([self.review_embeddings_cache[r["review_id"]] for r in candidate_reviews])
                    
                    cos_scores = util.cos_sim(query_emb, review_embs)[0]
                    for idx, r in enumerate(candidate_reviews):
                        sim_score = cos_scores[idx].item()
                        # Normalize rating to [0, 1] range
                        rating_val = (float(r["rating"]) - 1.0) / 4.0
                        blended_score = 0.70 * sim_score + 0.30 * rating_val
                        scored_candidates.append((r, blended_score))
                except Exception:
                    for r in candidate_reviews:
                        scored_candidates.append((r, float(r["rating"])))
            else:
                for r in candidate_reviews:
                    scored_candidates.append((r, float(r["rating"])))
                    
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
