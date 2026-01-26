from typing import List
from fastapi import UploadFile
import io
import pdfplumber
from unstructured.partition.docx import partition_docx

def read_text_from_file(file: UploadFile) -> str:
    """
    Читает загруженный файл и возвращает текст.
    Поддерживаются .txt, .pdf, .docx
    """
    filename = file.filename.lower()

    for extension, parser in PARSERS.items():
        if filename.endswith(extension):
            return parser(file)

    raise ValueError(f"Unsupported file type: {file.filename}")

def parse_txt(file: UploadFile) -> str:
    """
    Работает с .txt
    """
    
    content_bytes = file.file.read()
    return content_bytes.decode("utf-8")

def parse_pdf(file: UploadFile) -> str:
    """
    Работает с .pdf
    """

    text_pages = []
    with pdfplumber.open(file.file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_pages.append(page_text)

    return "\n".join(text_pages)

def parse_docx(file: UploadFile) -> str:
    """
    Работает с .docx
    """

    content = file.file.read()
    elements = partition_docx(file=io.BytesIO(content))
    text_parts = [str(el) for el in elements]
    
    return "\n".join(text_parts)

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

PARSERS = {
    ".txt": parse_txt,
    ".pdf": parse_pdf,
    ".docx": parse_docx,
}
