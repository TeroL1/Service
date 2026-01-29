import asyncio
import uvicorn
from fastapi import FastAPI
import os
from app.api import router

app = FastAPI(
    title="Document QA Service",
    description="Question answering over uploaded documents",
    version="0.3.1"
)

app.include_router(router)

API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8000"))

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Question answering over uploaded documents")
    parser.add_argument(
        "--mode",
        choices=["api", "bot", "both"],
        default="api",
        help="Режим запуска: api (только API), bot (только бот), both (API + бот)"
    )

    args = parser.parse_args()
    
    if args.mode == "api":
        print("Запуск только FastAPI...")
        uvicorn.run(app, host=API_HOST, port=API_PORT)
    
    elif args.mode == "bot":
        print("Запуск только Telegram-бота...")
        from app.bot import start_bot
        asyncio.run(start_bot())
    
    else: 
        print("Запуск API + бота одновременно...")
        
        async def run_both():
            from app.bot import start_bot
            
            config = uvicorn.Config(app, host=API_HOST, port=API_PORT, log_level="info")
            server = uvicorn.Server(config)
            
            await asyncio.gather(
                server.serve(),
                start_bot()
            )
        
        asyncio.run(run_both())