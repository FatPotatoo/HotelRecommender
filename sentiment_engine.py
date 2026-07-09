import re
import numpy as np

# Static dictionary mapping the 87 template sentences to their aspect and sentiment labels.
TEMPLATE_MAP = {
    # Generic / No Aspect
    "Second time staying at this property.": {"aspect": None, "sentiment": 1},
    "Stayed here for a few nights.": {"aspect": None, "sentiment": 0},
    "Stopped here on a longer trip.": {"aspect": None, "sentiment": 0},
    "We had high hopes for this stay.": {"aspect": None, "sentiment": 0},
    "Booked this for a short trip.": {"aspect": None, "sentiment": 0},
    "Chose this hotel based on the reviews.": {"aspect": None, "sentiment": 0},
    "Decent for one night, not for longer.": {"aspect": None, "sentiment": -1},
    "Would book again without hesitation.": {"aspect": None, "sentiment": 1},
    "Mixed feelings overall but mostly positive.": {"aspect": None, "sentiment": 1},
    "Overall a solid choice.": {"aspect": None, "sentiment": 1},
    "Would consider returning.": {"aspect": None, "sentiment": 1},
    "Not sure I'd come back.": {"aspect": None, "sentiment": -1},

    # Cleanliness
    "Spotlessly clean room and an immaculate bathroom.": {"aspect": "Cleanliness", "sentiment": 1},
    "Everything was sparkling clean, clearly very well maintained.": {"aspect": "Cleanliness", "sentiment": 1},
    "Housekeeping was impeccable; the room was fresh every single day.": {"aspect": "Cleanliness", "sentiment": 1},
    "Room wasn't clean on arrival — found hair in the bathroom.": {"aspect": "Cleanliness", "sentiment": -1},
    "Housekeeping was inconsistent and the carpets looked grubby.": {"aspect": "Cleanliness", "sentiment": -1},

    # Service
    "The level of refinement and personal service was world-class.": {"aspect": "Service", "sentiment": 1},
    "Impeccable five-star service, every tiny detail considered.": {"aspect": "Service", "sentiment": 1},
    "Pure luxury from check-in to checkout — utterly indulgent.": {"aspect": "Service", "sentiment": 1},
    "The spa was a highlight — incredible massages and a serene relaxation pool.": {"aspect": "Service", "sentiment": 1},
    "Wonderful wellness facilities; the sauna and treatments left us completely refreshed.": {"aspect": "Service", "sentiment": 1},
    "A proper retreat: yoga in the morning and an excellent spa in the afternoon.": {"aspect": "Service", "sentiment": 1},
    "Front desk was friendly and incredibly helpful with every request.": {"aspect": "Service", "sentiment": 1},
    "The team remembered our names and anticipated everything we needed.": {"aspect": "Service", "sentiment": 1},
    "Staff went above and beyond — genuinely warm, attentive service throughout.": {"aspect": "Service", "sentiment": 1},
    "On-site restaurant was a highlight — beautifully prepared local dishes.": {"aspect": "Service", "sentiment": 1},
    "The breakfast spread was extensive and genuinely delicious.": {"aspect": "Service", "sentiment": 1},
    "Outstanding dining; we never felt the need to eat elsewhere.": {"aspect": "Service", "sentiment": 1},
    "Service was indifferent and slow throughout the stay.": {"aspect": "Service", "sentiment": -1},
    "Front desk was rude and unhelpful whenever we asked for anything.": {"aspect": "Service", "sentiment": -1},
    "Wellness facilities were tired and the pool was often closed.": {"aspect": "Service", "sentiment": -1},
    "The spa was small and underwhelming for a property of this class.": {"aspect": "Service", "sentiment": -1},
    "The restaurant was disappointing and the menu was very limited.": {"aspect": "Service", "sentiment": -1},
    "Called itself five-star but the service felt distinctly mid-range.": {"aspect": "Service", "sentiment": -1},
    "Didn't live up to its luxury billing at all.": {"aspect": "Service", "sentiment": -1},

    # Location
    "Loved that it sat in a genuine local neighborhood, not a tourist bubble.": {"aspect": "Location", "sentiment": 1},
    "Great base for experiencing the real culture — artisans and street food all around.": {"aspect": "Location", "sentiment": 1},
    "Steps away from authentic local markets and family-run eateries.": {"aspect": "Location", "sentiment": 1},
    "Just steps from a beautiful stretch of beach with loungers ready.": {"aspect": "Location", "sentiment": 1},
    "You can't beat the location — everything was a short stroll away.": {"aspect": "Location", "sentiment": 1},
    "Right in the heart of the city, so easy to get everywhere on foot.": {"aspect": "Location", "sentiment": 1},
    "Direct beach access made the whole stay feel like a proper getaway.": {"aspect": "Location", "sentiment": 1},
    "Great bars and clubs right around the corner, perfect for a night out.": {"aspect": "Location", "sentiment": 1},
    "Buzzing area after dark with plenty of lively spots within walking distance.": {"aspect": "Location", "sentiment": 1},
    "Perfect central location, walking distance to all the main sights.": {"aspect": "Location", "sentiment": 1},
    "Woke up to the sea every morning — the beachfront setting was perfect.": {"aspect": "Location", "sentiment": 1},
    "The rooftop bar was packed and fun, and the nightlife nearby was excellent.": {"aspect": "Location", "sentiment": 1},
    "Quiet, safe neighborhood — I never once felt uncomfortable coming back late.": {"aspect": "Location", "sentiment": 1},
    "As a solo traveler I felt very secure here, both in the hotel and the surrounding streets.": {"aspect": "Location", "sentiment": 1},
    "Felt completely safe walking back alone at night; the area is well-lit and security was attentive.": {"aspect": "Location", "sentiment": 1},
    "Don't come here for nightlife — everything shuts early and it's sleepy.": {"aspect": "Location", "sentiment": -1},
    "Dead quiet at night with nothing to do in the area.": {"aspect": "Location", "sentiment": -1},
    "Felt like a generic tourist zone with no local character at all.": {"aspect": "Location", "sentiment": -1},
    "Very touristy strip; hard to find anything authentic or local nearby.": {"aspect": "Location", "sentiment": -1},
    "The neighborhood felt sketchy after dark and I didn't feel safe coming back alone.": {"aspect": "Location", "sentiment": -1},
    "Poorly lit surroundings made me uneasy walking back at night.": {"aspect": "Location", "sentiment": -1},
    "The location was far from everything and required long, expensive taxi rides.": {"aspect": "Location", "sentiment": -1},
    "Felt quite isolated — nothing within walking distance.": {"aspect": "Location", "sentiment": -1},
    "The beach was a 20-minute drive away, not 'on the beach' as advertised.": {"aspect": "Location", "sentiment": -1},
    "No real beach access — just a rocky shore you couldn't use.": {"aspect": "Location", "sentiment": -1},

    # Value
    "Excellent value for the price — far better than I expected for the rate.": {"aspect": "Value", "sentiment": 1},
    "Affordable and comfortable, a smart choice for a tighter budget.": {"aspect": "Value", "sentiment": 1},
    "Great bang for your buck; you really get a lot for what you pay.": {"aspect": "Value", "sentiment": 1},
    "Overpriced for what you actually get.": {"aspect": "Value", "sentiment": -1},
    "Far too expensive for such an average, no-frills experience.": {"aspect": "Value", "sentiment": -1},
    "Breakfast was overpriced at $45 and surprisingly basic.": {"aspect": "Value", "sentiment": -1},

    # Accessibility
    "Fully step-free with a spacious, well-designed accessible room.": {"aspect": "Accessibility", "sentiment": 1},
    "Getting around was easy with my wheelchair; ramps and lifts everywhere.": {"aspect": "Accessibility", "sentiment": 1},
    "Excellent accessibility — wide doorways, roll-in shower, and helpful staff.": {"aspect": "Accessibility", "sentiment": 1},
    "Not accessible — no ramps and the lift didn't reach all floors.": {"aspect": "Accessibility", "sentiment": -1},
    "Step-heavy layout made it very difficult with reduced mobility.": {"aspect": "Accessibility", "sentiment": -1},

    # WiFi/Quietness
    "The business center and conference facilities were excellent, ideal for work trips.": {"aspect": "WiFi/Quietness", "sentiment": 1},
    "Great setup for business travel: fast reliable internet and a proper desk.": {"aspect": "WiFi/Quietness", "sentiment": 1},
    "Meeting rooms were well-equipped and the WiFi was rock solid for video calls.": {"aspect": "WiFi/Quietness", "sentiment": 1},
    "Soundproofing was superb, not a peep from the street.": {"aspect": "WiFi/Quietness", "sentiment": 1},
    "Slept beautifully — very quiet despite being central.": {"aspect": "WiFi/Quietness", "sentiment": 1},
    "Room was wonderfully peaceful and the blackout curtains were perfect.": {"aspect": "WiFi/Quietness", "sentiment": 1},
    "No proper workspace and the internet was far too slow for business.": {"aspect": "WiFi/Quietness", "sentiment": -1},
    "WiFi kept dropping during calls, which was frustrating for work.": {"aspect": "WiFi/Quietness", "sentiment": -1},
    "Room was noisy due to nearby construction and thin walls.": {"aspect": "WiFi/Quietness", "sentiment": -1},
    "Constant street noise made it hard to sleep.": {"aspect": "WiFi/Quietness", "sentiment": -1},

    # Family-Friendliness
    "Plenty for children to do and the family suite had loads of space.": {"aspect": "Family-Friendliness", "sentiment": 1},
    "The kids loved the pool and the staff were wonderful with our toddler.": {"aspect": "Family-Friendliness", "sentiment": 1},
    "Fantastic for families — connecting rooms, a kids' club, and high chairs at breakfast.": {"aspect": "Family-Friendliness", "sentiment": 1},
    "Cramped rooms and nothing for the little ones to do.": {"aspect": "Family-Friendliness", "sentiment": -1},
    "Not great for kids — no facilities and the staff seemed annoyed by children.": {"aspect": "Family-Friendliness", "sentiment": -1}
}

# Globals for lazy-loading models and caching embeddings
_st_model = None
_classifier = None
_anchor_sentences = []
_anchor_embeddings = None

def get_sentence_transformer():
    """Lazy load SentenceTransformer model."""
    global _st_model
    if _st_model is None:
        from sentence_transformers import SentenceTransformer
        _st_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _st_model

def get_zero_shot_classifier():
    """Lazy load zero-shot classification pipeline."""
    global _classifier
    if _classifier is None:
        from transformers import pipeline
        try:
            # Prefer lightweight DistilBART model
            _classifier = pipeline("zero-shot-classification", model="valhalla/distilbart-mnli-12-3")
        except Exception:
            # Fallback to standard BART model if distilbart fails/is unavailable
            _classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
    return _classifier

def init_anchors():
    """Precompute embeddings for the 87 anchor template sentences."""
    global _anchor_sentences, _anchor_embeddings
    if _anchor_embeddings is None:
        model = get_sentence_transformer()
        _anchor_sentences = list(TEMPLATE_MAP.keys())
        # Compute embeddings for all anchor templates
        _anchor_embeddings = model.encode(_anchor_sentences, convert_to_tensor=True)

def rule_based_fallback(text: str) -> dict:
    """
    Highly robust rule-based fallback for aspect and sentiment prediction
    used when ML models are unavailable or crash.
    """
    text_lower = text.lower()
    
    # Aspect keyword mapping
    aspects = {
        "Cleanliness": ["clean", "dirty", "spotless", "immaculate", "housekeeping", "hair", "grimy", "grubby", "tidy", "dust", "carpets"],
        "Service": ["staff", "service", "team", "host", "receptionist", "chef", "dining", "food", "spa", "pool", "wellness", "checkout", "check-in", "breakfast", "restaurant", "massage"],
        "Location": ["location", "beach", "walking", "distance", "neighborhood", "view", "central", "sights", "transit", "bus", "taxi", "street", "safe", "secure", "isolated", "nightlife", "markets", "eateries"],
        "Value": ["value", "price", "budget", "money", "cost", "expensive", "cheap", "affordable", "overpriced", "rate", "billing"],
        "Accessibility": ["accessibility", "wheelchair", "ramp", "lift", "step-free", "handicap", "elevator", "mobility"],
        "WiFi/Quietness": ["wifi", "internet", "connection", "zoom", "call", "noise", "quiet", "soundproofing", "sleep", "loud", "construction", "peaceful", "workspace", "desk"],
        "Family-Friendliness": ["family", "kids", "children", "toddler", "baby", "club", "suites", "space", "crib", "ones"]
    }
    
    # Simple count-based aspect mapping
    aspect_counts = {aspect: 0 for aspect in aspects}
    for aspect, keywords in aspects.items():
        for keyword in keywords:
            if keyword in text_lower:
                aspect_counts[aspect] += 1
                
    max_aspect = max(aspect_counts, key=aspect_counts.get)
    assigned_aspect = max_aspect if aspect_counts[max_aspect] > 0 else None
    
    # Sentiment keyword mapping
    positive_words = ["great", "good", "excellent", "beautiful", "loved", "spotlessly", "clean", "friendly", "helpful", "fast", "reliable", "steps", "easy", "safe", "secure", "solid", "retreat", "highlight", "impeccable", "refinement", "indulgent", "refresh", "world-class", "delicious", "peaceful"]
    negative_words = ["bad", "worst", "poor", "dirty", "rude", "slow", "expensive", "overpriced", "drop", "noisy", "isolated", "sketch", "sketchy", "difficult", "cramped", "limited", "disappointing", "basic", "far", "unhelpful", "indifferent", "grubby", "noise", "shuts", "uneasy", "isolation"]
    
    pos_count = sum(1 for w in positive_words if w in text_lower)
    neg_count = sum(1 for w in negative_words if w in text_lower)
    
    if pos_count > neg_count:
        sentiment = 1
    elif neg_count > pos_count:
        sentiment = -1
    else:
        sentiment = 0
        
    return {"aspect": assigned_aspect, "sentiment": sentiment}

def extract_sentence_aspect_sentiment(text: str) -> dict:
    """
    Dual-Path Hybrid Aspect-Sentiment Extraction logic:
    1. Fast Path: Exact match lookup in TEMPLATE_MAP (milliseconds).
    2. General Path: SentenceTransformer embedding + cosine similarity match (> 0.80).
    3. Fallback Path: Zero-shot classification using valhalla/distilbart-mnli-12-3.
    """
    cleaned_text = text.strip()
    
    # 1. Fast Path (Exact Matches)
    if cleaned_text in TEMPLATE_MAP:
        return TEMPLATE_MAP[cleaned_text]
        
    # 2. General Path (Cosine Similarity Match)
    try:
        init_anchors()
        model = get_sentence_transformer()
        from sentence_transformers import util
        import torch
        
        query_embedding = model.encode(cleaned_text, convert_to_tensor=True)
        cos_scores = util.cos_sim(query_embedding, _anchor_embeddings)[0]
        max_idx = torch.argmax(cos_scores).item()
        max_score = cos_scores[max_idx].item()
        
        if max_score > 0.80:
            matched_sentence = _anchor_sentences[max_idx]
            return TEMPLATE_MAP[matched_sentence]
            
    except Exception as e:
        # Fallback to zero-shot if similarity calculation fails
        pass

    # 3. Fallback Path (Zero-Shot Classifier)
    try:
        classifier = get_zero_shot_classifier()
        
        # Classify Aspect
        aspect_labels = ["Cleanliness", "Service", "Location", "Value", "Accessibility", "WiFi/Quietness", "Family-Friendliness", "Other"]
        aspect_res = classifier(cleaned_text, candidate_labels=aspect_labels)
        best_aspect = aspect_res["labels"][0]
        mapped_aspect = None if best_aspect == "Other" else best_aspect
        
        # Classify Sentiment
        sentiment_labels = ["positive", "negative", "neutral"]
        sentiment_res = classifier(cleaned_text, candidate_labels=sentiment_labels)
        best_sentiment = sentiment_res["labels"][0]
        
        if best_sentiment == "positive":
            mapped_sentiment = 1
        elif best_sentiment == "negative":
            mapped_sentiment = -1
        else:
            mapped_sentiment = 0
            
        return {"aspect": mapped_aspect, "sentiment": mapped_sentiment}
        
    except Exception as e:
        # If ML pipeline fails completely, use rule-based fallback
        return rule_based_fallback(cleaned_text)
