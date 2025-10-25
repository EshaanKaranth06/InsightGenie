import os
from serpapi import GoogleSearch
from datetime import datetime
from dotenv import load_dotenv
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

def scrape_google_search(query: str, limit: int = 10):
    """
    Uses SerpApi to get top Google Search results for a query.
    Returns a list of dictionaries containing title, link, and snippet.
    """
    print(f"🔍 Getting top {limit} Google Search results via SerpApi for query: '{query}'...")

    if not SERPAPI_API_KEY:
        print("❌ SerpApi API key missing in .env file. Skipping Google Search scraping.")
        return []

    collected_results = []
    try:
        params = {
          "q": query,
          "api_key": SERPAPI_API_KEY,
          "num": limit # Number of results to return
        }

        search = GoogleSearch(params)
        results_data = search.get_dict()

        organic_results = results_data.get("organic_results", [])

        if not organic_results:
            print("⚠️ No organic results found by SerpApi.")
            return []

        print(f"✅ Found {len(organic_results)} organic results from SerpApi.")

        for result in organic_results:
            link = result.get("link")
            if not link: # Skip results without a link
                continue

            collected_results.append({
                "source": "Google Search Result", # Source identifier
                "source_id": link, # Use the URL as a unique ID
                "content": f"{result.get('title', '')}\n{result.get('snippet', '')}".strip(), # Combine title and snippet
                "created_at": None # Search results don't have a creation date
            })

    except Exception as e:
        print(f"❌ Google Search scraping via SerpApi failed: {e}")
        return []

    print(f"✅ Google Search scraping complete. Collected {len(collected_results)} results.")
    return collected_results

# Example usage (for testing this script directly)
if __name__ == '__main__':
    # Make sure to load .env if running standalone
    from dotenv import load_dotenv
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    load_dotenv(dotenv_path=dotenv_path)
    SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY") # Reload after loading .env

    test_query = "Royal Enfield Continental GT 650 review"
    scraped_data = scrape_google_search(test_query, limit=5)
    if scraped_data:
        print("\n--- Scraped Data ---")
        for item in scraped_data:
            print(f"Link: {item['source_id']}")
            print(f"Content:\n{item['content']}\n---")
    else:
        print("No data scraped.")