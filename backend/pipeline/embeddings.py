import os
from sentence_transformers import SentenceTransformer

hf_token = os.getenv("HF_API_KEY") or os.getenv("HF_TOKEN")

try:
    model = SentenceTransformer('all-MiniLM-L6-v2', use_auth_token=hf_token)
except Exception as e:
    raise RuntimeError(f"Failed to load embedding model: {e}")

def get_embedding(text: str):
    """Generate a vector embedding for the given text."""
    if not text or not isinstance(text, str) or not text.strip():
        return None

    try:
        return model.encode(text, normalize_embeddings=True).tolist()
    except Exception as e:
        print(f"Embedding generation failed: {e}")
        return None
