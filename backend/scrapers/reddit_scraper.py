import os
import praw
from datetime import datetime
import prawcore
from dotenv import load_dotenv # <-- Add dotenv import

# --- Load .env specifically within this script ---
# Adjust path if .env is not in the parent 'backend' directory relative to 'scrapers'
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)
# --- End loading .env ---

# Load credentials AFTER loading .env
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")

def scrape_reddit(search_queries: list, subreddits: list, limit: int):
    """Scrapes Reddit for posts matching search queries."""
    print(" scraping Reddit...")

    # Print loaded creds (except secret) for debugging
    print(f"  Using Client ID: {REDDIT_CLIENT_ID}")
    print(f"  Using User Agent: {REDDIT_USER_AGENT}")

    if not all([REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT]):
        print("Reddit API credentials missing or failed to load. Skipping Reddit scraping.")
        return []

    collected_posts = []
    reddit = None

    try:
        # Explicitly pass credentials just in case
        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT,
            read_only=True
        )
        print(f"Reddit API authenticated as: {reddit.user.me() or 'read-only'}")

        for query in search_queries:
            for subreddit_name in subreddits:
                print(f"\nAttempting to access subreddit: r/{subreddit_name}")
                try:
                    subreddit = reddit.subreddit(subreddit_name)
                    _ = subreddit.display_name # Force validation
                    print(f"Successfully accessed r/{subreddit_name}. Searching...")

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

                # Specific error handling
                except prawcore.exceptions.NotFound:
                    print(f"❌ ERROR: Subreddit 'r/{subreddit_name}' not found (404). Skipping.")
                    continue
                except prawcore.exceptions.Forbidden:
                     print(f"❌ ERROR: Subreddit 'r/{subreddit_name}' is private or quarantined (403). Skipping.")
                     continue
                except prawcore.exceptions.Redirect:
                     print(f"❌ ERROR: Subreddit 'r/{subreddit_name}' caused redirect. Skipping.")
                     continue
                except Exception as sub_e:
                     print(f"❌ ERROR: Failed processing subreddit 'r/{subreddit_name}': {sub_e}")
                     continue

        print(f"\nReddit scraping complete. Found {len(collected_posts)} total posts.")
        return collected_posts

    # Catch potential authentication errors
    except prawcore.exceptions.OAuthException as auth_e:
        print(f"❌ Reddit Authentication Failed: {auth_e}. Check credentials.")
        return []
    except prawcore.exceptions.ResponseException as resp_e:
        # Catch other potential HTTP errors like 403 Forbidden here
        print(f"❌ Reddit API Request Failed: {resp_e}")
        print(f"   Response details: {resp_e.response}") # Log more details if available
        return []
    except Exception as e:
        print(f"❌ Reddit scraping failed unexpectedly: {e}")
        import traceback
        traceback.print_exc()
        return []