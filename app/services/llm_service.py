from typing import List

import os
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

load_dotenv()

client = InferenceClient(
    provider="novita",
    api_key=os.environ["HF_TOKEN"],
)

def generate_answer(question: str, context_chunks: List[str]) -> str:
    f"""
    Генерирует ответ на вопрос, используя контекст из чанков.
    Использует API Llama-3.1-8B-Instruct.
    """

    context = "\n".join(context_chunks)
    
    completion = client.chat.completions.create(
        model="meta-llama/Llama-3.1-8B-Instruct",
        messages=[
            {"role": "system", 
            "content": "Ты - полезный ассистент. Отвечай на вопросы ТОЛЬКО на основе предоставленного контекста. "
            "Если ответа нет в контексте, скажи, что не можешь найти ответа на вопрос в документе."},
            {"role": "user", "content": f"""Контекст: {context} 
            Вопрос: {question} Ответ (только на основе контекста):"""
            }
        ],
        temperature=0.1,
        max_tokens=200
    )

    answer = completion.choices[0].message.content

    return answer

