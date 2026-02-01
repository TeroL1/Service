from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel

from app.services.document_service import read_text_from_file, chunk_text
from app.services.retrieval_service import search, compute_embeddings, add_document_to_db, rerank
from app.services.llm_service import generate_answer, generate_query_variations
from app.database import get_user_stats, delete_user_data, get_or_create_user

router = APIRouter()

class AskRequest(BaseModel):
    user_id: int
    question: str

@router.get("/health")
def health_check():
    return {"status": "ok"}

@router.post("/documents")
def upload_document(user_id: int, file: UploadFile = File(...)):
    get_or_create_user(user_id)

    text = read_text_from_file(file)
    raw_chunks = chunk_text(text)
    chunks = [
        {"text": chunk, "document": file.filename, "chunk_id": i}
        
        for i, chunk in enumerate(raw_chunks)
    ]

    embeddings = compute_embeddings([chunk["text"] for chunk in chunks])
    add_document_to_db(user_id, file.filename, text, raw_chunks, embeddings)
    
    return {
        "filename": file.filename,
        "num_chunks": len(chunks),
        "chunk_preview": chunks[0]["text"][:200]
    }

@router.post("/ask")
def ask_question(request: AskRequest):
    get_or_create_user(request.user_id)

    try:
        #questions = generate_query_variations(request.question, num_variations=2)
        retrieved = search(request)
        reranked = rerank(request, retrieved)
        context_chunks = [chunk["text"] for chunk in reranked]
        answer = generate_answer(request.question, context_chunks)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "question": request.question,
        "answer": answer
    }

@router.get("/stats/{user_id}")
def stats(user_id: int):
    get_or_create_user(user_id)

    return get_user_stats(user_id)

@router.post("/reset/{user_id}")
def reset(user_id: int):
    get_or_create_user(user_id)
    delete_user_data(user_id)
    return {"status": "user data reset"}