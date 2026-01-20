from fastapi import UploadFile
from typing import List

def read_text_from_file(file: UploadFile) -> str:
    """
    Читает загруженный файл и возвращает текст.
    Поддерживается лишь .txt
    """

    if not file.filename.endswith(".txt"):
        raise ValueError("Only .txt files are supported")

    content_bytes = file.file.read()
    text = content_bytes.decode("utf-8")

    return text

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
    """
    Разбивает текст на чанки фиксированного размера с перекрытием
    """

    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)

        start = end - overlap

    return chunks
