from sqlalchemy.orm import Session
from tqdm import tqdm

from backend.db.database import SessionLocal
from backend.db.models import Product
from backend.db.vector_store import QdrantDB
from backend.scrapers.youtube_scraper import scrape_youtube
from backend.scrapers.reddit_scraper import scrape_reddit


def process_and_store(items: list, product_id: int, qdrant: QdrantDB):
    payloads_to_upsert = []
    for item in tqdm(items, desc="Preparing Payloads"):
        source_id = item.get("source_id")
        if not source_id:
            continue

        payload = {
            "product_id": product_id,
            "source": item.get("source"),
            "external_id": source_id,
            "content": item.get("content"),
            "created_at": item.get("created_at")
        }
        payloads_to_upsert.append(payload)

    if payloads_to_upsert:
        qdrant.upsert_many_feedbacks(payloads_to_upsert)
        print(f"Successfully upserted {len(payloads_to_upsert)} items for product {product_id}.")


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
        
        query = str(config.search_query or product.name)

        print(f"--- Starting Data Collection Phase for '{product.name}' ---")

        if config.youtube_keywords:
            all_feedback.extend(
                scrape_youtube(
                    query=query,
                    keywords=config.youtube_keywords,
                    max_videos=10
                )
            )

        if config.reddit_subreddits:
            all_feedback.extend(
                scrape_reddit(
                    search_queries=[query],
                    subreddits=config.reddit_subreddits,
                    limit=50
                )
            )

        print(f"\n--- Data Collection Complete: Found {len(all_feedback)} items ---")
        if all_feedback:
            process_and_store(all_feedback, product_id, qdrant_client)

        print(f"\n✅ Ingestion task for product {product_id} finished successfully.")

    finally:
        db.close()