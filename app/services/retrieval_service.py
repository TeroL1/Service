from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder

from app.database import SessionLocal, Document, Embedding, get_user_settings

model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-mpnet-base-v2")
reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

def compute_embeddings(chunks: List[str]) -> np.ndarray:
    """Преобразует список чанков в векторы"""

    embeddings = model.encode(chunks, convert_to_numpy=True, normalize_embeddings=True)
    return embeddings

def add_document_to_db(user_id: int, filename: str, content: str, chunks: List[str], embeddings: np.ndarray):
    """Сохраняет документ и embeddings в БД"""

    db = SessionLocal()

    try:
        doc = Document(
            user_id=user_id,
            filename=filename,
            content=content
        )

        db.add(doc)
        db.commit()
        db.refresh(doc)
        
        for idx, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            embedding = Embedding(
                document_id=doc.id,
                user_id=user_id,
                chunk_text=chunk,
                embedding=emb.tolist(),
                chunk_index=idx,
                document_name=filename
            )

            db.add(embedding)
        
        db.commit()
        return doc.id
    
    finally:
        db.close()

def search(request) -> List[dict]:
    """Находит похожие чанки для пользователя"""

    db = SessionLocal()
    try:
        settings = get_user_settings(request.user_id)
        top_k = settings.get("retrieval_top_k", 15) if settings else 15
        
        query_embedding = model.encode([request.question], convert_to_numpy=True, normalize_embeddings=True)[0]
        
        results = db.query(
            Embedding.chunk_text,
            Embedding.document_name,
            Embedding.embedding.cosine_distance(query_embedding).label('distance')
        ).filter(Embedding.user_id == request.user_id).order_by('distance').limit(top_k).all()
        
        if not results:
            raise ValueError("No documents indexed yet")
        
        return [
            {
                "text": r.chunk_text,
                "document": r.document_name,
                "score": 1 - r.distance
            }
            for r in results
        ]
    finally:
        db.close()

def rerank(request, chunks: List[dict]) -> List[dict]:
    """Находит из предложенных чанков top_k похожих на вопрос"""
    
    settings = get_user_settings(request.user_id)
    top_k = settings.get("rerank_top_k", 5) if settings else 5
    
    pairs = [[request.question, chunk["text"]] for chunk in chunks]
    scores = reranker.predict(pairs)
    ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    
    return [chunks[i] for i in ranked_indices[:top_k]]