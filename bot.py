
import os
import logging
from pathlib import Path
from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ============ КОНФИГ ============
BOT_TOKEN = os.environ["BOT_TOKEN"]
OWNER_CHAT_ID = int(os.environ.get("OWNER_CHAT_ID", "1194243262"))
ADMIN_CHAT_ID = int(os.environ.get("ADMIN_CHAT_ID", "358325979"))
ADMIN_TOPIC_ID = int(os.environ.get("ADMIN_TOPIC_ID", "225548"))

logging.basicConfig(level=logging.INFO)
bot = TeleBot(BOT_TOKEN)

# ============ ПОИСК ФОТО С FALLBACK ============
def find_photo(*names):
    for n in names:
        if Path(n).exists():
            return n
    return None

PHOTOS = {
    "razbor": find_photo("photo-razbor.jpg", "razbor.jpg"),
    "manikur": find_photo("photo-manikur.jpg", "manikur.jpg"),
    "pedikur": find_photo("photo-pedikur.jpg", "pedikur.jpg"),
    "makeup": find_photo("photo-makeup.jpg", "foto-makiyazh.jpg", "photo-макияж.jpg", "makeup.jpg"),
}

# ============ КАТАЛОГ УСЛУГ ============
SERVICES = {
    "razbor": {
        "name": "Разбор косметички",
        "price": "1 500₽",
        "dur": "60 мин",
        "motiv": "✨ Твой идеальный набор собирается за один визит. Не пора ли?",
        "variants": [],
        "extra": "",
    },
    "manikur": {
        "name": "Маникюр",
        "price": "от 700₽",
        "dur": "60 мин",
        "motiv": "💅 Не затягивай до последнего — бронируй дату заранее. Ведь красивый маникюр вырабатывает гармон счастья.",
        "variants": [
            ("Маникюр", "700₽", "60 мин"),
            ("Маникюр с покрытием", "от 1 450₽", "75 мин"),
            ("Наращивание", "от 1 800₽", "90 мин"),
        ],
        "extra": "Дополнительно:\n+ Френч — 200₽\n+ Дизайн — 200₽\n+ Фигурки — 200₽",
    },
    "pedikur": {
        "name": "Педикюр",
        "price": "от 1 500₽",
        "dur": "75 мин",
        "motiv": "🦶 Ножки тоже заслуживают заботы.",
        "variants": [
            ("Педикюр с покрытием, обработка пальчиков", "1 500₽", "75 мин"),
            ("Педикюр с полной обработкой стоп", "1 700₽", "90 мин"),
        ],
        "extra": "",
    },
    "makeup": {
        "name": "Сопровождение макияжа",
        "price": "1 500₽",
        "dur": "до 60 мин видеозвонка",
        "motiv": "💋 Сегодня — тот самый день, когда ты можешь это сделать под моей бережной опекой.",
        "variants": [],
        "extra": "",
    },
}

# ============ FSM ============
state = {}

def reset_state(chat_id):
    state[chat_id] = {"step": "menu"}

def get_state(chat_id):
    return state.setdefault(chat_id, {"step": "menu"})

# ============ КНОПКИ ============
def main_menu_kb():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("💄 Разбор косметички", callback_data="svc:razbor"))
    kb.add(InlineKeyboardButton("💅 Маникюр", callback_data="svc:manikur"))
    kb.add(InlineKeyboardButton("🦶 Педикюр", callback_data="svc:pedikur"))
    kb.add(InlineKeyboardButton("💋 Сопровождение макияжа", callback_data="svc:makeup"))
    kb.add(InlineKeyboardButton("ℹ️ Обо мне", callback_data="about"))
    kb.add(InlineKeyboardButton("📞 Связаться напрямую", callback_data="contact"))
    kb.add(InlineKeyboardButton("🌐 Сайт Валерии Михайловой", url="https://mikhaylovabeauty.p.spru.io/"))
    return kb

def variants_kb(svc_key):
    kb = InlineKeyboardMarkup(row_width=1)
    svc = SERVICES[svc_key]
    if svc["variants"]:
        for i, (name, price, dur) in enumerate(svc["variants"]):
            label = f"{name} — {price} ({dur})"
            kb.add(InlineKeyboardButton(label, callback_data=f"var:{svc_key}:{i}"))
    else:
        kb.add(InlineKeyboardButton("✅ Записаться", callback_data=f"var:{svc_key}:0"))
    kb.add(InlineKeyboardButton("← Назад", callback_data="back:menu"))
    return kb

def date_kb():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("📅 Сегодня", callback_data="date:today"))
    kb.add(InlineKeyboardButton("📅 Завтра", callback_data="date:tomorrow"))
    kb.add(InlineKeyboardButton("📅 Выходные", callback_data="date:weekend"))
    kb.add(InlineKeyboardButton("📝 Свой вариант", callback_data="date:custom"))
    kb.add(InlineKeyboardButton("← Назад", callback_data="back:menu"))
    return kb

def confirm_kb():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("✅ Отправить", callback_data="send:ok"))
    kb.add(InlineKeyboardButton("✏️ Изменить", callback_data="back:name"))
    return kb

def after_kb():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("🏠 В начало", callback_data="back:menu"))
    kb.add(InlineKeyboardButton("📤 Поделиться ботом", callback_data="share"))
    return kb

# ============ СТАРТ ============
@bot.message_handler(commands=["start", "help"])
def cmd_start(message):
    reset_state(message.chat.id)
    bot.send_message(
        message.chat.id,
        "Привет! 🌷\nЯ бот Валерии Михайловой.\nПомогу записаться на услугу или расскажу подробнее.",
    )
    bot.send_message(message.chat.id, "Что вас интересует?", reply_markup=main_menu_kb())

# ============ CALLBACK ============
@bot.callback_query_handler(func=lambda c: True)
def on_callback(call):
    chat_id = call.message.chat.id
    s = get_state(chat_id)
    data = call.data
    bot.answer_callback_query(call.id)

    if data.startswith("svc:"):
        s["service"] = data.split(":", 1)[1]
        s["step"] = "variants"
        svc = SERVICES[s["service"]]
        try:
            bot.delete_message(chat_id, call.message.message_id)
        except Exception:
            pass
        photo_path = PHOTOS.get(s["service"])
        if photo_path:
            try:
                with open(photo_path, "rb") as ph:
                    bot.send_photo(chat_id, ph)
            except Exception as e:
                logging.warning("photo send failed: %s", e)
        text = svc["motiv"]
        if svc.get("extra"):
            text += "\n\n" + svc["extra"]
        bot.send_message(chat_id, text, reply_markup=variants_kb(s["service"]))

    elif data.startswith("var:"):
        _, svc_key, idx = data.split(":")
        svc = SERVICES[svc_key]
        if svc["variants"]:
            v = svc["variants"][int(idx)]
            s["variant"] = f"{v[0]} — {v[1]} ({v[2]})"
        else:
            s["variant"] = f"{svc['name']} — {svc['price']} ({svc['dur']})"
        s["step"] = "name"
        bot.edit_message_text("Как вас зовут?", chat_id, call.message.message_id, reply_markup=None)

    elif data.startswith("date:"):
        v = data.split(":", 1)[1]
        s["date"] = {"today": "Сегодня", "tomorrow": "Завтра", "weekend": "Выходные"}.get(v, "")
        if v == "custom":
            s["step"] = "date_custom"
            bot.edit_message_text(
                "Напишите удобную дату (например: 25 сентября, воскресенье)",
                chat_id, call.message.message_id, reply_markup=None,
            )
            return
        s["step"] = "confirm"
        bot.edit_message_text(render_summary(s), chat_id, call.message.message_id, reply_markup=confirm_kb())

    elif data == "send:ok":
        send_lead(s)
        s["step"] = "after"
        bot.edit_message_text(
            "✅ Заявка отправлена!\n\nВалерия свяжется с вами в течение часа в рабочее время (пн–сб, 10:00–20:00).",
            chat_id, call.message.message_id, reply_markup=after_kb(),
        )

    elif data.startswith("back:"):
        target = data.split(":", 1)[1]
        if target == "menu":
            reset_state(chat_id)
            bot.edit_message_text("Что вас интересует?", chat_id, call.message.message_id, reply_markup=main_menu_kb())
        elif target == "name":
            s["step"] = "name"
            bot.edit_message_text("Как вас зовут?", chat_id, call.message.message_id, reply_markup=None)

    elif data == "about":
        kb = InlineKeyboardMarkup(row_width=1)
        kb.add(InlineKeyboardButton("Записаться", callback_data="svc:razbor"))
        kb.add(InlineKeyboardButton("← Назад", callback_data="back:menu"))
        bot.edit_message_text(
            "Валерия — бьюти-мастер с 8-летним опытом.\n\n"
            "💄 Разбор косметички — помогу собрать идеальный набор под ваш тип кожи.\n"
            "💅 Маникюр и педикюр — от 700₽, с покрытием, дизайн, наращивание.\n"
            "🦶 Педикюр — от 1 500₽ с покрытием.\n"
            "💋 Сопровождение макияжа — консультация в реальном времени.\n\n"
            "Хотите записаться?",
            chat_id, call.message.message_id, reply_markup=kb,
        )

    elif data == "contact":
        kb = InlineKeyboardMarkup(row_width=1)
        kb.add(InlineKeyboardButton("🏠 В начало", callback_data="back:menu"))
        bot.edit_message_text(
            "Связаться с Валерией:\n\n"
            "✈️ Telegram: @mikhaylova_pilit\n"
            "📱 Тел.: +7 (999) 123-45-67\n\n"
            "Или вернуться в меню:",
            chat_id, call.message.message_id, reply_markup=kb,
        )

    elif data == "share":
        bot.edit_message_text(
            "Вот ссылка:\nhttps://t.me/mikhaylovabeauty_bot\n\n"
            "Поделитесь с подругами 🌷",
            chat_id, call.message.message_id, reply_markup=after_kb(),
        )

# ============ ТЕКСТ (FSM) ============
@bot.message_handler(func=lambda m: True)
def on_text(message):
    if message.text and message.text.startswith("/"):
        return
    chat_id = message.chat.id
    s = get_state(chat_id)
    step = s.get("step")

    if step == "name":
        s["name"] = message.text.strip()
        s["step"] = "phone"
        bot.send_message(chat_id, f"Приятно познакомиться, {s['name']}! 🤍\nОтправьте номер телефона для связи:")
    elif step == "phone":
        s["phone"] = message.text.strip()
        s["step"] = "date"
        bot.send_message(chat_id, "Когда удобно?", reply_markup=date_kb())
    elif step == "date_custom":
        s["date"] = message.text.strip()
        s["step"] = "confirm"
        bot.send_message(chat_id, render_summary(s), reply_markup=confirm_kb())
    else:
        kb = InlineKeyboardMarkup(row_width=1)
        kb.add(InlineKeyboardButton("Открыть меню", callback_data="back:menu"))
        bot.send_message(chat_id, "Нажмите /start, чтобы открыть меню 🌷", reply_markup=kb)

# ============ HELPERS ============
def render_summary(s):
    return (
        "Проверьте заявку:\n\n"
        f"👤 Имя: {s.get('name','')}\n"
        f"📞 Телефон: {s.get('phone','')}\n"
        f"💄 Услуга: {s.get('variant','')}\n"
        f"📅 Когда: {s.get('date','')}\n\n"
        "Всё верно?"
    )

def send_lead(s):
    text = (
        "📥 Новая заявка из бота @mikhaylovabeauty_bot\n\n"
        f"👤 Имя: {s.get('name','')}\n"
        f"📞 Телефон: {s.get('phone','')}\n"
        f"💄 Услуга: {s.get('variant','')}\n"
        f"📅 Когда: {s.get('date','')}"
    )
    try:
        bot.send_message(OWNER_CHAT_ID, text)
    except Exception as e:
        logging.exception("owner notify failed: %s", e)
    try:
        bot.send_message(ADMIN_CHAT_ID, text, message_thread_id=ADMIN_TOPIC_ID)
    except Exception:
        pass

# ============ RUN ============
if __name__ == "__main__":
    print("Bot is starting…")
    bot.infinity_polling(skip_pending=True)

