import os
import praw
from datetime import datetime
from dotenv import load_dotenv


dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")

def scrape_reddit(search_queries: list, subreddits: list, limit: int):
    """Scrapes Reddit for posts matching search queries."""
    print(" scraping Reddit...")
    
    if not all([REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT]):
        print("Reddit API credentials missing in .env file. Skipping Reddit scraping.")
        return []

    collected_posts = []
    try:
        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT
        )
        
        for query in search_queries:
            for subreddit_name in subreddits:
                subreddit = reddit.subreddit(subreddit_name)
                search_results = list(subreddit.search(query=query, limit=limit, sort='new'))
                print(f"--- Reddit Search for '{query}' in r/{subreddit_name} found {len(search_results)} results. ---")
                
                for post in search_results:
                    full_text = post.title + " " + post.selftext
                    collected_posts.append({
                        "source": "Reddit",
                        "source_id": f"reddit_post_{post.id}",
                        "content": full_text.strip(),
                        "created_at": datetime.utcfromtimestamp(post.created_utc).isoformat()
                    })
        
        print(f"Reddit scraping complete. Found {len(collected_posts)} total posts.")
        return collected_posts

    except Exception as e:
        print(f"Reddit scraping failed: {e}")
        return []
