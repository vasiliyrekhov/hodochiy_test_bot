import asyncio
import os
import threading
from flask import Flask
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# --- ТОКЕН ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("Переменная TELEGRAM_TOKEN не установлена!")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ===== Хранилище результатов пользователя =====
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
            "a": "Ищу хитрый обходной путь или пытаюсь договориться.",
            "b": "Впадаю в уныние, но продолжаю идти вперёд из принципа.",
            "c": "Злюсь и пытаюсь сломать преграду силой или магией.",
            "d": "Ухожу в себя, делаю вид, что проблемы нет."
        },
        "scores": {"a": "A", "b": "B", "c": "C", "d": "D"}
    },
    "q2": {
        "text": "2️⃣ Как бы ты описал свою внешность или стиль?",
        "options": {
            "a": "Сдержанно, но с изюминкой (много карманов или необычный аксессуар).",
            "b": "Скромно, практично, стараюсь быть незаметным.",
            "c": "Ярко, вызывающе, люблю производить впечатление.",
            "d": "Немного неопрятно или старомодно, мне всё равно на моду."
        },
        "scores": {"a": "A", "b": "B", "c": "C", "d": "D"}
    },
    "q3": {
        "text": "3️⃣ Что для тебя важнее всего в отношениях?",
        "options": {
            "a": "Взаимная выгода и интересный диалог.",
            "b": "Чувство безопасности и покой рядом с человеком.",
            "c": "Страсть, динамика и чтобы меня не боялись.",
            "d": "Безусловное принятие и забота (даже если я ворчу)."
        },
        "scores": {"a": "A", "b": "B", "c": "C", "d": "D"}
    },
    "q4": {
        "text": "4️⃣ Твой любимый способ провести выходной?",
        "options": {
            "a": "Устроить генеральную уборку или перестановку.",
            "b": "Уйти в лес, к воде или просто долго гулять в одиночестве.",
            "c": "Пойти в шумное место, развлекаться или устроить праздник.",
            "d": "Лежать с книгой/сериалом, никуда не выходя, и вкусно поесть."
        },
        "scores": {"a": "A", "b": "B", "c": "C", "d": "D"}
    },
    "q5": {
        "text": "5️⃣ Как ты реагируешь на чужую грубость или вторжение в личное пространство?",
        "options": {
            "a": "Отвечаю вежливо, но с холодной иронией, ставлю на место словами.",
            "b": "Терпеливо сношу, но внутри сильно переживаю.",
            "c": "Взрываюсь и отвечаю той же монетой (или проклинаю).",
            "d": "Игнорирую, ухожу в себя или перевожу в шутку."
        },
        "scores": {"a": "A", "b": "B", "c": "C", "d": "D"}
    },
    "q6": {
        "text": "6️⃣ Выбери блюдо, которое тебе нравится больше всего:",
        "options": {
            "a": "Что-то острое, пряное, с необычными ингредиентами.",
            "b": "Простая, но сытная домашняя еда (каша, суп, хлеб с маслом).",
            "c": "Мясо на костре или что-то эффектное, большое.",
            "d": "Сладости (пирожные, мармелад, шоколад)."
        },
        "scores": {"a": "A", "b": "B", "c": "C", "d": "D"}
    },
    "q7": {
        "text": "7️⃣ Какая суперсила тебе была бы полезнее?",
        "options": {
            "a": "Убеждение и дар красноречия.",
            "b": "Исцеление и способность вселять спокойствие.",
            "c": "Огненная магия или невероятная физическая сила.",
            "d": "Невидимость или способность замедлять время."
        },
        "scores": {"a": "A", "b": "B", "c": "C", "d": "D"}
    },
    "q8": {
        "text": "8️⃣ Ты попал в новый незнакомый мир. Твои первые действия:",
        "options": {
            "a": "Начну изучать местные законы и искать выгоду.",
            "b": "Присмотрюсь к местным, найду того, кому можно доверять.",
            "c": "Пойду напролом, чтобы меня сразу заметили и боялись.",
            "d": "Найду тихое место, чтобы выдохнуть и всё обдумать."
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

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    user_scores[message.from_user.id] = []
    await message.answer(
        "🧙‍♂️ *Добро пожаловать в тест «Какой ты персонаж из Ходячего замка?»*\n\n"
        "Ответь на 8 вопросов, и я скажу, кто ты — Хаул, Софи, Ведьма Пустоши или Муха.\n\n"
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
        character = "🐕 **Муха (собака-компаньон)**\n\nТы ценишь уют, тишину и простые радости. Ты наблюдателен, верен и не лезешь в драму, если она не касается тебя напрямую. Ты — «душа дома», тот, кто создаёт атмосферу покоя и всегда готов обнять (или вздремнуть)."
    
    stats = f"📊 *Твой профиль:* A={count_A}, B={count_B}, C={count_C}, D={count_D}"
    await message.answer(
        f"✨ *Ты — {character}*\n\n{stats}",
        parse_mode="Markdown"
    )
    await state.clear()

@dp.message()
async def unknown(message: types.Message):
    await message.answer("🧙‍♂️ Нажми /start, чтобы пройти тест!")

# ===== Flask для Render =====
app = Flask(__name__)

@app.route('/')
def home():
    return "Бот работает!"

@app.route('/health')
def health():
    return "OK", 200

async def run_bot():
    print("Бот запущен!")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

def start_bot():
    asyncio.run(run_bot())

if __name__ == "__main__":
    bot_thread = threading.Thread(target=start_bot)
    bot_thread.start()
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)