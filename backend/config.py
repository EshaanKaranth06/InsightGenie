import os
from dotenv import load_dotenv

# Load environment variables from the .env file in the backend directory
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=dotenv_path)

# === API Keys ===
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")


# === Scraper settings ===
SCRAPER_CONFIG = {
    "product_name": "Bajaj Pulsar NS400Z",
    "search_query": "Bajaj Pulsar NS400Z review",

    "youtube": {
        "keywords_to_filter": [
            "engine", "performance", "vibrations", "handling", "suspension", 
            "brakes", "mileage", "price", "heating", "features", "display"
        ],
        "max_videos": 10
    },
    "reddit": {
        "subreddits": [
            "IndianBikes",
            "india",
            "bangalore",
            "mumbai"
        ],
        "max_posts": 50
    },
    # You can enable other scrapers like Google Reviews here if needed
    "google_reviews": {
        "enabled": False 
    }
}
"""
SCRAPER_CONFIG = {
    "product_name": "Galaxy S25 Ultra",
    "search_query": "Galaxy S25 Ultra review",

    "youtube": {
        "keywords_to_filter": ["battery", "camera", "price", "screen", "performance", "issue", "problem", "display"],
        "max_videos": 10
    },
    "reddit": {
        "subreddits": [
            "samsunggalaxy",
            "Android",
            "smartphones",
            "GalaxyS25Ultra"
        ],
        "max_posts": 50
    }
}
"""

# === Scraper settings ===
"""
SCRAPER_CONFIG = {
    "product_name": "Nandini Milk",
    "search_query": "Nandini Milk review",

    "youtube": {
        "keywords_to_filter": ["milk", "pasteurized", "toned", "fortified", "health", "taste", "price", "quality"],
        "max_videos": 10
    },
    "reddit": {
        "subreddits": [
            "bangalore",
            "karnataka",
            "india",
            "IndianFood"
        ],
        "max_posts": 50
    }
}
"""