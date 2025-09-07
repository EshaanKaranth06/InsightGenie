import os
import json
import traceback
import vertexai
from vertexai.generative_models import GenerativeModel
from dotenv import load_dotenv

# Load .env variables and initialize Vertex AI
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

try:
    GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
    if GCP_PROJECT_ID:
        vertexai.init(project=GCP_PROJECT_ID, location="us-central1")
    else:
        print("WARNING: GCP_PROJECT_ID not found in .env file. LLM Analyzer will not work.")
except Exception as e:
    print(f"Failed to initialize Vertex AI: {e}")

def analyze_text_with_llm(text: str):
    """
    Analyzes a given piece of text using Vertex AI to extract structured data.
    """
    if not GCP_PROJECT_ID: return {"sentiment": "Error", "topics": [], "summary": "Vertex AI not initialized."}
    
    # Use the fast and cost-effective Flash model for this high-volume task
    model = GenerativeModel("gemini-1.5-flash-001")

    prompt = f"""
    Analyze the following product feedback text. Provide a structured analysis
    in a valid JSON format.

    The JSON output must have these exact keys:
    - "sentiment": (string) Classify sentiment as "Positive", "Negative", or "Neutral".
    - "topics": (list of strings) Identify key topics or product features mentioned.
    - "summary": (string) A concise, one-sentence summary of the user's main point.

    Do not include any text, explanations, or markdown formatting.

    Text to analyze:
    ---
    {text}
    ---
    """
    try:
        response = model.generate_content(prompt)
        cleaned_response = response.text.strip().replace('```json', '').replace('```', '')
        analysis = json.loads(cleaned_response)
        
        if not all(k in analysis for k in ["sentiment", "topics", "summary"]):
            raise KeyError("LLM response was missing one or more required keys.")
            
        return analysis
    except Exception as e:
        print(f"An error occurred during text analysis:")
        traceback.print_exc()
        return {"sentiment": "Error", "topics": [], "summary": "Analysis failed."}

def query_llm_for_product_info(product_name: str, question: str):
    """
    Uses the Vertex AI model's general knowledge to answer a question.
    """
    if not GCP_PROJECT_ID: return "Vertex AI not initialized. Cannot query for product info."
    
    print(f"Querying LLM for: '{question}'...")
    # Use the powerful Pro model for general knowledge questions
    model = GenerativeModel("gemini-1.5-pro-001")

    prompt = f"""
    You are a concise and knowledgeable product expert.
    Based on your general knowledge, please answer the following question about "{product_name}".
    Provide a direct and clear answer. If the question asks for a list, use bullet points.

    Question: {question}
    """
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"An unexpected error occurred during the LLM query:")
        traceback.print_exc()
        return "Sorry, I was unable to answer that question."


# --- Example Usage ---
if __name__ == "__main__":
    # Test Function 1: Analyzing a scraped review
    sample_review = "I find Nandini milk to be really good value for the price, and the taste is consistent. However, I've noticed the packaging for the toned milk can sometimes leak."
    print("--- Testing Text Analysis ---")
    analysis_result = analyze_text_with_llm(sample_review)
    print(json.dumps(analysis_result, indent=2))
    print("-" * 20)

    # Test Function 2: Asking a general knowledge question
    product = "Nandini Milk"
    question = "What are the common opinions about Nandini Milk's quality and price in Karnataka?"
    print("\n--- Testing General Knowledge Query ---")
    query_result = query_llm_for_product_info(product, question)
    print(query_result)
    print("-" * 20)