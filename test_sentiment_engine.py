import time
import sentiment_engine

def test_fast_path():
    print("\n--- Running Fast Path Unit Tests ---")
    test_cases = [
        ("Spotlessly clean room and an immaculate bathroom.", "Cleanliness", 1),
        ("Room wasn't clean on arrival — found hair in the bathroom.", "Cleanliness", -1),
        ("Front desk was rude and unhelpful whenever we asked for anything.", "Service", -1),
        ("Perfect central location, walking distance to all the main sights.", "Location", 1),
        ("Second time staying at this property.", None, 1),
        ("Stayed here for a few nights.", None, 0),
    ]
    
    for text, expected_aspect, expected_sentiment in test_cases:
        t0 = time.perf_counter()
        res = sentiment_engine.extract_sentence_aspect_sentiment(text)
        t1 = time.perf_counter()
        duration_ms = (t1 - t0) * 1000
        
        assert res["aspect"] == expected_aspect, f"Expected aspect {expected_aspect}, got {res['aspect']} for: {text}"
        assert res["sentiment"] == expected_sentiment, f"Expected sentiment {expected_sentiment}, got {res['sentiment']} for: {text}"
        print(f"Passed: [{text}] -> aspect: {res['aspect']}, sentiment: {res['sentiment']} (Time: {duration_ms:.4f} ms)")
        assert duration_ms < 1.0, f"Fast Path took too long: {duration_ms:.4f} ms"

def test_general_path():
    print("\n--- Running General Path Unit Tests ---")
    # Para-phrased / slight variations of template sentences
    test_cases = [
        # Original: "Spotlessly clean room and an immaculate bathroom."
        ("Spotlessly clean room & a very immaculate bathroom.", "Cleanliness", 1),
        # Original: "Room wasn't clean on arrival — found hair in the bathroom."
        ("Room was not clean on arrival — found hair in our bathroom.", "Cleanliness", -1),
        # Original: "Front desk was rude and unhelpful whenever we asked for anything."
        ("Front desk was rude & unhelpful whenever we asked for something.", "Service", -1),
    ]
    
    for text, expected_aspect, expected_sentiment in test_cases:
        t0 = time.perf_counter()
        res = sentiment_engine.extract_sentence_aspect_sentiment(text)
        t1 = time.perf_counter()
        duration_ms = (t1 - t0) * 1000
        
        print(f"Match: [{text}] -> aspect: {res['aspect']}, sentiment: {res['sentiment']} (Time: {duration_ms:.2f} ms)")
        assert res["aspect"] == expected_aspect, f"General Path: Expected aspect {expected_aspect}, got {res['aspect']} for: {text}"
        assert res["sentiment"] == expected_sentiment, f"General Path: Expected sentiment {expected_sentiment}, got {res['sentiment']} for: {text}"

def test_fallback_path():
    print("\n--- Running Fallback Path (Zero-Shot/Rule-based) Unit Tests ---")
    # Totally unique sentence, should fallback to Zero-Shot or rule-based fallback
    unrelated_text = "The elevator was completely broken but the breakfast was wonderful."
    # Since it mentions "elevator" (Accessibility) and "breakfast" (Service), and says "broken" (negative) and "wonderful" (positive),
    # the classifier or rule-based engine should resolve it dynamically.
    
    t0 = time.perf_counter()
    res = sentiment_engine.extract_sentence_aspect_sentiment(unrelated_text)
    t1 = time.perf_counter()
    duration_ms = (t1 - t0) * 1000
    
    print(f"Fallback: [{unrelated_text}] -> aspect: {res['aspect']}, sentiment: {res['sentiment']} (Time: {duration_ms:.2f} ms)")
    assert res["aspect"] in ["Accessibility", "Service", None], f"Unexpected fallback aspect: {res['aspect']}"
    assert res["sentiment"] in [-1, 0, 1], f"Unexpected fallback sentiment: {res['sentiment']}"

def run_latency_benchmark():
    print("\n--- Running Latency Benchmark (50,000 exact lookups) ---")
    # Prepare 50,000 sentences using template lookups
    import random
    templates = list(sentiment_engine.TEMPLATE_MAP.keys())
    batch = [random.choice(templates) for _ in range(50000)]
    
    print("Starting processing of 50,000 sentences...")
    t0 = time.perf_counter()
    for sentence in batch:
        res = sentiment_engine.extract_sentence_aspect_sentiment(sentence)
    t1 = time.perf_counter()
    
    duration = t1 - t0
    print(f"Processed 50,000 lookups in {duration:.4f} seconds!")
    print(f"Average time per sentence: {(duration / 50000) * 1000:.6f} ms")
    assert duration < 5.0, f"Benchmark failed: Took {duration:.2f} seconds which is above the 5.0 seconds PRD requirement."

if __name__ == "__main__":
    try:
        test_fast_path()
        test_general_path()
        test_fallback_path()
        run_latency_benchmark()
        print("\nAll Phase 1 tests passed successfully!")
    except AssertionError as e:
        print(f"\nAssertion Error: {e}")
        import sys
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        import sys
        sys.exit(1)
