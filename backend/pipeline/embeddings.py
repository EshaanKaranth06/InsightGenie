# backend/pipeline/embeddings.py
import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# Load environment variables from the .env file at the project root
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

# Get the token from the environment variable
hf_token = os.getenv("HF_API_KEY")

# Load the model, passing the token for authentication
# If the token is None, it will download anonymously as before.
model = SentenceTransformer('all-MiniLM-L6-v2', token=hf_token)

def get_embedding(text: str):
    """Generates a vector embedding for a given text."""
    if not text or not isinstance(text, str):
        return None
    return model.encode(text).tolist()