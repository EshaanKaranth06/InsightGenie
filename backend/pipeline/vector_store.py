# backend/pipeline/vector_store.py
import faiss
import numpy as np
import pickle
import os

class VectorStore:
    def __init__(self, dimension=384, index_path="backend/faiss_index.bin", map_path="backend/doc_map.pkl"):
        self.dimension = dimension
        self.index_path = index_path
        self.map_path = map_path
        
        # Load existing index and map if they exist
        if os.path.exists(index_path) and os.path.exists(map_path):
            print("Loading existing vector store from disk...")
            self.index = faiss.read_index(index_path)
            with open(map_path, "rb") as f:
                self.doc_map = pickle.load(f)
            self.next_idx = self.index.ntotal
            print(f"Loaded {self.index.ntotal} vectors.")
        else:
            print("Creating a new, empty vector store.")
            self.index = faiss.IndexFlatL2(dimension)
            self.doc_map = {} 
            self.next_idx = 0

    def add_documents(self, doc_ids: list, vectors: list):
        """Adds document vectors to the index."""
        if not vectors:
            return
        vectors_np = np.array(vectors, dtype='float32')
        self.index.add(vectors_np)
        for doc_id in doc_ids:
            self.doc_map[self.next_idx] = doc_id
            self.next_idx += 1
        self._save()

    def search(self, query_vector: list, k=5):
        """Searches for k-nearest neighbors to a query vector."""
        
        # Check if the index has any vectors before searching.
        if self.index.ntotal == 0:
            print("Vector store is empty. Returning no results.")
            return []
        
        query_np = np.array([query_vector], dtype='float32')
        distances, indices = self.index.search(query_np, k)
        
        # Filter out the -1 results which mean no neighbor was found
        found_ids = [self.doc_map[i] for i in indices[0] if i != -1]
        return found_ids

    def _save(self):
        """Saves the index and mapping to disk."""
        print(f"Saving index with {self.index.ntotal} vectors to {self.index_path}...")
        faiss.write_index(self.index, self.index_path)
        with open(self.map_path, "wb") as f:
            pickle.dump(self.doc_map, f)