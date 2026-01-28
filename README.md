# Document QA Service (RAG-сервис)

## Описание

Проект реализует сервис вопрос-ответ по загруженным документам на основе retrieval-augmented generation (RAG).  
Он позволяет:

1. Загружать документы (.txt, .docx, .pdf) в память и индексировать их с помощью FAISS.  
2. Разбивать текст на чанки с перекрытием для точного поиска.  
3. Представлять каждый чанк в виде вектора эмбеддинга с помощью SentenceTransformers.  
4. Выполнять семантический поиск по документам (cosine similarity через L2 нормализованные векторы).  
5. Ранжировать найденные фрагменты с помощью простого lexical reranking.  
6. Генерировать ответы с помощью LLM ("Llama-3.1-8B-Instruct").  
7. Взаимодействовать с сервисом через Telegram-бота (все функции из API).

## Установка

1. Клонируйте репозиторий
2. Создайте .env и добавьте свой HF_TOKEN
3. Создайте виртуальное окружение:
   `python -m venv venv
    venv\Scripts\Activate.ps1`
4. Установите зависимости:
   `pip install -r requirements.txt`
5. Опционально в .env добавьте:

BOT_TOKEN (если пользуетесь ботом в ТГ)

API_URL (куда подключается телеграм бот - для локальной разработки совпадает с API_HOST + API_PORT)

API_HOST (где запускается API сервер)

API_PORT (порт)

## Запуск сервиса

API:
`python -m app.main --mode api`

Bot с внешним API (API должен быть запущен отдельно!!!):
`python -m app.main --mode bot`

Оба (Рекомендуется для локального запуска):
`python -m app.main --mode both`

## API Endpoints

GET /health
Проверяет, работает ли сервис.
Ответ: {"status": "ok"}

POST /documents
Параметр: file (только .txt)
Разбивает текст на чанки, вычисляет embeddings и сохраняет их в индекс FAISS.
Пример ответа: {"filename": "example.txt", "num_chunks": 12, "chunk_preview": "Первый фрагмент текста документа..."}

POST /ask
Параметр: JSON {"question": "Ваш вопрос"}
Ищет релевантные чанки, rerank и генерирует ответ через локальную LLM.
Пример ответа: {"question": "Что такое RAG?", "answer": "RAG — это Retrieval-Augmented Generation..."}

GET /stats
Возвращает количество чанков, размер индекса и размерность embeddings.
Пример ответа: {"num_chunks": 12, "index_size": 12, "embedding_dim": 384}

POST /reset
Очищает FAISS и удаляет все сохранённые чанки.
Пример ответа: {"status": "index reset"}
