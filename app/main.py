from fastapi import FastAPI
from app.api import router

app = FastAPI(
    title="Document QA Service",
    description="Question answering over uploaded documents",
    version="0.2.0"
)

app.include_router(router)