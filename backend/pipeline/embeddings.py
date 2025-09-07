
import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

hf_token = os.getenv("HF_API_KEY")

model = SentenceTransformer('all-MiniLM-L6-v2', token=hf_token)

def get_embedding(text: str):
    """Generates a vector embedding for a given text."""
    if not text or not isinstance(text, str):
        return None
    return model.encode(text).tolist()
