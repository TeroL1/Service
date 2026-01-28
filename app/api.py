from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel

from app.services.document_service import read_text_from_file, chunk_text
from app.services.retrieval_service import search, compute_embeddings, add_embeddings_to_index, rerank, get_stats, reset_index
from app.services.llm_service import generate_answer

router = APIRouter()

class AskRequest(BaseModel):
    question: str

@router.get("/health")
def health_check():
    return {"status": "ok"}

@router.post("/documents")
def upload_document(file: UploadFile = File(...)):
    text = read_text_from_file(file)
    raw_chunks = chunk_text(text)
    chunks = [
        {"text": chunk, "document": file.filename, "chunk_id": i}
        
        for i, chunk in enumerate(raw_chunks)
    ]

    embeddings = compute_embeddings([chunk["text"] for chunk in chunks])
    add_embeddings_to_index(embeddings, chunks)

    
    return {
        "filename": file.filename,
        "num_chunks": len(chunks),
        "chunk_preview": chunks[0]["text"][:200]
    }

@router.post("/ask")
def ask_question(request: AskRequest):
    try:
        retrieved = search(request.question, top_k=15)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    reranked = rerank(request.question, retrieved, top_k=5)
    context_chunks = [chunk["text"] for chunk in reranked]
    answer = generate_answer(request.question, context_chunks)

    return {
        "question": request.question,
        "answer": answer
    }

@router.get("/stats")
def stats():
    return get_stats()

@router.post("/reset")
def reset():
    reset_index()
    return {"status": "index reset"}