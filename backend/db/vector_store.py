import os
import uuid
from typing import List, Dict, Optional
from qdrant_client import QdrantClient, models
from ..pipeline.embeddings import get_embedding, model as embedding_model

dimension = embedding_model.get_sentence_embedding_dimension()
if not isinstance(dimension, int):
    raise ValueError("Could not determine the embedding dimension from the model.")
VECTOR_DIMENSION: int = dimension


def create_deterministic_id(source: str, external_id: str) -> str:
    id_string = f"{source}-{external_id}"
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, id_string))

class QdrantDB:
    def __init__(self, collection_name: str = "feedback_reviews"):
        self.collection_name = collection_name
        qdrant_url = os.getenv("QDRANT_URL")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")

        if not qdrant_url or not qdrant_api_key:
            raise ValueError("Qdrant environment variables are not set!")

        self.client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        self._initialize_collection()

    def _initialize_collection(self):
        try:
            self.client.get_collection(collection_name=self.collection_name)
        except Exception:
            self.client.recreate_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=VECTOR_DIMENSION,
                    distance=models.Distance.COSINE
                ),
            )
            # --- ADD THE NEW INDEX HERE ---
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="product_id",
                field_schema=models.PayloadSchemaType.INTEGER
            )
            # --- KEEP THE OLD INDEX AS WELL ---
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="source",
                field_schema=models.PayloadSchemaType.KEYWORD
            )

    def upsert_feedback(self, item: Dict) -> Optional[str]:
        content = item.get("content")
        if not content:
            print(f"Skipping feedback due to invalid content: ID {item.get('external_id')}")
            return None

        vector = get_embedding(content)
        if not vector:
            print(f"Skipping feedback due to embedding failure: ID {item.get('external_id')}")
            return None

        point_id = create_deterministic_id(item["source"], item["external_id"])
        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                models.PointStruct(id=point_id, vector=vector, payload=item)
            ],
            wait=True
        )
        return point_id

    def upsert_many_feedbacks(self, items: List[Dict]):
        points_to_upsert = []
        for item in items:
            content = item.get("content")
            if not content:
                print(f"Skipping feedback due to invalid content: ID {item.get('external_id')}")
                continue

            vector = get_embedding(content)
            if vector:
                point_id = create_deterministic_id(item["source"], item["external_id"])
                point = models.PointStruct(id=point_id, vector=vector, payload=item)
                points_to_upsert.append(point)
            else:
                 print(f"Skipping feedback due to embedding failure: ID {item.get('external_id')}")

        if points_to_upsert:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points_to_upsert,
                wait=True
            )