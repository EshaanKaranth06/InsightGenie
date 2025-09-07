import os
import traceback
from tqdm import tqdm
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from datetime import datetime

# --- Local Module Imports ---
from backend.scrapers.youtube_scraper import scrape_youtube
from backend.scrapers.reddit_scraper import scrape_reddit
from backend.pipeline.embeddings import get_embedding
from backend.pipeline.vector_store import VectorStore
from backend.db.models import Feedback, init_db
from backend.config import SCRAPER_CONFIG

# Load .env
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

# Ensure Feedback model has unique constraint:
# source_id = Column(String, unique=True, index=True)

def process_and_store(items: list, session: Session, vector_store: VectorStore):
    """Cleans, embeds, and stores feedback in SQL and a vector DB."""
    print("Processing, embedding, and storing feedback...")

    new_doc_ids = []
    new_vectors = []

    for item in tqdm(items, desc="Processing Items"):
        try:
            # Use stable source_id from scraper
            source_id = item.get("source_id")  # Must be YouTube video ID or Reddit post ID
            if not source_id:
                continue  # Skip if no stable ID

            # Skip if already exists in DB
            if session.query(Feedback).filter_by(source_id=source_id).first():
                continue

            # Parse created_at string
            date_str = item.get("created_at")
            if isinstance(date_str, str):
                if date_str.endswith('Z'):
                    date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                else:
                    date_obj = datetime.fromisoformat(date_str)
            else:
                date_obj = date_str

            # Create Feedback object
            new_feedback = Feedback(
                source_id=source_id,
                source=item.get("source"),
                content=item.get("content"),
                created_at=date_obj
            )
            session.add(new_feedback)
            session.flush()  # Get ID without committing yet

            # Generate embedding
            vector = get_embedding(new_feedback.content)
            if vector:
                new_doc_ids.append(new_feedback.id)
                new_vectors.append(vector)

        except (SQLAlchemyError, TypeError, ValueError, IntegrityError):
            print(f"\n--- ERROR processing item {item.get('source_id')} ---")
            traceback.print_exc()
            session.rollback()

    # Add vectors in one batch
    if new_vectors:
        vector_store.add_documents(new_doc_ids, new_vectors)
        print(f"Added {len(new_vectors)} new vectors to the vector store.")

    session.commit()
    print("Database and vector store updates complete.")


def run_full_ingest(vector_store: VectorStore):
    """Scrape all sources and process data, safely skipping already-ingested items."""
    DB_URL = os.getenv("DATABASE_URL", "sqlite:///./backend/feedback.db")
    SessionLocal = init_db(DB_URL)
    db_session = SessionLocal()

    try:
        cfg = SCRAPER_CONFIG
        all_feedback = []
        print("--- Starting Data Collection Phase ---")

        # --- YouTube ---
        if "youtube" in cfg:
            yt_conf = cfg["youtube"]
            query = cfg.get("search_query", cfg.get("product_name"))
            all_feedback.extend(
                scrape_youtube(
                    query=query,
                    keywords=yt_conf.get("keywords_to_filter", []),
                    max_videos=yt_conf.get("max_videos", 10)
                )
            )

        # --- Reddit ---
        if "reddit" in cfg:
            rconf = cfg["reddit"]
            query = cfg.get("search_query", cfg.get("product_name"))
            all_feedback.extend(
                scrape_reddit(
                    search_queries=[query],
                    subreddits=rconf.get("subreddits"),
                    limit=rconf.get("max_posts", 50)
                )
            )

        print(f"\n--- Data Collection Complete: Found {len(all_feedback)} items ---")
        process_and_store(all_feedback, db_session, vector_store)
        print("\n✅ Ingestion pipeline finished successfully.")

    finally:
        db_session.close()
        print("Database session closed.")
