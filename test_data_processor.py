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
        # Hotel H001:
        # - Cleanliness: 3 positive, 1 negative -> 3.0 + 2.0 * (3-1)/4 = 4.0
        # - Service: 0 positive, 4 negative -> 3.0 + 2.0 * (0-4)/4 = 1.0
        # - Others: 0 mentions -> should fall back to overall review rating (average of 5.0 and 1.0 = 3.0)
        mock_reviews = [
            {
                "hotel_id": "H001",
                "hotel_name": "Test Hotel, Barcelona",
                "rating": "5.0",
                "review_date": "2025-05-01",
                "review_text": "Spotlessly clean room and an immaculate bathroom. Everything was sparkling clean, clearly very well maintained. Housekeeping was impeccable; the room was fresh every single day. Service was indifferent and slow throughout the stay."
            },
            {
                "hotel_id": "H001",
                "hotel_name": "Test Hotel, Barcelona",
                "rating": "1.0",
                "review_date": "2025-05-02",
                "review_text": "Room wasn't clean on arrival — found hair in the bathroom. Front desk was rude and unhelpful whenever we asked for anything. Wellness facilities were tired and the pool was often closed. The spa was small and underwhelming for a property of this class."
            }
        ]
        
        scorecard = data_processor.compile_aspect_scorecard(mock_reviews)
        self.assertIn("H001", scorecard)
        hotel_scores = scorecard["H001"]
        
        self.assertEqual(hotel_scores["Cleanliness"], 4.0)
        self.assertEqual(hotel_scores["Service"], 1.0)
        
        for aspect in ["Location", "Value", "Accessibility", "WiFi/Quietness", "Family-Friendliness"]:
            self.assertEqual(hotel_scores[aspect], 3.0)

    def test_compile_aspect_scorecard_fallback_default(self):
        mock_reviews = [
            {
                "hotel_id": "H002",
                "hotel_name": "Fallback Hotel, Rome",
                "rating": "4.50",
                "review_date": "2025-05-01",
                "review_text": "Second time staying at this property. Stayed here for a few nights."
            }
        ]
        scorecard = data_processor.compile_aspect_scorecard(mock_reviews)
        self.assertIn("H002", scorecard)
        hotel_scores = scorecard["H002"]
        
        for aspect in data_processor.ASPECTS:
            self.assertEqual(hotel_scores[aspect], 4.5)

    def test_detect_quality_anomalies_true_positive(self):
        # Hotel H003 (Quality Anomaly):
        # Max date is 2025-12-01. Cutoff is 60 days before (2025-10-02).
        # Historic split (2025-01-01): 3 positive cleanliness, 0 negative -> Cleanliness score = 5.0.
        # Recent split (2025-12-01): 0 positive cleanliness, 3 negative -> Cleanliness score = 1.0.
        # Since H003 has no data in 2024, it's not seasonal. It should be flagged as an anomaly.
        mock_reviews = [
            {
                "hotel_id": "H003",
                "hotel_name": "Problematic Inn, Istanbul",
                "rating": "5.0",
                "review_date": "2025-01-01",
                "review_text": "Spotlessly clean room and an immaculate bathroom. Everything was sparkling clean, clearly very well maintained. Housekeeping was impeccable; the room was fresh every single day."
            },
            {
                "hotel_id": "H003",
                "hotel_name": "Problematic Inn, Istanbul",
                "rating": "1.0",
                "review_date": "2025-12-01",
                "review_text": "Room wasn't clean on arrival — found hair in the bathroom. Housekeeping was inconsistent and the carpets looked grubby."
            }
        ]
        
        anomalies = data_processor.detect_quality_anomalies(mock_reviews)
        self.assertEqual(len(anomalies), 1)
        anomaly = anomalies[0]
        self.assertEqual(anomaly["hotel_id"], "H003")
        self.assertEqual(anomaly["aspect"], "Cleanliness")
        self.assertEqual(anomaly["historic_score"], 5.0)
        self.assertEqual(anomaly["recent_score"], 1.0)
        self.assertEqual(anomaly["drop_percentage"], -80.0)

    def test_detect_quality_anomalies_seasonal_drift_exclusion(self):
        # Hotel H004 (Seasonal Drift):
        # Max date is 2025-12-01. Cutoff is 60 days before (2025-10-02). Recent months are Nov-Dec.
        # 2025:
        # - Historic (Jan-Oct 2025): 3 positive cleanliness -> 5.0
        # - Recent (Nov-Dec 2025): 3 negative cleanliness -> 1.0 (Drop of -80%)
        # 2024 (Previous year counterpart check):
        # - Historic (Jan-Oct 2024): 3 positive cleanliness -> 5.0
        # - Recent (Nov-Dec 2024): 3 negative cleanliness -> 1.0 (Drop of -80%)
        # Since this drop also occurred in 2024, it is a seasonal drift and should NOT be flagged.
        mock_reviews = [
            # 2024
            {
                "hotel_id": "H004",
                "hotel_name": "Seasonal Lodge, London",
                "rating": "5.0",
                "review_date": "2024-05-01",
                "review_text": "Spotlessly clean room and an immaculate bathroom. Everything was sparkling clean, clearly very well maintained. Housekeeping was impeccable; the room was fresh every single day."
            },
            {
                "hotel_id": "H004",
                "hotel_name": "Seasonal Lodge, London",
                "rating": "1.0",
                "review_date": "2024-12-01",
                "review_text": "Room wasn't clean on arrival — found hair in the bathroom. Housekeeping was inconsistent and the carpets looked grubby."
            },
            # 2025
            {
                "hotel_id": "H004",
                "hotel_name": "Seasonal Lodge, London",
                "rating": "5.0",
                "review_date": "2025-05-01",
                "review_text": "Spotlessly clean room and an immaculate bathroom. Everything was sparkling clean, clearly very well maintained. Housekeeping was impeccable; the room was fresh every single day."
            },
            {
                "hotel_id": "H004",
                "hotel_name": "Seasonal Lodge, London",
                "rating": "1.0",
                "review_date": "2025-12-01",
                "review_text": "Room wasn't clean on arrival — found hair in the bathroom. Housekeeping was inconsistent and the carpets looked grubby."
            }
        ]
        
        anomalies = data_processor.detect_quality_anomalies(mock_reviews)
        # Should exclude H004 because it is seasonal drift
        self.assertEqual(len(anomalies), 0)

    def test_analyze_seasonal_trends_explanation(self):
        # Hotel H005 in London:
        # Peak months (June, July, August): 3 positive location mentions -> Location score = 5.0
        # Off-peak months (December, January, February): 3 negative location mentions -> Location score = 1.0
        # (This should trigger London's seasonality profile in the description)
        mock_reviews = [
            # Peak months
            {
                "hotel_id": "H005",
                "hotel_name": "Seasons Hotel, London",
                "rating": "5.0",
                "review_date": "2025-06-01",
                "review_text": "You can't beat the location — everything was a short stroll away."
            },
            {
                "hotel_id": "H005",
                "hotel_name": "Seasons Hotel, London",
                "rating": "5.0",
                "review_date": "2025-07-01",
                "review_text": "Right in the heart of the city, so easy to get everywhere on foot."
            },
            {
                "hotel_id": "H005",
                "hotel_name": "Seasons Hotel, London",
                "rating": "5.0",
                "review_date": "2025-08-01",
                "review_text": "Perfect central location, walking distance to all the main sights."
            },
            # Off-peak months
            {
                "hotel_id": "H005",
                "hotel_name": "Seasons Hotel, London",
                "rating": "1.0",
                "review_date": "2025-12-01",
                "review_text": "Felt quite isolated — nothing within walking distance."
            },
            {
                "hotel_id": "H005",
                "hotel_name": "Seasons Hotel, London",
                "rating": "1.0",
                "review_date": "2025-01-01",
                "review_text": "The location was far from everything and required long, expensive taxi rides."
            },
            {
                "hotel_id": "H005",
                "hotel_name": "Seasons Hotel, London",
                "rating": "1.0",
                "review_date": "2025-02-01",
                "review_text": "Felt quite isolated — nothing within walking distance."
            }
        ]
        
        trends = data_processor.analyze_seasonal_trends(mock_reviews)
        self.assertIn("H005", trends)
        trend = trends["H005"]
        
        self.assertEqual(trend["seasonal_aspect"], "Location")
        self.assertEqual(trend["max_score"], 5.0)
        self.assertEqual(trend["min_score"], 1.0)
        self.assertEqual(trend["variance"], 4.0)
        
        # Verify the custom explanation matches London and details the off-peak sentences
        explanation = trend["explanation"]
        self.assertIn("Location scores for this hotel exhibit clear seasonality", explanation)
        self.assertIn("London", explanation)
        self.assertIn('Felt quite isolated', explanation)
        self.assertIn("rainy winters reduce outdoor walkability", explanation)

if __name__ == "__main__":
    unittest.main()
