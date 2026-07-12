import subprocess
import sys
import time

def main():
    print("Starting backend API server (FastAPI) on port 8000...")
    api_process = subprocess.Popen([sys.executable, "-m", "uvicorn", "api:app", "--port", "8000"])
    
    # Wait a moment for backend to initialize
    time.sleep(2)
    
    print("Starting frontend dashboard (Streamlit) on port 8501...")
    app_process = subprocess.Popen([sys.executable, "-m", "streamlit", "run", "app.py"])
    
    try:
        while True:
            time.sleep(1)
            # Check if either process terminated unexpectedly
            if api_process.poll() is not None:
                print("API server stopped unexpectedly.")
                break
            if app_process.poll() is not None:
                print("Streamlit dashboard stopped unexpectedly.")
                break
    except KeyboardInterrupt:
        print("\nShutting down servers...")
    finally:
        api_process.terminate()
        app_process.terminate()
        print("Goodbye!")

if __name__ == "__main__":
    main()
