import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from google import genai
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv('BOT_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

client = genai.Client(api_key=GEMINI_API_KEY)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("Я бот gemini и я очень классный!")


@dp.message(F.text)
async def chat_gemini(message: Message):
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=message.text
        )

        if response.text:
            await message.answer(response.text)
        else:
            await message.answer("ответа нет.")
    except Exception as e:
        print(f"ошибка: {e}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен")