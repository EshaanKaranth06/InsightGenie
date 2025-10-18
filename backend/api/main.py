import os
from dotenv import load_dotenv

# --- ADD THIS BLOCK AT THE TOP ---
# This finds the .env file in the 'backend' folder, one level up from this 'api' folder
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)


from fastapi import FastAPI, BackgroundTasks, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.db import models
from backend.db.database import SessionLocal, engine
from backend.llm.engine import InsightEngine
from backend.pipeline.tasks import run_full_ingest_task
from backend.reports.report_gen import generate_and_email_report_task

models.Base.metadata.create_all(bind=engine)

insight_engine = InsightEngine()

app = FastAPI(
    title="InsightGenie API",
    description="API for scraping, analyzing, and reporting on customer feedback.",
    version="1.0.0"
)

class QuestionRequest(BaseModel):
    question: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "Welcome to InsightGenie API"}

@app.post("/products/{product_id}/ingest")
def trigger_ingestion(product_id: int, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_full_ingest_task, product_id)
    return {
        "status": "success",
        "message": f"Ingestion process for product {product_id} started in the background."
    }

@app.post("/products/{product_id}/ask")
def ask_question(product_id: int, request: QuestionRequest):
    try:
        generator = insight_engine.answer_question(
            question=request.question,
            product_id=product_id   # type: ignore
        )
        return StreamingResponse(generator, media_type="text/event-stream")
    except Exception as e:
        return StreamingResponse(
            iter([f"An unexpected error occurred: {e}"]),
            media_type="text/event-stream"
        )

@app.post("/products/{product_id}/email-report")
def email_product_report(product_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        return {"error": "Product not found"}

    recipient = os.getenv("EMAIL_RECIPIENT")
    if not recipient:
        return {
            "status": "error",
            "message": "Server is not configured with a recipient email. Please set EMAIL_RECIPIENT in the .env file."
        }
    
    background_tasks.add_task(
        generate_and_email_report_task,
        product_id=product_id,
        recipient_email=recipient,
        product_name=str(product.name)
    )
    
    return {"message": "Report generation has started. It will be sent to your email shortly."}