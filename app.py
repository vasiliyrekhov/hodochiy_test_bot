import asyncio
import os
import threading
from flask import Flask
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# --- ТОКЕН ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("Переменная TELEGRAM_TOKEN не установлена!")

bot = Bot(token=TOKEN)
dp = Dispatcher()
user_scores = {}

# ===== Состояния для FSM =====
class TestState(StatesGroup):
    q1 = State()
    q2 = State()
    q3 = State()
    q4 = State()
    q5 = State()
    q6 = State()
    q7 = State()
    q8 = State()

# ===== Вопросы =====
questions = {
    "q1": {
        "text": "1️⃣ Что ты делаешь, когда сталкиваешься с неразрешимой проблемой?",
        "options": {
            "a": "Ищу хитрый обходной путь",
            "b": "Впадаю в уныние, но иду вперёд",
            "c": "Злюсь и ломаю преграду",
            "d": "Ухожу в себя и жду"
        },
        "scores": {"a": "A", "b": "B", "c": "C", "d": "D"}
    },
    "q2": {
        "text": "2️⃣ Как бы ты описал свою внешность или стиль?",
        "options": {
            "a": "Сдержанно, но с изюминкой",
            "b": "Скромно и практично",
            "c": "Ярко и вызывающе",
            "d": "Мне всё равно на моду"
        },
        "scores": {"a": "A", "b": "B", "c": "C", "d": "D"}
    },
    "q3": {
        "text": "3️⃣ Что для тебя важнее всего в отношениях?",
        "options": {
            "a": "Взаимная выгода и диалог",
            "b": "Безопасность и покой",
            "c": "Страсть и динамика",
            "d": "Безусловная забота"
        },
        "scores": {"a": "A", "b": "B", "c": "C", "d": "D"}
    },
    "q4": {
        "text": "4️⃣ Твой любимый способ провести выходной?",
        "options": {
            "a": "Устроить перестановку",
            "b": "Уйти в лес или гулять",
            "c": "Пойти в шумное место",
            "d": "Лежать и вкусно есть"
        },
        "scores": {"a": "A", "b": "B", "c": "C", "d": "D"}
    },
    "q5": {
        "text": "5️⃣ Как ты реагируешь на чужую грубость?",
        "options": {
            "a": "Отвечаю с холодной иронией",
            "b": "Терпеливо сношу",
            "c": "Взрываюсь и отвечаю",
            "d": "Игнорирую или шучу"
        },
        "scores": {"a": "A", "b": "B", "c": "C", "d": "D"}
    },
    "q6": {
        "text": "6️⃣ Выбери блюдо, которое тебе нравится больше всего:",
        "options": {
            "a": "Острое и пряное",
            "b": "Простая домашняя еда",
            "c": "Мясо на костре",
            "d": "Сладости (пирожные)"
        },
        "scores": {"a": "A", "b": "B", "c": "C", "d": "D"}
    },
    "q7": {
        "text": "7️⃣ Какая суперсила тебе была бы полезнее?",
        "options": {
            "a": "Дар убеждения",
            "b": "Исцеление и покой",
            "c": "Огненная магия",
            "d": "Невидимость"
        },
        "scores": {"a": "A", "b": "B", "c": "C", "d": "D"}
    },
    "q8": {
        "text": "8️⃣ Ты попал в новый незнакомый мир. Твои первые действия:",
        "options": {
            "a": "Изучу местные законы",
            "b": "Найду, кому доверять",
            "c": "Пойду напролом",
            "d": "Найду тихое место"
        },
        "scores": {"a": "A", "b": "B", "c": "C", "d": "D"}
    }
}

question_order = ["q1", "q2", "q3", "q4", "q5", "q6", "q7", "q8"]

def get_keyboard(question_key):
    q = questions[question_key]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🇦 {q['options']['a']}", callback_data="a")],
        [InlineKeyboardButton(text=f"🇧 {q['options']['b']}", callback_data="b")],
        [InlineKeyboardButton(text=f"🇨 {q['options']['c']}", callback_data="c")],
        [InlineKeyboardButton(text=f"🇩 {q['options']['d']}", callback_data="d")]
    ])
    return kb

# ===== ОБРАБОТЧИК КОМАНДЫ /start =====
@dp.message(CommandStart())
async def cmd_start(message: types.Message, command: CommandObject, state: FSMContext):
    await state.clear()
    user_scores[message.from_user.id] = []
    
    if command.args:
        await message.answer(
            "🧙‍♂️ *Привет! Ты перешёл по ссылке из канала.*\n\n"
            "Давай сразу пройдём тест «Какой ты персонаж из Ходячего замка»?\n\n"
            "Готов? Поехали! 🚀",
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            "🧙‍♂️ *Добро пожаловать в тест «Какой ты персонаж из Ходячего замка»?*\n\n"
            "Ответь на 8 вопросов, и я скажу, кто ты — Хаул, Софи, Ведьма Пустоши или пёс Хин.\n\n"
            "Готов? Поехали! 🚀",
            parse_mode="Markdown"
        )
    
    await ask_question(message, state, 0)

async def ask_question(message: types.Message, state: FSMContext, index: int):
    if index >= len(question_order):
        await show_result(message, state)
        return
    q_key = question_order[index]
    q = questions[q_key]
    await state.update_data(current_index=index)
    await message.answer(
        q["text"],
        reply_markup=get_keyboard(q_key)
    )

@dp.callback_query()
async def handle_answer(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    answer = callback.data
    data = await state.get_data()
    index = data.get("current_index", 0)
    if index >= len(question_order):
        await callback.answer("Тест уже завершён!")
        return
    q_key = question_order[index]
    scores_map = questions[q_key]["scores"]
    user_scores[user_id].append(scores_map[answer])
    next_index = index + 1
    if next_index >= len(question_order):
        await callback.message.delete()
        await show_result(callback.message, state, user_id)
        await callback.answer()
    else:
        await callback.message.delete()
        await state.update_data(current_index=next_index)
        await ask_question(callback.message, state, next_index)
        await callback.answer()

async def show_result(message: types.Message, state: FSMContext, user_id=None):
    if user_id is None:
        user_id = message.from_user.id
    scores = user_scores.get(user_id, [])
    if len(scores) < 8:
        await message.answer("❌ Что-то пошло не так. Начни тест заново командой /start")
        return
    count_A = scores.count("A")
    count_B = scores.count("B")
    count_C = scores.count("C")
    count_D = scores.count("D")
    
    if count_A >= count_B and count_A >= count_C and count_A >= count_D:
        character = "🔥 **Хаул**\n\nТы хитёр, обаятелен, любишь эффектные решения и немного кокетлив. Ты умеешь менять правила игры и не терпишь скуки. Как и Хаул, ты можешь быть эгоистичным, но в критический момент проявишь чудеса храбрости ради близких."
    elif count_B >= count_A and count_B >= count_C and count_B >= count_D:
        character = "👒 **Софи**\n\nТы терпелива, упряма и добра до глубины души. Ты не считаешь себя особенной, но именно ты способна удержать всё на себе и разбить проклятия просто силой своей любви и заботы. Твоя главная магия — в принятии других такими, какие они есть."
    elif count_C >= count_A and count_C >= count_B and count_C >= count_D:
        character = "🧹 **Ведьма Пустоши**\n\nОго! Ты импульсивна, страстна и живёшь эмоциями. Ты не боишься быть сильной и требовать своё. Но, как и Ведьма, ты часто скрываешь за гневом огромную боль и одиночество. Тебе не хватает кого-то, кто полюбит тебя просто так."
    else:
        character = "🐕 **Пёс Хин**\n\nТы ценишь уют, тишину и простые радости. Ты наблюдателен, верен и не лезешь в драму, если она не касается тебя напрямую. Ты — «душа дома», тот, кто создаёт атмосферу покоя и всегда готов обнять (или вздремнуть)."

    # Отправляем результат БЕЗ строчки со статистикой
    await message.answer(
        f"✨ *Ты — {character}*",
        parse_mode="Markdown"
    )
    await state.clear()

@dp.message()
async def unknown(message: types.Message):
    await message.answer("🧙‍♂️ Нажми /start, чтобы пройти тест!")

# ===== Функция запуска бота =====
async def run_bot():
    print("Бот запущен!")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

# ===== Flask для Render =====
app = Flask(__name__)

@app.route('/')
def home():
    return "Бот работает!"

@app.route('/health')
def health():
    return "OK", 200

# ===== ГЛАВНЫЙ ЗАПУСК =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    
    def run_flask():
        app.run(host='0.0.0.0', port=port)
    
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    
    asyncio.run(run_bot())
