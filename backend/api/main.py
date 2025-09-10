import os
from fastapi import FastAPI, Depends, BackgroundTasks
from fastapi.responses import HTMLResponse
import markdown2
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# --- Local Module Imports ---
from backend.db.models import init_db
from backend.llm.engine import InsightEngine
from backend.pipeline.vector_store import VectorStore
from backend.pipeline.ingest import run_full_ingest

# Load .env file from the project root
load_dotenv()

app = FastAPI(title="InsightGenie API")

# --- Initialize DB and Vector Store on Startup ---
DB_URL = os.getenv("DATABASE_URL", "sqlite:///./backend/feedback.db")
SessionLocal = init_db(DB_URL)
vector_store = VectorStore(
    index_path="backend/faiss_index.bin",
    map_path="backend/doc_map.pkl"
)

# --- THIS IS THE MISSING SECTION ---
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
# --- END OF MISSING SECTION ---


# --- API Endpoints ---
@app.post("/ingest")
async def trigger_ingestion(background_tasks: BackgroundTasks):
    """Triggers the scraping and processing pipeline as a background job."""
    print("API: Received request to start ingestion.")
    background_tasks.add_task(run_full_ingest, vector_store)
    return {
        "status": "success",
        "message": "Ingestion process started in the background. Check server logs for progress."
    }

@app.get("/query")
async def query_insights_json(question: str, engine: InsightEngine = Depends(get_engine)):
    """Asks a question and returns the raw analysis in JSON format."""
    answer = engine.answer_question(question)
    return {"answer": answer}

@app.get("/query/html", response_class=HTMLResponse)
async def query_insights_html(question: str, engine: InsightEngine = Depends(get_engine)):
    """Asks a question and returns the analysis as a polished HTML page."""
    markdown_answer = engine.answer_question(question)
    html_content = markdown2.markdown(
        markdown_answer, 
        extras=["fenced-code-blocks", "tables", "cuddled-lists"]
    )
    html_with_style = f"""
    <html>
        <head>
            <style>
                body {{ font-family: sans-serif; line-height: 1.6; padding: 2em; max-width: 800px; margin: auto; }}
                h2 {{ border-bottom: 1px solid #ccc; padding-bottom: 5px; }}
                blockquote {{ border-left: 3px solid #eee; padding-left: 1em; margin-left: 0; color: #555; }}
            </style>
        </head>
        <body>
            <h1>InsightGenie Analysis</h1>
            <h3>Query: "{question}"</h3>
            <hr>
            {html_content}
        </body>
    </html>
    """
    return HTMLResponse(content=html_with_style)