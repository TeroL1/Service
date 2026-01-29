import asyncio
import aiohttp
import os
import tempfile
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_URL = os.getenv("API_URL", "http://localhost:8000")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Я бот для работы с документами.\n\n"
        "Отправь мне файл (.txt, .pdf, .docx) - я его проиндексирую\n"
        "Напиши вопрос - отвечу на основе загруженных документов\n\n"
        "Команды:\n"
        "/stats - статистика базы\n"
        "/reset - очистить базу"
    )

@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}/stats") as resp:
            stats = await resp.json()
            answer = ''.join([f'{name}: {value}\n' for name, value in stats.items()])
            await message.answer(f"Статистика:\n{answer}")

@dp.message(Command("reset"))
async def cmd_reset(message: Message):
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{API_URL}/reset") as resp:
            await message.answer("База очищена!")

@dp.message(lambda msg: msg.document is not None)
async def handle_document(message: Message):
    doc = message.document

    await message.answer("Обработка документа может занять какое-то время...")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=doc.file_name) as tmp:
        await bot.download(doc, destination=tmp.name)
        tmp_path = tmp.name
    
    try:
        async with aiohttp.ClientSession() as session:
            with open(tmp_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('file', f, filename=doc.file_name)
                
                async with session.post(f"{API_URL}/documents", data=data) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        await message.answer(
                            f"Документ обработан!\n"
                            f"Пример чанка: {result['chunk_preview']}\n"
                            f"Всего чанков: {result['num_chunks']}"
                        )
                    else:
                        error = await resp.text()
                        print(f"Ошибка: {str(error)}")
                        await message.answer(f"Извините, ошибка работы программы")

    except Exception as e:
        print(f"Ошибка обработки: {str(e)}")
        await message.answer(f"Извините, ошибка обработки")

    finally:
        os.remove(tmp_path)

@dp.message()
async def handle_question(message: Message):
    question = message.text
    
    await message.answer("Думаю...")
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{API_URL}/ask",
            json={"question": question}
        ) as resp:
            if resp.status == 200:
                result = await resp.json()
                await message.answer(f"{result['answer']}")
                
            else:
                error = await resp.text()
                print(f'Ошибка: {error}')
                await message.answer(f"Извините, ошибка работы программы")

async def start_bot():
    await dp.start_polling(bot)