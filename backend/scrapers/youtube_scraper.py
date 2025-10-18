import os
import googleapiclient.discovery
from youtube_transcript_api import YouTubeTranscriptApi
from datetime import datetime

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

def _get_video_ids(youtube, query: str, max_results: int):
    """Finds the top video IDs for a given search query."""
    request = youtube.search().list(
        part="snippet",
        q=query,
        type="video",
        order="relevance",
        maxResults=max_results
    )
    response = request.execute()
    return [item['id']['videoId'] for item in response.get('items', [])]

def _get_comments(youtube, video_id: str, keywords: list):
    """Fetches comments for a video that match specific keywords."""
    matching_comments = []
    try:
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=100,
            textFormat="plainText"
        )
        response = request.execute()

        while response:
            for item in response['items']:
                comment = item['snippet']['topLevelComment']['snippet']
                comment_text = comment['textDisplay']
                
                if not keywords or any(keyword.lower() in comment_text.lower() for keyword in keywords):
                    matching_comments.append({
                        "source": "YouTube Comment",
                        "source_id": f"yt_comment_{item['id']}",
                        "content": comment_text,
                        "created_at": comment['publishedAt']
                    })

            if 'nextPageToken' in response:
                request = youtube.commentThreads().list_next(request, response)
                response = request.execute()
            else:
                break
    except Exception as e:
        print(f"Could not retrieve comments for video {video_id}: {e}")
        
    return matching_comments

def scrape_youtube(query: str, keywords: list, max_videos: int = 10):
    """Main function to scrape YouTube video comments."""
    if not YOUTUBE_API_KEY:
        print("YouTube API key not found. Skipping YouTube scraping.")
        return []

    youtube = googleapiclient.discovery.build(
        "youtube", "v3", developerKey=YOUTUBE_API_KEY
    )
    
    print(f"🔍 Finding top {max_videos} YouTube videos for query: '{query}'...")
    video_ids = _get_video_ids(youtube, query, max_videos)
    print(f"Found {len(video_ids)} videos. Now fetching comments...")
    
    all_feedback = []
    for video_id in video_ids:
            
        comments = _get_comments(youtube, video_id, keywords)
        all_feedback.extend(comments)

    print(f" YouTube scraping complete. Found {len(all_feedback)} total comments.")
    return all_feedback
