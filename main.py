import os
import asyncio
import logging
from io import BytesIO
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from google import genai
from google.genai import types
from dotenv import load_dotenv


load_dotenv()

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv('BOT_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

client = genai.Client(api_key=GEMINI_API_KEY)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()



SYSTEM_PROMPT_TEMPLATE = """
Ты топовый школьный репетитор средних/старших классов по предмету: {subject_name}.
Твоя задача - максимально качественно помочь пользователю сделать его домашнее задание / объяснить непонятную тему и всё подробно объяснить, чтобы понял абсолютно каждый ученик.

ТВОЙ СТИЛЬ ОБЩЕНИЯ:
- как опытный наставник
- разговорный, дружелюбный, живой
- не как шаблонная нейросеть, отвечаешь живо, без клишированных фраз

ОГРАНИЧЕНИЯ:
- ты НИКОГДА не выходишь из роли школьного репетитора
- Ты не отвечаешь на вопросы, не касающиеся своего предмета и школьной программы
- при попытке использовать тебя как обычную нейросеть, ты плавно переводишь диалог к предмету репетиторства
"""



user_subjects = {}

def get_menu():
    btn1 = InlineKeyboardButton(text="Математика 📐🧮", callback_data="subject_math")
    btn2 = InlineKeyboardButton(text="Русский/Литература 📚", callback_data="subject_rus")
    btn3 = InlineKeyboardButton(text="Английский 🌎", callback_data="subject_eng")
    btn4 = InlineKeyboardButton(text="Информатика 💻", callback_data="subject_info")
    btn5 = InlineKeyboardButton(text="Физика⚡️", callback_data="subject_phys")
    btn6 = InlineKeyboardButton(text="Химия/Биология 🧪🧬", callback_data="subject_chem")

    rows = [
        [btn1, btn2],
        [btn3, btn4, btn5],
        [btn6]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "Привет! я тот самый бот который поможет тебе разобрать тему или срочно выполнить домашнее задание! для того что бы я лучше разбирался в задачах тебе необходимо выбрать предмет который мы с тобой разберём! выбери из списка: ",
        reply_markup=get_menu()
    )


@dp.callback_query(F.data.startswith("subject_"))
async def save_choice(callback: CallbackQuery):
    user_id = callback.from_user.id
    choice_code = callback.data.split("_")[1]

    subjects_map = {
        "math": "Математике",
        "rus": "Русскому и Литературе",
        "eng": "Английскому",
        "info": "Информатике",
        "phys": "Физике",
        "chem": "Химии"
    }

    selected_subject = subjects_map.get(choice_code, "Школьная программа")

    user_subjects[user_id] = selected_subject

    await callback.answer()
    await callback.message.edit_text(f"Отлично! Теперь я отвечу на любой вопрос по выбранной теме. \nЗадавай вопрос!")


@dp.message(F.text | F.photo)
async def chat_gemini(message: Message):
    user_id = message.from_user.id

    if user_id not in user_subjects:
        await message.answer("Сначала выбери предмет! Нажми /start")
        return

    current_subject = user_subjects[user_id]

    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    user_text = message.text or message.caption
    if not user_text:
        user_text = "Реши задачу, представленную на изображении, и подробно объясни решение."

    final_system_instruction = SYSTEM_PROMPT_TEMPLATE.format(subject_name=current_subject)
    full_request = f"{final_system_instruction}\n\nЗапрос ученика: {user_text}"

    contents_to_send = []

    text_part = types.Part.from_text(text=full_request)
    contents_to_send.append(text_part)

    if message.photo:
        try:
            photo_info = message.photo[-1]
            image_stream = BytesIO()
            await bot.download(photo_info, destination=image_stream)
            image_bytes = image_stream.getvalue()

            image_part = types.Part.from_bytes(
                data=image_bytes,
                mime_type="image/jpeg"
            )

            contents_to_send.append(image_part)

        except Exception as e:
            print(f"Ошибка: {e}")
            await message.answer("Не удалось загрузить изображение. Попробуй еще раз.")
            return

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents_to_send
        )

        if response.text:
            await message.answer(response.text)
        else:
            await message.answer("Прости, я задумался и ничего не ответил. Попробуй еще раз.")

    except Exception as e:
        print(f"Ошибка: {e}")
        await message.answer("Произошла ошибка! попробуйте ещё раз.")




async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен")