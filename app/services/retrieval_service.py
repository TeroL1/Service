from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder
import faiss 

model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

def compute_embeddings(chunks: List[str]) -> np.ndarray:
    """
    Преобразует список чанков в векторы
    """
    
    embeddings = model.encode(chunks, convert_to_numpy=True)
    faiss.normalize_L2(embeddings)

    return embeddings

dim = 384
index = faiss.IndexFlatL2(dim)
stored_chunks = []

def add_embeddings_to_index(embeddings: np.ndarray, chunks: List[str]):
    """
    Сохраняет embeddings в FAISS и текст в память
    """

    global index, stored_chunks
    index.add(embeddings)
    stored_chunks.extend(chunks)

def search(query: str, top_k: int = 10) -> List[str]:
    """
    Находит top_k похожих чанков на вопрос
    """

    global index, stored_chunks

    if index.ntotal == 0:
        raise ValueError("No documents indexed yet")

    query_embedding = model.encode([query], convert_to_numpy=True)
    faiss.normalize_L2(query_embedding)
    _, indices = index.search(query_embedding, top_k)
    results = [stored_chunks[i] for i in indices[0]]

    return results

def rerank(query: str, chunks: List[dict], top_k: int = 5):
    """
    Находит из предложенных раннее чанков top_k похожих на вопрос
    """

    pairs = [[query, chunk["text"]] for chunk in chunks]
    scores = reranker.predict(pairs)
    ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    
    return [chunks[i] for i in ranked_indices[:top_k]]

def reset_index():
    """
    Очистка индекса
    """

    global index, stored_chunks

    index.reset()
    stored_chunks.clear()

def get_stats():
    """
    Статистика
    """

    return {
        "num_chunks": len(stored_chunks),
        "index_size": index.ntotal if index else 0,
        "embedding_dim": index.d if index else None
    }