import telebot
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
import json

TOKEN = "7807718978:AAEE4pDJSrnDHHDh8uW4mPoumCaMwBoYq_s"
bot = telebot.TeleBot(TOKEN)

ITEMS_PER_PAGE = 5

# === БАЗА ДАННЫХ ===

def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# === АВТО-РЕГИСТРАЦИЯ ===

def ensure_user(uid):
    users = load_json("users.json")
    if uid not in users:
        users[uid] = {
            "email": "",
            "password": "",
            "subscriptions": [],
            "notify_days_before": 2
        }
        save_json(users, "users.json")

# === ГЛАВНОЕ МЕНЮ ===

def main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📋 Список олимпиад", "📌 Мои подписки")
    kb.row("🔔 Подписаться", "⚙️ Настройки")
    kb.row("❓ Помощь")
    return kb

@bot.message_handler(commands=["start"])
def start(m):
    uid = str(m.chat.id)
    ensure_user(uid)
    bot.send_message(m.chat.id, "Добро пожаловать!", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "❓ Помощь")
def help_cmd(m):
    bot.send_message(m.chat.id,
        "Доступные действия:\n"
        "📋 Список олимпиад — просмотр\n"
        "🔔 Подписаться — выбрать из списка\n"
        "📌 Мои подписки — список и отписка\n"
        "⚙️ Настройки — напоминание"
    )

# === СПИСОК ОЛИМПИАД ПО СТРАНИЦАМ ===

def get_olympiad_page(page, action="none"):
    olympiads = load_json("olympiads.json")
    total = len(olympiads)
    start = page * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    page_data = olympiads[start:end]

    text = f"📋 Олимпиады (стр. {page+1}):\n\n"
    kb = InlineKeyboardMarkup()

    for o in page_data:
        dt = datetime.fromisoformat(o["datetime"]).strftime("%d.%m.%Y %H:%M")
        text += f"{o['id']}. {o['title']} — {dt}\n"
        if action == "subscribe":
            kb.add(InlineKeyboardButton(f"✅ Подписаться на {o['id']}", callback_data=f"sub:{o['id']}"))
        elif action == "unsubscribe":
            kb.add(InlineKeyboardButton(f"❌ Отписаться от {o['id']}", callback_data=f"unsub:{o['id']}"))

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"page:{action}:{page-1}"))
    if end < total:
        nav.append(InlineKeyboardButton("➡️ Далее", callback_data=f"page:{action}:{page+1}"))
    if nav:
        kb.row(*nav)

    return text, kb

@bot.message_handler(func=lambda m: m.text == "📋 Список олимпиад")
def show_list(m):
    text, kb = get_olympiad_page(0, action="none")
    bot.send_message(m.chat.id, text, reply_markup=kb)

# === ПОДПИСКА ===

@bot.message_handler(func=lambda m: m.text == "🔔 Подписаться")
def show_subscribe_menu(m):
    ensure_user(str(m.chat.id))
    text, kb = get_olympiad_page(0, action="subscribe")
    bot.send_message(m.chat.id, "Выберите олимпиаду для подписки:", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("sub:"))
def handle_subscribe(call):
    uid = str(call.from_user.id)
    oid = int(call.data.split(":")[1])
    users = load_json("users.json")
    ensure_user(uid)

    if oid not in users[uid]["subscriptions"]:
        users[uid]["subscriptions"].append(oid)
        save_json(users, "users.json")
        bot.answer_callback_query(call.id, f"✅ Подписка на {oid} оформлена!")
    else:
        bot.answer_callback_query(call.id, "Вы уже подписаны.")

# === МОИ ПОДПИСКИ + ОТПИСКА ===

@bot.message_handler(func=lambda m: m.text == "📌 Мои подписки")
def show_my_subs(m):
    uid = str(m.chat.id)
    ensure_user(uid)
    users = load_json("users.json")
    olympiads = load_json("olympiads.json")

    subs = users[uid]["subscriptions"]
    if not subs:
        bot.send_message(m.chat.id, "У вас нет подписок.")
        return

    text = "📌 Ваши подписки:\n\n"
    kb = InlineKeyboardMarkup()
    for o in olympiads:
        if o["id"] in subs:
            dt = datetime.fromisoformat(o["datetime"]).strftime("%d.%m.%Y %H:%M")
            text += f"{o['id']}. {o['title']} — {dt}\n"
            kb.add(InlineKeyboardButton(f"❌ Отписаться от {o['id']}", callback_data=f"unsub:{o['id']}"))
    bot.send_message(m.chat.id, text, reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("unsub:"))
def handle_unsubscribe(call):
    uid = str(call.from_user.id)
    oid = int(call.data.split(":")[1])
    users = load_json("users.json")
    ensure_user(uid)

    if oid in users[uid]["subscriptions"]:
        users[uid]["subscriptions"].remove(oid)
        save_json(users, "users.json")
        bot.answer_callback_query(call.id, f"❌ Подписка на {oid} удалена.")
    else:
        bot.answer_callback_query(call.id, "Вы не были подписаны.")

# === НАВИГАЦИЯ ПАГИНАЦИИ ===

@bot.callback_query_handler(func=lambda call: call.data.startswith("page:"))
def handle_page_nav(call):
    _, action, page = call.data.split(":")
    page = int(page)
    text, kb = get_olympiad_page(page, action=action)
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=text,
        reply_markup=kb
    )

# === НАСТРОЙКИ УВЕДОМЛЕНИЙ ===

@bot.message_handler(func=lambda m: m.text == "⚙️ Настройки")
def show_settings_hint(m):
    bot.send_message(m.chat.id, "Введите команду: /settings <дней>\nНапример: /settings 2")

@bot.message_handler(commands=["settings"])
def handle_settings(m):
    uid = str(m.chat.id)
    ensure_user(uid)
    users = load_json("users.json")
    args = m.text.split()

    if len(args) != 2 or not args[1].isdigit():
        bot.send_message(m.chat.id, "Пример: /settings 2")
        return

    days = int(args[1])
    users[uid]["notify_days_before"] = days
    save_json(users, "users.json")
    bot.send_message(m.chat.id, f"🔔 Уведомления за {days} дней сохранены.")

print("✅ Бот запущен с интерактивной подпиской и регистрацией")
bot.polling()
