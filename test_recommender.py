import unittest
import json
import recommender
import data_processor

class TestRecommender(unittest.TestCase):
    
    def test_extract_aspect_weights_predefined(self):
        # Description: "Solo female traveler, safety-conscious, wants a central, walkable base, keen on local culture and markets."
        # This is P01, matches "Solo-Traveler" archetype closely.
        desc = "Solo female traveler, safety-conscious, wants a central, walkable base, keen on local culture and markets."
        weights = recommender.extract_aspect_weights(desc)
        
        # Verify Location weight is high
        self.assertIn("Location", weights)
        self.assertGreaterEqual(weights["Location"], 0.5)

    def test_extract_aspect_weights_custom_dynamic(self):
        # Custom: "I need a budget stay with super fast internet to do zoom calls."
        # Should dynamically extract high weights for Value and WiFi/Quietness (either via zero-shot or keyword fallback)
        desc = "I need a budget stay with super fast internet to do zoom calls."
        weights = recommender.extract_aspect_weights(desc)
        
        # Check WiFi/Quietness and Value have positive weights
        self.assertIn("WiFi/Quietness", weights)
        self.assertIn("Value", weights)
        self.assertGreater(weights["WiFi/Quietness"], 0.1)
        self.assertGreater(weights["Value"], 0.1)

    def test_recommender_mcda_and_accessibility_penalty(self):
        # Setup mock reviews:
        # Hotel H101 (Overall rating: 5.0, Cleanliness aspect: 5.0. Accessibility aspect: 1.0 (has negative accessibility comments))
        # Hotel H102 (Overall rating: 3.0, Cleanliness aspect: 4.0. Accessibility aspect: 5.0 (no negative accessibility comments))
        mock_reviews = [
            # Hotel H101
            {
                "review_id": "REV101",
                "hotel_id": "H101",
                "hotel_name": "Lux Hotel, Paris",
                "rating": "5.0",
                "review_date": "2025-05-01",
                "review_text": "Spotlessly clean room and an immaculate bathroom. Not accessible — no ramps and the lift didn't reach all floors."
            },
            # Hotel H102
            {
                "review_id": "REV102",
                "hotel_id": "H102",
                "hotel_name": "Accessible Lodge, Paris",
                "rating": "3.0",
                "review_date": "2025-05-01",
                "review_text": "Getting around was easy with my wheelchair; ramps and lifts everywhere."
            }
        ]
        
        # We need mock user profiles
        mock_profiles = [
            {"profile_id": "P_MOBILITY", "description": "Traveler in a wheelchair, step-free access needed."},
            {"profile_id": "P_NORMAL", "description": "Wellness guest seeking spotless cleanliness."}
        ]
        
        # Write mock files to scratch for testing
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as rf:
            json.dump(mock_reviews, rf)
            reviews_temp_path = rf.name
            
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as pf:
            json.dump(mock_profiles, pf)
            profiles_temp_path = pf.name
            
        try:
            # Instantiate Recommender on mock data
            rec = recommender.Recommender(reviews_temp_path, profiles_temp_path)
            
            # Case 1: Normal traveler (P_NORMAL) - cares about Cleanliness
            # H101 has cleanliness 5.0 and overall rating 5.0. H102 has cleanliness 3.0 (fallback to overall rating) and overall 3.0.
            # H101 should rank 1st
            recs_normal = rec.get_recommendations("P_NORMAL", top_n=2)
            self.assertEqual(recs_normal[0]["hotel_id"], "H101")
            
            # Case 2: Mobility traveler (P_MOBILITY) - requires wheelchair access
            # H101 has negative accessibility comments ("Not accessible..."), so it should receive a 2.5-point penalty.
            # H102 has positive accessibility comments.
            # H101's score will drop drastically, making H102 rank 1st
            recs_mobility = rec.get_recommendations("P_MOBILITY", top_n=2)
            self.assertEqual(recs_mobility[0]["hotel_id"], "H102")
            self.assertGreater(recs_mobility[1]["applied_penalty"], 0.0) # H101 had a penalty
            
        finally:
            os.remove(reviews_temp_path)
            os.remove(profiles_temp_path)

if __name__ == "__main__":
    unittest.main()
