from fastapi import FastAPI, HTTPException
import requests
from bs4 import BeautifulSoup

# Programmable Search Engine ID: 5686e09ce64f54ca2
# API Key: AIzaSyDyLDDcuhkqRU_tYMBe7ObkqOJsnwe3_1Y

app = FastAPI()

# Configuration
GOOGLE_API_KEY = "AIzaSyDyLDDcuhkqRU_tYMBe7ObkqOJsnwe3_1Y"
SEARCH_ENGINE_ID = "5686e09ce64f54ca2"

def google_search(query):
    """
    Queries Google Custom Search restricted to the specific health sites.
    """
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'key': GOOGLE_API_KEY,
        'cx': SEARCH_ENGINE_ID,
        'q': query,
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error calling Google API: {e}")
        return None

@app.get("/")
def home():
    return {"message": "Health Article API is running. Use /search?q=your_query"}

@app.get("/search")
def search_health_sites(q: str):
    """
    Endpoint to search WebMD, Healthline, Mayo Clinic, and Cleveland Clinic.
    """
    if not q:
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required")

    data = google_search(q)
    
    if not data or 'items' not in data:
        return {"results": [], "message": "No results found or error occurred."}

    # Clean up the results to return just what we need
    clean_results = []
    for item in data['items']:
        clean_results.append({
            "title": item.get("title"),
            "link": item.get("link"),
            "snippet": item.get("snippet"),
            "source": item.get("displayLink")
        })

    return {
        "query": q,
        "count": len(clean_results),
        "results": clean_results
    }

if __name__ == "__main__":
    import uvicorn
    # Run the API locally on port 8000
    uvicorn.run(app, host="localhost", port=8000)