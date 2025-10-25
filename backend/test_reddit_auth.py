import praw
import os
from dotenv import load_dotenv

# Load .env file from your backend folder
# Adjust path if needed
dotenv_path = r'D:\InsightGenie\backend\.env'
load_dotenv(dotenv_path=dotenv_path)

REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")

print("Attempting to connect with:")
print(f"  Client ID: {REDDIT_CLIENT_ID}")
print(f"  Secret:    {REDDIT_CLIENT_SECRET[:5] if REDDIT_CLIENT_SECRET else 'None'}") # Print only first few chars of secret
print(f"  User Agent: {REDDIT_USER_AGENT}")

if not all([REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT]):
    print("\nERROR: Missing credentials in .env file!")
else:
    try:
        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT,
            read_only=True
        )
        # Try accessing a simple attribute to force authentication
        me = reddit.user.me()
        print("\nSUCCESS! Authentication successful.")
        print(f"Authenticated as: {me or 'read-only user'}")

        # Try accessing a known subreddit
        print("\nAttempting to access r/test...")
        subreddit = reddit.subreddit("test")
        print(f"Successfully accessed subreddit: {subreddit.display_name}")

    except Exception as e:
        print(f"\nERROR: Connection failed!")
        print(e)