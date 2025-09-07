# backend/llm/engine.py
import os
import traceback
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

from backend.pipeline.vector_store import VectorStore
from backend.pipeline.embeddings import get_embedding
from backend.db.models import Feedback
from sqlalchemy.orm import Session

# Load .env variables
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

# --- Initialize the Hugging Face Inference Client for Fireworks AI ---
HF_TOKEN = os.getenv("HF_TOKEN")

class InsightEngine:
    def __init__(self, db_session: Session, vector_store: VectorStore):
        self.db = db_session
        self.vdb = vector_store
        
        if HF_TOKEN:
            self.client = InferenceClient(
                provider="fireworks-ai",
                api_key=HF_TOKEN
            )
            # Use the specified DeepSeek model
            self.model = "deepseek-ai/DeepSeek-V3.1"
        else:
            self.client = None
            print("WARNING: HF_TOKEN not found in .env file. InsightEngine will not work.")

    def answer_question(self, question: str):
        """Finds relevant feedback and uses the Fireworks AI API to generate a detailed analysis."""
        try:
            if not self.client:
                return "Error: Fireworks AI token (HF_TOKEN) is not configured. Please check your .env file."

            print(f"Received query: '{question}'. Finding relevant context...")
            query_vector = get_embedding(question)
            if not query_vector: return "Could not process the query."
            relevant_ids = self.vdb.search(query_vector, k=20)
            
            if relevant_ids:
                results = self.db.query(Feedback).filter(Feedback.id.in_(relevant_ids)).all()
                context_text = "\n".join([f"- {r.content}" for r in results])
                print(f"Found {len(results)} relevant comments to analyze.")
            else:
                context_text = "No relevant user comments were found in the database."
                print("No relevant comments found. Relying on general knowledge.")

            # --- System prompt for the model ---
            system_prompt = """You are a senior product analyst for InsightGenie. Your goal is to provide a detailed, unbiased summary based on user feedback. You will be given a user's question and a collection of relevant scraped user comments as 'Context'.

**Your Instructions:**
1.  **Primary Analysis:** First, thoroughly analyze the provided 'Context' from the scraped user comments.
2.  **Identify Themes:** Extract the main positive themes (Pros) and negative themes (Cons).
3.  **Find Quotes:** For each theme, select one or two short, impactful quotes from the 'Context' that best represent the user sentiment.
4.  **Formatting:** Structure your final answer in clear Markdown format. Use "## Pros" and "## Cons" headings. Each theme should be a bullet point."""
            
            # --- User prompt with the specific context ---
            user_prompt = f"""
**User's Question:**
{question}

**Context from Scraped Data:**
---
{context_text}
---
"""
            
            print(f"Generating detailed analysis with {self.model} via Fireworks AI...")
            
            # Use the OpenAI-compatible chat.completions.create method
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=1024,
                temperature=0.7,
                stream=False # Set to False to get the full response at once
            )
            
            return response.choices[0].message.content.strip()

        except Exception as e:
            print("\n--- ERROR in InsightEngine ---")
            traceback.print_exc()
            print("-----------------------------")
            return f"An error occurred while generating the analysis: {e}"