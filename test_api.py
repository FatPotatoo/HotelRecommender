import unittest
from fastapi.testclient import TestClient
import api

class TestAPI(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # Initialize Recommender cache during startup
        api.startup_event()
        cls.client = TestClient(api.app)

    def test_get_profiles(self):
        response = self.client.get("/api/profiles")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("P01", data)
        self.assertIn("P50", data)

    def test_get_hotels(self):
        response = self.client.get("/api/hotels")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(len(data), 0)
        self.assertIn("hotel_id", data[0])
        self.assertIn("hotel_name", data[0])

    def test_recommendations(self):
        # Test predefined profile recommendation
        payload = {"query": "P08", "top_n": 3}
        response = self.client.post("/api/recommend", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data["query"], "P08")
        self.assertIn("weights", data)
        self.assertIn("recommendations", data)
        
        recs = data["recommendations"]
        self.assertEqual(len(recs), 3)
        self.assertIn("hotel_name", recs[0])
        self.assertIn("evidence", recs[0])
        self.assertIn("match_score", recs[0])

    def test_anomalies(self):
        response = self.client.get("/api/anomalies")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # Should be a list
        self.assertIsInstance(data, list)
        if len(data) > 0:
            self.assertIn("hotel_id", data[0])
            self.assertIn("aspect", data[0])
            self.assertIn("drop_percentage", data[0])

    def test_seasonality(self):
        # We know H051 is in the dataset
        response = self.client.get("/api/seasonality/H051")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data["hotel_id"], "H051")
        self.assertIn("trend", data)
        self.assertIn("ratings_stream", data)
        self.assertIn("explanation", data["trend"])

if __name__ == "__main__":
    unittest.main()
