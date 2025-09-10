
import os
import traceback
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

from backend.pipeline.vector_store import VectorStore
from backend.pipeline.embeddings import get_embedding
from backend.db.models import Feedback
from sqlalchemy.orm import Session
from backend.pipeline.sentiment import analyze_sentiment # <-- IMPORT VADER

# ... (dotenv loading and client initialization)

class InsightEngine:
    def __init__(self, db_session: Session, vector_store: VectorStore):
        # ... (init method is the same)
        self.db = db_session
        self.vdb = vector_store
        
        HF_TOKEN = os.getenv("HF_TOKEN")
        if HF_TOKEN:
            self.client = InferenceClient(provider="fireworks-ai", api_key=HF_TOKEN)
            self.model = "deepseek-ai/DeepSeek-V3.1"
        else:
            self.client = None

    def answer_question(self, question: str):
        """Finds, pre-analyzes, and uses feedback to generate a detailed analysis."""
        try:
            if not self.client:
                return "Error: Fireworks AI token (HF_TOKEN) is not configured."

            print(f"Received query: '{question}'. Finding relevant context...")
            query_vector = get_embedding(question)
            if not query_vector: return "Could not process the query."
            relevant_ids = self.vdb.search(query_vector, k=20)
            
            context_text = "No relevant user comments were found in the database."
            if relevant_ids:
                results = self.db.query(Feedback).filter(Feedback.id.in_(relevant_ids)).all()
                print(f"Found {len(results)} relevant comments. Pre-analyzing sentiment with VADER...")
                
                # --- THIS IS THE NEW LOGIC ---
                # Pre-process each comment with VADER before building the final context
                enriched_context = []
                for res in results:
                    sentiment = analyze_sentiment(res.content)
                    sentiment_label = sentiment.get("label", "neutral")
                    enriched_context.append(f"({sentiment_label}) {res.content}")
                
                context_text = "\n".join(enriched_context)
                # --- END OF NEW LOGIC ---

            # --- UPDATED SYSTEM PROMPT ---
            system_prompt = """You are a senior product analyst for InsightGenie. Your goal is to provide a detailed, unbiased summary based on user feedback. You will be given a user's question and a collection of scraped user comments as 'Context'.

**Your Instructions:**
1.  **Analyze Context:** The user comments in the 'Context' have been pre-analyzed for sentiment and are prefixed with `(positive)`, `(negative)`, or `(neutral)`. Use these labels to inform your analysis.
2.  **Identify Themes:** Based on the context, extract the main positive themes (Pros) and negative themes (Cons).
3.  **Summarize Sentiment**: Briefly summarize the overall sentiment distribution (e.g., "The feedback was mostly positive...").
4.  **Find Quotes:** For each theme, select one or two short, impactful quotes from the 'Context' that best represent the user sentiment.
5.  **Formatting:** Structure your final answer in clear Markdown format. Use "## Pros" and "## Cons" headings. Each theme should be a bullet point."""
            
            user_prompt = f"""
**User's Question:**
{question}

**Context from Scraped Data:**
---
{context_text}
---
"""
            
            print(f"Generating detailed analysis with {self.model} via Fireworks AI...")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=1024,
                temperature=0.7,
                stream=False
            )
            
            return response.choices[0].message.content.strip()

        except Exception as e:
            # ... (error handling is the same)
            print(f"An error occurred while generating the analysis: {e}")
