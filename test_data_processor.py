import unittest
import data_processor

class TestDataProcessor(unittest.TestCase):
    
    def test_segment_sentences(self):
        text = "Spotlessly clean room and an immaculate bathroom. Room wasn't clean on arrival — found hair in the bathroom! Front desk was rude? Yes."
        expected = [
            "Spotlessly clean room and an immaculate bathroom.",
            "Room wasn't clean on arrival — found hair in the bathroom!",
            "Front desk was rude?",
            "Yes."
        ]
        result = data_processor.segment_sentences(text)
        self.assertEqual(result, expected)

    def test_compile_aspect_scorecard_math(self):
        # Create a mock review set with known outcomes
        # Hotel H001:
        # - Cleanliness: 3 positive, 1 negative -> 3.0 + 2.0 * (3-1)/4 = 4.0
        # - Service: 1 positive, 3 negative -> 3.0 + 2.0 * (1-3)/4 = 2.0
        # - Others: 0 mentions -> should fall back to overall review rating (average of 5.0 and 1.0 = 3.0)
        mock_reviews = [
            {
                "hotel_id": "H001",
                "hotel_name": "Test Hotel",
                "rating": "5.0",
                "review_text": "Spotlessly clean room and an immaculate bathroom. Everything was sparkling clean, clearly very well maintained. Housekeeping was impeccable; the room was fresh every single day. Service was indifferent and slow throughout the stay."
            },
            {
                "hotel_id": "H001",
                "hotel_name": "Test Hotel",
                "rating": "1.0",
                "review_text": "Room wasn't clean on arrival — found hair in the bathroom. Front desk was rude and unhelpful whenever we asked for anything. Wellness facilities were tired and the pool was often closed. The spa was small and underwhelming for a property of this class."
            }
        ]
        
        scorecard = data_processor.compile_aspect_scorecard(mock_reviews)
        
        # Verify hotel exists in scorecard
        self.assertIn("H001", scorecard)
        hotel_scores = scorecard["H001"]
        
        # Check Cleanliness math:
        # Positive: "Spotlessly clean room...", "Everything was sparkling...", "Housekeeping was impeccable..." (3)
        # Negative: "Room wasn't clean on arrival..." (1)
        # Score = 3.0 + 2.0 * (3-1)/4 = 4.0
        self.assertEqual(hotel_scores["Cleanliness"], 4.0)
        
        # Check Service math:
        # Positive: None (0)
        # Negative: "Service was indifferent...", "Front desk was rude...", "Wellness facilities were tired...", "The spa was small..." (4)
        # Score = 3.0 + 2.0 * (0-4)/4 = 1.0
        self.assertEqual(hotel_scores["Service"], 1.0)
        
        # Check Fallbacks for Location, Value, Accessibility, WiFi/Quietness, Family-Friendliness:
        # Since no mentions exist, they should fall back to H001 average rating: (5.0 + 1.0) / 2 = 3.0
        for aspect in ["Location", "Value", "Accessibility", "WiFi/Quietness", "Family-Friendliness"]:
            self.assertEqual(hotel_scores[aspect], 3.0)

    def test_compile_aspect_scorecard_fallback_default(self):
        # Create a mock review set where there is only 1 review with rating 4.5 and no mentions of anything
        mock_reviews = [
            {
                "hotel_id": "H002",
                "hotel_name": "Fallback Hotel",
                "rating": "4.50",
                "review_text": "Second time staying at this property. Stayed here for a few nights."
            }
        ]
        scorecard = data_processor.compile_aspect_scorecard(mock_reviews)
        
        self.assertIn("H002", scorecard)
        hotel_scores = scorecard["H002"]
        
        # All aspects should default to the overall rating: 4.5
        for aspect in data_processor.ASPECTS:
            self.assertEqual(hotel_scores[aspect], 4.5)

if __name__ == "__main__":
    unittest.main()
