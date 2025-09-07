import os
from fastapi import FastAPI, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from backend.db.models import init_db
from backend.llm.engine import InsightEngine
from backend.pipeline.vector_store import VectorStore
from backend.pipeline.ingest import run_full_ingest

load_dotenv()

app = FastAPI(title="InsightGenie API")

# --- Initialize DB and Vector Store on Startup ---
DB_URL = os.getenv("DATABASE_URL", "sqlite:///./backend/feedback.db")
SessionLocal = init_db(DB_URL)
vector_store = VectorStore(
    index_path="backend/faiss_index.bin",
    map_path="backend/doc_map.pkl"
)

# --- Dependencies ---
def get_db():
    """Dependency to get a DB session for a single request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_engine(db: Session = Depends(get_db)):
    """Dependency to get an instance of the InsightEngine."""
    return InsightEngine(db_session=db, vector_store=vector_store)

# --- API Endpoints ---
@app.post("/ingest")
async def trigger_ingestion(background_tasks: BackgroundTasks):
    """
    Triggers the scraping and processing pipeline as a background job.
    """
    print("API: Received request to start ingestion.")
    background_tasks.add_task(run_full_ingest, vector_store)
    
    return {
        "status": "success",
        "message": "Ingestion process started in the background. Check server logs for progress."
    }

@app.get("/query")
async def query_insights(question: str, engine: InsightEngine = Depends(get_engine)):
    """Asks a question about the product feedback using the vector store."""
    answer = engine.answer_question(question)
    return {"answer": answer}