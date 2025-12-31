from telebot import TeleBot, types
import os
import query
from dotenv import load_dotenv
import flask
from flask import request
# ----------------- تنظیمات -----------------
ADMINS = ['1246405986']  # آیدی تلگرام ادمین
user_state = {}  # state کاربر
load_dotenv()
TOKEN = os.getenv("TOKEN")
bot = TeleBot (TOKEN ,threaded=False)

app = flask.Flask (__name__)

# ----------------- هندلر /start -----------------
@bot.message_handler(commands=['start'])
def start(m):
    user_id = str(m.from_user.id)
    username = m.from_user.username or "NoName"

    query.insert_user(user_id, username)


    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('نوبت‌های من', 'اخذ نوبت')
    if user_id in ADMINS:
        markup.row('اضافه کردن نوبت', 'پاک کردن همه نوبت‌ها')

    bot.send_message(
        m.chat.id,
        "🎉 به ربات آرایشگاه خوش آمدید!\nگزینه مناسب را انتخاب کنید:",
        reply_markup=markup
    )

# ----------------- اخذ نوبت -----------------
@bot.message_handler(func=lambda m: m.text == 'اخذ نوبت')
def take_slot(m):
    dates = query.show_slot_dates()

    if not dates:
        bot.send_message(m.chat.id, "❌ هنوز هیچ نوبتی اضافه نشده است.")
        return

    markup = types.InlineKeyboardMarkup()
    for d in dates:
        markup.add(types.InlineKeyboardButton(
            text=d, callback_data=f"date_{d}"
        ))

    bot.send_message(m.chat.id, "تاریخ مورد نظر را انتخاب کنید:", reply_markup=markup)

# ----------------- انتخاب تاریخ -----------------
@bot.callback_query_handler(func=lambda c: c.data.startswith("date_"))
def choose_date(c):
    user_id = str(c.from_user.id)
    date = c.data.split("_", 1)[1]
    user_state[user_id] = {"date": date}

    times = query.show_times_by_date(date)

    if not times:
        bot.send_message(c.message.chat.id, "❌ هنوز ساعتی برای این تاریخ اضافه نشده.")
        return

    markup = types.InlineKeyboardMarkup()
    for slot_id, t in times:
        markup.add(types.InlineKeyboardButton(
            text=t, callback_data=f"time_{slot_id}"
        ))

    bot.send_message(c.message.chat.id, "ساعت مورد نظر را انتخاب کنید:", reply_markup=markup)

# ----------------- انتخاب ساعت -----------------
@bot.callback_query_handler(func=lambda c: c.data.startswith("time_"))
def choose_time(c):
    user_id = str(c.from_user.id)
    slot_id = int(c.data.split("_", 1)[1])

    query.book_appointment(user_id, slot_id)


    bot.send_message(c.message.chat.id, "✅ نوبت شما با موفقیت ثبت شد!")
    user_state.pop(user_id, None)

# ----------------- نمایش نوبت‌ها -----------------
@bot.message_handler(func=lambda m: m.text == 'نوبت‌های من')
def my_appointments(m):
    user_id = str(m.from_user.id)
    if user_id in ADMINS:
        appointments = query.get_admin_appointments()
        if not appointments:
            bot.send_message(m.chat.id, "❌ هنوز هیچ نوبتی ثبت نشده است.")
            return
        text = "📋 همه نوبت‌های رزروی کاربران:\n\n"
        for date, time, username in appointments:
            text += f"📅 {date} ⏰ {time} — @{username}\n"
    else:
        appointments = query.get_user_appointments(user_id)
        if not appointments:
            bot.send_message(m.chat.id, "❌ شما هنوز هیچ نوبتی رزرو نکرده‌اید.")
            return
        text = "📋 نوبت‌های شما:\n\n"
        for date, time in appointments:
            text += f"📅 {date} ⏰ {time}\n"

    bot.send_message(m.chat.id, text)

# ----------------- اضافه کردن نوبت -----------------
@bot.message_handler(func=lambda m: m.text == 'اضافه کردن نوبت')
def add_slot(m):
    user_id = str(m.from_user.id)
    if user_id not in ADMINS:
        bot.send_message(m.chat.id, "❌ شما ادمین نیستید.")
        return

    user_state[user_id] = {"step": "add_date", "dates": [], "slots": []}
    bot.send_message(m.chat.id, "تاریخ جدید را وارد کنید (YYYY-MM-DD). برای پایان 'done' را بزنید:")

# ----------------- پاک کردن همه نوبت‌ها -----------------
@bot.message_handler(func=lambda m: m.text == 'پاک کردن همه نوبت‌ها')
def clear_slots(m):
    user_id = str(m.from_user.id)
    if user_id not in ADMINS:
        bot.send_message(m.chat.id, "❌ شما ادمین نیستید.")
        return

    query.delete_all_slots()
    bot.send_message(m.chat.id, "✅ تمام نوبت‌ها و رزروها پاک شدند!")

# ----------------- هندلر Admin Input -----------------
@bot.message_handler(func=lambda m: str(m.from_user.id) in user_state)
def admin_input(m):
    user_id = str(m.from_user.id)
    state = user_state[user_id]

    step = state.get("step")

    if step == "add_date":
        text = m.text.strip()
        if text.lower() == "done":
            if not state["dates"]:
                bot.send_message(m.chat.id, "❌ حداقل یک تاریخ وارد کنید.")
                return
            state["date_index"] = 0
            state["step"] = "add_times"
            bot.send_message(m.chat.id, f"⏰ زمان‌ها را برای تاریخ {state['dates'][0]} با کاما جدا وارد کنید (مثال: 10:00,11:00):")
        else:
            state["dates"].append(text)
            bot.send_message(m.chat.id, "تاریخ ثبت شد. تاریخ بعدی را وارد کنید یا 'done' بزنید.")

    elif step == "add_times":
        times = [t.strip() for t in m.text.split(",") if t.strip()]
        date = state["dates"][state["date_index"]]
        query.insert_slots(date, times)


        state["date_index"] += 1
        if state["date_index"] < len(state["dates"]):
            next_date = state["dates"][state["date_index"]]
            bot.send_message(m.chat.id, f"⏰ زمان‌ها را برای تاریخ {next_date} وارد کنید (مثال: 10:00,11:00):")
        else:
            bot.send_message(m.chat.id, f"✅ همه تاریخ‌ها و ساعت‌ها با موفقیت اضافه شدند.")
            user_state.pop(user_id)

# ----------------- دیباگ -----------------
@bot.message_handler(func=lambda m: True)
def debug_all(m):
    print("MESSAGE RECEIVED:", m.text)

# ----------------- اجرا -----------------
    
    
    
    
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    raw = request.get_data().decode("utf-8")
    print(f"📦 Raw update: {raw}")  # Log the full payload
    update = types.Update.de_json(raw)
    print(f"✅ Parsed update: {update}")  # Log the parsed object
    bot.process_new_updates([update])
    return "OK", 200


@app.route("/")
def index():
    return "Bot is running!", 200


