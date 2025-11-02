import math
from sqlalchemy.orm import Session
from tqdm import tqdm

from backend.db.database import SessionLocal
from backend.db.models import Product
from backend.db.vector_store import QdrantDB
from backend.scrapers.youtube_scraper import scrape_youtube
from backend.scrapers.reddit_scraper import scrape_reddit
from backend.scrapers.google_search_scraper import scrape_google_search
from backend.pipeline.sentiment import analyze_sentiment
from backend.celery_app import celery

BATCH_SIZE = 100

def process_and_store(items: list, product_id: int, qdrant: QdrantDB):
    total_items = len(items)
    total_batches = math.ceil(total_items / BATCH_SIZE)

    print(f"Preparing to upsert {total_items} items in {total_batches} batches of {BATCH_SIZE}...")

    payloads_to_upsert = []

    for i, item in enumerate(tqdm(items, desc="Processing Items")):
        source_id = item.get("source_id")
        content = item.get("content")

        if not source_id or not content or not content.strip():
            print(f"Skipping item due to missing ID or invalid content.")
            continue

        # Run sentiment analysis for all content
        sentiment_result = analyze_sentiment(content)

        payload = {
            "product_id": product_id,
            "source": item.get("source"),
            "external_id": source_id,
            "content": content,
            "created_at": item.get("created_at"), # Will be None for Google results
            "sentiment_label": sentiment_result.get("label", "neutral"),
            "sentiment_compound": sentiment_result.get("compound", 0.0)
        }
        payloads_to_upsert.append(payload)

        if (len(payloads_to_upsert) == BATCH_SIZE) or (i == total_items - 1):
            if payloads_to_upsert:
                print(f"\nUpserting batch {len(payloads_to_upsert)} items...")
                qdrant.upsert_many_feedbacks(payloads_to_upsert)
                payloads_to_upsert.clear()

    print(f"Successfully upserted all items.")

@celery.task
def run_full_ingest_task(product_id: int):
    print(f"--- Starting background ingestion task for product_id: {product_id} ---")
    db: Session = SessionLocal()
    qdrant_client = QdrantDB()

    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product or not product.config:
            print(f"Error: Product or config not found for product_id: {product_id}")
            return

        config = product.config
        all_feedback = []
        # Use search_query if available, otherwise default to product name
        query = str(config.search_query or product.name) # Ensure query is string

        print(f"--- Starting Data Collection Phase for '{product.name}' using query: '{query}' ---")

        # --- SCRAPE YOUTUBE ---
        if config.youtube_keywords:
            print("--- Scraping YouTube ---")
            all_feedback.extend(
                scrape_youtube(
                    query=query,
                    keywords=config.youtube_keywords,
                    max_videos=15 # Reduced from 30 for faster testing, adjust as needed
                )
            )

        # --- SCRAPE REDDIT ---
        if config.reddit_subreddits:
            print("--- Scraping Reddit ---")
            all_feedback.extend(
                scrape_reddit(
                    search_queries=[query],
                    subreddits=config.reddit_subreddits,
                    limit=50
                )
            )

        # --- SCRAPE GOOGLE SEARCH ---
        print("--- Scraping Google Search Results (via SerpApi) ---")
        all_feedback.extend(
            scrape_google_search(
                query=query,
                limit=10 # Get top 10 results
            )
        )
        print(f"\n--- Data Collection Complete: Found {len(all_feedback)} total items from all sources ---")
        if all_feedback:
            process_and_store(all_feedback, product_id, qdrant_client)
        else:
            print("No feedback items collected from any source.")

        print(f"\n Ingestion task for product {product_id} finished successfully.")

    except Exception as e:
        # Add broader error catching for the whole task
        print(f" CRITICAL ERROR during ingestion task for product {product_id}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()