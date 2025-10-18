import os
import traceback
from huggingface_hub import InferenceClient
from qdrant_client import QdrantClient,models
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
                api_key=qdrant_api_key
            )
            print(f"Connected to Qdrant Cloud at {qdrant_url}")
        else:
            raise ValueError(
                "Qdrant Cloud env vars missing!"
            )

        hf_token = os.getenv("HF_TOKEN")
        if hf_token:
            self.llm_client = InferenceClient(provider="fireworks-ai", api_key=hf_token)
            self.model = "openai/gpt-oss-20b"
        else:
            raise ValueError("HF_TOKEN environment variable is not set!")

    def answer_question(self, question: str, product_id: int):
        try:
            print("--- Insight Engine Started ---")
            if not self.llm_client:
                yield "Error: HF_TOKEN is not configured."
                return

            print(f"🚦 STEP 1: Processing query: '{question}'")
            query_vector = get_embedding(question)
            if not query_vector:
                yield "Error: Could not process the query into an embedding."
                return
            print("✅ STEP 1: Query processed successfully.")


            print(f"🚦 STEP 2: Searching Qdrant for product_id {product_id}...")
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
                limit=25,
                with_payload=True
            )
            print("✅ STEP 2: Qdrant search complete.")


            if not search_results:
                context_text = "No relevant user comments were found in the database."
            else:
                print(f"Found {len(search_results)} relevant comments. Pre-analyzing sentiment...")
                enriched_context = []
                for result in search_results:
                    payload = getattr(result, "payload", None) or {}
                    text = payload.get("content", "")
                    if text:
                        sentiment = analyze_sentiment(text) or {}
                        label = sentiment.get("label", "neutral")
                        enriched_context.append(f"({label}) {text}")
                context_text = "\n".join(enriched_context)

            
            system_prompt = """You are a senior product analyst for InsightGenie. Your goal is to provide a detailed, unbiased summary based on user feedback. You will be given a user's question and a collection of scraped user comments as 'Context'.

**Your Instructions:**

1. **Analyze Context:** The user comments in the 'Context' have been pre-analyzed for sentiment and are prefixed with `(positive)`, `(negative)`, or `(neutral)`. Use these labels to inform your analysis.
2. **Identify Themes:** Based on the context, extract the main positive themes (Pros) and negative themes (Cons).
3. **Summarize Sentiment:** Briefly summarize the overall sentiment distribution (e.g., "The feedback was mostly positive...").
4. **Find Quotes:** For each theme, select one or two short, impactful quotes from the 'Context' that best represent the user sentiment.
5. **Formatting:** Structure your final answer in clear Markdown format. Use "## Pros" and "## Cons" headings. Each theme should be a bullet point.""" 

            user_prompt = f"""
**User's Question:**
{question}

**Context from Scraped Data:**
---
{context_text}
---
"""

            print(f"🚦 STEP 3: Generating analysis with {self.model} via Fireworks AI...")
            stream = self.llm_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=1024,
                temperature=0.6,
                stream=True
            )
            print("✅ STEP 3: Stream from LLM received. Yielding content...")

            for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    yield content

            print("\n--- Insight Engine Finished ---")

        except Exception as e:
            print(f"An error occurred while generating the analysis: {e}")
            traceback.print_exc()
            yield f"\n\n**An error occurred:** {e}"
