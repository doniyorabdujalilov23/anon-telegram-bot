from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import sqlite3
import time
import os
from threading import Thread
from flask import Flask

# ==================== RENDER/REPLIT UCHUN SERVER ====================
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot a'lo darajada ishlamoqda!"

def run_server():
    # Render o'zi beradigan portni olamiz
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
# =============================================================

# DİQQAT: @BotFather dan yangi token oling va bu yerga yozing!
TOKEN = "8717578342:AAHfOuaZFiNwsCmyGezQLPqnvKvLMvHPojE"
ADMIN_ID = 5578534822

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# ==================== BAZA BILAN ISHLASH ====================
conn = sqlite3.connect("anon.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS messages(msg_id INTEGER, sender INTEGER, receiver INTEGER)")
cursor.execute("CREATE TABLE IF NOT EXISTS stats(user INTEGER, username TEXT, count INTEGER)")

try:
    cursor.execute("ALTER TABLE users ADD COLUMN username TEXT")
    cursor.execute("ALTER TABLE stats ADD COLUMN username TEXT")
except sqlite3.OperationalError:
    pass

conn.commit()

links = {}
last_message = {}
broadcast_mode = False

# ==================== MENU TUZILISHI ====================
menu = ReplyKeyboardMarkup(resize_keyboard=True)
menu.add(KeyboardButton("💌 Savol yuborish"), KeyboardButton("🔗 Mening anonim linkim"))
menu.add(KeyboardButton("👤 Profilim"), KeyboardButton("ℹ️ Bot haqida"))

admin_menu = ReplyKeyboardMarkup(resize_keyboard=True)
admin_menu.add(KeyboardButton("👥 Userlar"), KeyboardButton("📢 Broadcast"))
admin_menu.add(KeyboardButton("📊 Statistika"), KeyboardButton("📈 Top anonimlar"))


def get_user_name(user: types.User):
    if user.username:
        return f"@{user.username}"
    return user.first_name

# ==================== BUYRUQLAR ====================
@dp.message_handler(commands=['admin'])
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("👨💻 Admin panel", reply_markup=admin_menu)


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    uname = get_user_name(message.from_user)
    cursor.execute("INSERT OR REPLACE INTO users (id, username) VALUES (?, ?)", (message.from_user.id, uname))
    conn.commit()

    args = message.get_args()
    if args:
        links[message.from_user.id] = int(args)
        await message.answer(
            "💌 Anonim xabar yozing\n\nMatn, rasm, video, GIF, stiker yoki ovozli xabar yuborishingiz mumkin.",
            reply_markup=menu)
    else:
        me = await bot.get_me()
        link = f"https://t.me/{me.username}?start={message.from_user.id}"
        await message.answer(f"💌 Quyidagi havolangiz orqali anonim xabarlar qabul qiling:\n\n{link}", reply_markup=menu)

# ==================== TUGMALAR VA ADMIN PANEL ====================
@dp.message_handler(lambda m: m.text == "💌 Savol yuborish")
async def send_q_btn(message: types.Message):
    await message.answer("Savol yuborish uchun avval do'stingizning maxsus anonim linki orqali botga kirishingiz kerak.\n\nO'z linkingizni olish uchun «🔗 Mening anonim linkim» tugmasini bosing.")

@dp.message_handler(lambda m: m.text == "🔗 Mening anonim linkim")
async def link(message: types.Message):
    me = await bot.get_me()
    link = f"https://t.me/{me.username}?start={message.from_user.id}"
    await message.answer(f"💌 Sizga anonim savol yuborish linki:\n\n{link}")

@dp.message_handler(lambda m: m.text == "👤 Profilim")
async def profile(message: types.Message):
    cursor.execute("SELECT count FROM stats WHERE user=?", (message.from_user.id, ))
    row = cursor.fetchone()
    count = row[0] if row else 0
    await message.answer(f"👤 Sizning profilingiz\n\n🆔 ID: {message.from_user.id}\n📩 Olingan xabarlar: {count}")

@dp.message_handler(lambda m: m.text == "ℹ️ Bot haqida")
async def about(message: types.Message):
    await message.answer("💌 Bu anonim savol bot.\n\nDo‘stlaringiz sizga anonim xabar yuborishi mumkin.\n\nAdmin bilan aloqa: @AloqaAdminRobot")

@dp.message_handler(lambda m: m.text == "📊 Statistika")
async def bot_stats(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    await message.answer(f"📊 Bot statistikasi\n\n👥 Umumiy userlar: {count}")

@dp.message_handler(lambda m: m.text == "👥 Userlar")
async def users_list(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    cursor.execute("SELECT id, username FROM users")
    rows = cursor.fetchall()
    if not rows:
        await message.answer("Bazada hozircha foydalanuvchilar yo'q.")
        return
    text = "👥 Bot foydalanuvchilari ro'yxati:\n\n"
    for i, row in enumerate(rows):
        uname = row[1] if row[1] else "Noma'lum"
        line = f"{i+1}. {uname} (ID: {row[0]})\n"
        if len(text) + len(line) > 4000:
            await message.answer(text)
            text = ""
        text += line
    if text:
        await message.answer(text)

@dp.message_handler(lambda m: m.text == "📈 Top anonimlar")
async def top_users(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    cursor.execute("SELECT user, username, count FROM stats ORDER BY count DESC LIMIT 10")
    rows = cursor.fetchall()
    text = "🏆 Eng ko‘p xabar olgan userlar\n\n"
    for i, row in enumerate(rows):
        uname = row[1] if row[1] else "Noma'lum"
        text += f"{i+1}. {uname} (ID: {row[0]}) — {row[2]} ta xabar\n"
    await message.answer(text if rows else "Hozircha ma'lumot yo'q.")

@dp.message_handler(lambda m: m.text == "📢 Broadcast")
async def broadcast_start(message: types.Message):
    global broadcast_mode
    if message.from_user.id != ADMIN_ID:
        return
    broadcast_mode = True
    await message.answer("✍️ Yuboriladigan xabarni yozing (Matn, rasm, video va h.k)")

# ==================== ASOSIY XABARLAR ALMASHINUVI ====================
def spam(user):
    now = time.time()
    if user in last_message and now - last_message[user] < 3:
        return True
    last_message[user] = now
    return False

# JAVOB QAYTARISH QISMI (Xatolik tuzatildi)
@dp.message_handler(lambda m: m.reply_to_message, content_types=['text', 'photo', 'video', 'animation', 'voice', 'sticker', 'document'])
async def reply_system(message: types.Message):
    msg_id = message.reply_to_message.message_id
    cursor.execute("SELECT sender, receiver FROM messages WHERE msg_id=?", (msg_id,))
    row = cursor.fetchone()

    if row:
        sender, receiver = row[0], row[1]
        target = sender if message.from_user.id == receiver else receiver
        prefix = "💬 Sizga javob keldi:" if message.from_user.id == receiver else "💬 Anonim javob:"
        sender_uname = get_user_name(message.from_user)

        try:
            await bot.send_message(target, prefix)
            sent = await message.send_copy(target)
            cursor.execute("INSERT INTO messages VALUES(?,?,?)", (sent.message_id, sender, receiver))
            conn.commit()

            # MANA SHU YERDA FOYDALANUVCHIGA JAVOB KETADI
            await message.answer("✅ Javobingiz yuborildi!")

            admin_info = f"♻️ Javob qaytarildi!\n👤 Kimdan: {sender_uname} | ID: {message.from_user.id}\n🎯 Kimga ID: {target}"
            if message.content_type == 'text':
                await bot.send_message(ADMIN_ID, f"{admin_info}\n\n📝 Matn: {message.text}")
            else:
                await bot.send_message(ADMIN_ID, admin_info)
                await message.send_copy(ADMIN_ID)
                
        except Exception:
            await message.answer("❌ Xabar yuborilmadi. Foydalanuvchi botni bloklagan bo'lishi mumkin.")

@dp.message_handler(content_types=['text', 'photo', 'video', 'animation', 'voice', 'sticker', 'document'])
async def handle_all_media(message: types.Message):
    global broadcast_mode

    if broadcast_mode and message.from_user.id == ADMIN_ID:
        cursor.execute("SELECT id FROM users")
        users = cursor.fetchall()
        sent = 0
        for user in users:
            try:
                await message.send_copy(user[0])
                sent += 1
            except Exception:
                pass
        broadcast_mode = False
        await message.answer(f"✅ Xabar {sent} ta userga muvaffaqiyatli yuborildi.")
        return

    menus = ["💌 Savol yuborish", "🔗 Mening anonim linkim", "👤 Profilim", "ℹ️ Bot haqida", "👥 Userlar", "📢 Broadcast", "📊 Statistika", "📈 Top anonimlar"]
    if message.text in menus:
        return

    if message.from_user.id not in links:
        return

    receiver = links[message.from_user.id]

    if spam(message.from_user.id):
        await message.answer("⏳ Juda tez yozayapsiz, biroz kuting.")
        return

    sender_uname = get_user_name(message.from_user)

    try:
        await bot.send_message(receiver, "💌 Sizga anonim xabar keldi\n(Javob yozish uchun xabarga 'Reply' qiling):")
        sent = await message.send_copy(receiver)
        cursor.execute("INSERT INTO messages VALUES(?,?,?)", (sent.message_id, message.from_user.id, receiver))

        cursor.execute("SELECT username FROM users WHERE id=?", (receiver,))
        r_user = cursor.fetchone()
        receiver_uname = r_user[0] if r_user and r_user[0] else "Noma'lum"

        cursor.execute("SELECT count FROM stats WHERE user=?", (receiver,))
        if cursor.fetchone():
            cursor.execute("UPDATE stats SET count=count+1, username=? WHERE user=?", (receiver_uname, receiver))
        else:
            cursor.execute("INSERT INTO stats (user, username, count) VALUES (?,?,?)", (receiver, receiver_uname, 1))
        conn.commit()

        admin_info = f"📩 Yangi xabar!\n👤 Yuboruvchi: {sender_uname} | ID: {message.from_user.id}\n🎯 Qabul qiluvchi: {receiver_uname} | ID: {receiver}"

        if message.content_type == 'text':
            await bot.send_message(ADMIN_ID, f"{admin_info}\n\n📝 Matn:\n{message.text}")
        else:
            await bot.send_message(ADMIN_ID, admin_info)
            await message.send_copy(ADMIN_ID)

        me = await bot.get_me()
        link = f"https://t.me/{me.username}?start={receiver}"
        await message.answer(f"✅ Xabaringiz muvaffaqiyatli yuborildi!\n\n🔗 Sizning anonim linkingiz:\n{link}")

    except Exception:
        await message.answer("❌ Xatolik yuz berdi. Qabul qiluvchi botni bloklagan bo'lishi mumkin.")

# Dasturni ishga tushirish qismi
if __name__ == '__main__':
    # Serverni orqa fonda ishga tushiramiz
    Thread(target=run_server).start()
    # Botni ishga tushiramiz
    executor.start_polling(dp, skip_updates=True)
