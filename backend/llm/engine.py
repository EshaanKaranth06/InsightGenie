import os
import traceback
from collections import Counter
from huggingface_hub import InferenceClient
from qdrant_client import QdrantClient, models
from backend.pipeline.sentiment import analyze_sentiment
from backend.pipeline.embeddings import get_embedding

class InsightEngine:
    def __init__(self):
        qdrant_url = os.getenv("QDRANT_URL")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")
        self.collection_name = "feedback_reviews"

        if qdrant_url and qdrant_api_key:
            self.qdrant_client = QdrantClient(
                url=qdrant_url,
                api_key=qdrant_api_key,
                timeout=60
            )
            print(f"Connected to Qdrant Cloud at {qdrant_url}")
        else:
            raise ValueError("Qdrant Cloud env vars missing!")

        hf_token = os.getenv("HF_TOKEN")
        if hf_token:
            self.llm_client = InferenceClient(provider="fireworks-ai", api_key=hf_token)
            self.model = "openai/gpt-oss-120b" 
            print(f"Using LLM model via Fireworks AI: {self.model}")
        else:
            raise ValueError("HF_TOKEN environment variable is not set!")

    def _calculate_sentiment_stats(self, reviews):
        """Calculate sentiment distribution statistics"""
        sentiment_counts = Counter()
        rating_counts = Counter()
        
        for review in reviews:
            payload = getattr(review, "payload", None) or {}
            
            # Count sentiment labels
            sentiment = payload.get("sentiment_label", "neutral")
            sentiment_counts[sentiment] += 1
            
            # Count ratings if available
            rating = payload.get("rating")
            if rating:
                rating_counts[rating] += 1
        
        total = len(reviews)
        
        # Calculate percentages
        sentiment_breakdown = {
            label: round((count / total) * 100, 1) if total > 0 else 0
            for label, count in sentiment_counts.items()
        }
        
        rating_breakdown = {
            f"{rating}-star": round((count / total) * 100, 1) if total > 0 else 0
            for rating, count in rating_counts.items()
        }
        
        return sentiment_breakdown, rating_breakdown

    def answer_question(self, question: str, product_id: int, product_name: str | None = None):
        """
        Generate insights based on user question and product reviews
        
        Args:
            question: User's query about the product
            product_id: ID of the product to analyze
            product_name: Name of the product (optional, for better formatting)
        """
        try:
            print("--- Insight Engine Started ---")
            if not self.llm_client:
                yield "Error: HF_TOKEN is not configured."
                return

            print(f"STEP 1: Processing query: '{question}'")
            query_vector = get_embedding(question)
            if not query_vector:
                yield "Error: Could not process the query into an embedding."
                return
            print("STEP 1: Query processed successfully.")

            print(f"STEP 2: Searching Qdrant for product_id {product_id}...")
            search_results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="product_id",
                            match=models.MatchValue(value=product_id)
                        )
                    ]
                ),
                limit=100, 
                with_payload=True
            )
            print("STEP 2: Qdrant search complete.")

            if not search_results:
                yield "## Analysis Result\n\n No relevant user feedback was found for this product in the database.\n\nPlease ensure reviews have been scraped and indexed for this product."
                return

            print(f"Found {len(search_results)} relevant comments.")
            
            # Calculate sentiment statistics
            sentiment_breakdown, rating_breakdown = self._calculate_sentiment_stats(search_results)
            
            # Enrich context with sentiment labels
            enriched_context = []
            for result in search_results:
                payload = getattr(result, "payload", None) or {}
                text = payload.get("content", "")
                rating = payload.get("rating")
                source = payload.get("source", "")
                label = payload.get("sentiment_label", "neutral")
                if text:
                    sentiment = analyze_sentiment(text) or {}
                    label = sentiment.get("label", "neutral")
                    
                    # Format: [sentiment] (rating★) "review text" - source
                    rating_str = f"({rating}★)" if rating else ""
                    source_str = f" - {source}" if source else ""
                    enriched_context.append(f"[{label.upper()}] {rating_str} {text}{source_str}")
            
            context_text = "\n".join(enriched_context)
            
            # Enhanced system prompt with STRICT product-only focus
            system_prompt = """You are a helpful product analyst assistant for InsightGenie. 
Your task is to analyze customer feedback context provided and answer the user's specific question accurately and concisely based ONLY on that context.

**CRITICAL RULES:**
1.  **Focus ONLY on the PRODUCT:** Ignore any comments about videos, reviews, reviewers, channels, or production quality. Analyze only feedback related to the product itself (features, performance, quality, user experience).
2.  **Use the Provided Context:** Base your answer strictly on the customer feedback provided in the 'Context' section of the user prompt. Do not add outside information or opinions.
3.  **Answer the Specific Question:** Directly address the user's question. If the question asks for Pros, list only pros. If it asks for Cons, list only cons. If it asks for an overall summary, provide only that.
4.  **Be Clear and Concise:** Use clear language. Use bullet points for lists where appropriate (like for Pros, Cons, or Feature Requests)."""

            user_prompt = f"""
**User's Question:**
{question}

**Product Name:**
{product_name if product_name else f"Product ID: {product_id}"}

**Customer Feedback Context (Total: {len(search_results)} reviews):**
---
{context_text}
---

**Pre-calculated Statistics:**
- Sentiment Breakdown: {sentiment_breakdown}
- Rating Distribution: {rating_breakdown if rating_breakdown else "Not available"}

**Reminder:** Analyze ONLY the product itself based on the context provided. Answer only the specific question asked above.

Your Answer:"""

            print(f"\n--- CONTEXT FOR '{question}' ---")
            print(context_text)
            print("--- END CONTEXT ---\n")
            print(f"STEP 3: Generating analysis with {self.model} via Fireworks AI...")
            stream = self.llm_client.chat.completions.create(
                model=self.model, 
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=1000, # Can reduce this slightly now
                temperature=0.3, # Lower temp for more factual answers
                stream=True
            )
            print("STEP 3: Stream from LLM received. Yielding content...")

            for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    yield content

            print("\n--- Insight Engine Finished ---")

        except Exception as e:
            print(f"An error occurred while generating the analysis: {e}")
            traceback.print_exc()
            yield f"\n\n** An error occurred:** {e}\n\nPlease check your configuration and try again."

    def generate_report(self, product_id: int, product_name: str, time_period: str = "weekly"):
       
        question = f"Provide a comprehensive analysis of all customer feedback for {product_name}, focusing exclusively on the product itself - its features, performance, quality, and user experience. Ignore all comments about videos or reviews."
        
        yield f"# InsightGenie Summary Report\n"
        yield f"## {product_name}\n"
        
        import datetime
        current_time = datetime.datetime.now().strftime("%Y-%m-%d")
        yield f"**Generated on:** {current_time}\n\n"
        
        # Stream the main analysis
        for chunk in self.answer_question(question, product_id, product_name):
            yield chunk