from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import sqlite3
import time

TOKEN = "8717578342:AAHfOuaZFiNwsCmyGezQLPqnvKvLMvHPojE"
ADMIN_ID = 5578534822

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

conn = sqlite3.connect("anon.db")
cursor = conn.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY)")
cursor.execute("CREATE TABLE IF NOT EXISTS messages(msg_id INTEGER,sender INTEGER,receiver INTEGER)")
cursor.execute("CREATE TABLE IF NOT EXISTS stats(user INTEGER,count INTEGER)")

conn.commit()

links = {}
last_message = {}
broadcast_mode = False


# NGL STYLE MENU
menu = ReplyKeyboardMarkup(resize_keyboard=True)

menu.add(
KeyboardButton("💌 Savol yuborish"),
KeyboardButton("🔗 Mening anonim linkim")
)

menu.add(
KeyboardButton("👤 Profilim"),
KeyboardButton("ℹ️ Bot haqida")
)


# START
@dp.message_handler(commands=['start'])
async def start(message: types.Message):

    cursor.execute("INSERT OR IGNORE INTO users VALUES(?)",(message.from_user.id,))
    conn.commit()

    args = message.get_args()

    if args:

        links[message.from_user.id] = int(args)

        await message.answer(
            "💌 Anonim savol yozing\n\n"
            "Matn, rasm yoki video yuborishingiz mumkin.",
            reply_markup=menu
        )

    else:

        me = await bot.get_me()

        link = f"https://t.me/{me.username}?start={message.from_user.id}"

        await message.answer(
            f"💌 Sizning anonim sahifangiz\n\n"
            f"{link}",
            reply_markup=menu
        )


# LINK
@dp.message_handler(lambda m: m.text=="🔗 Mening anonim linkim")
async def link(message: types.Message):

    me = await bot.get_me()

    link = f"https://t.me/{me.username}?start={message.from_user.id}"

    await message.answer(
        f"💌 Sizga anonim savol yuborish linki:\n\n{link}"
    )


# PROFIL
@dp.message_handler(lambda m: m.text=="👤 Profilim")
async def profile(message: types.Message):

    cursor.execute("SELECT count FROM stats WHERE user=?",(message.from_user.id,))
    row = cursor.fetchone()

    if row:
        count=row[0]
    else:
        count=0

    await message.answer(
        f"👤 Sizning profilingiz\n\n"
        f"🆔 ID: {message.from_user.id}\n"
        f"📩 Olingan savollar: {count}"
    )


# BOT HAQIDA
@dp.message_handler(lambda m: m.text=="ℹ️ Bot haqida")
async def about(message: types.Message):

    await message.answer(
        "💌 Bu anonim savol bot.\n\n"
        "Do‘stlaringiz sizga anonim savol yuborishi mumkin.\n\n"
        "Admin bilan aloqa: @AloqaAdminRobot"
    )


# SPAM HIMOYA
def spam(user):

    now=time.time()

    if user in last_message:

        if now-last_message[user] < 5:
            return True

    last_message[user]=now
    return False


# REPLY JAVOB
@dp.message_handler(lambda m: m.reply_to_message, content_types=['text','photo','video'])
async def reply(message: types.Message):

    msg = message.reply_to_message.message_id

    cursor.execute("SELECT sender FROM messages WHERE msg_id=?", (msg,))
    row = cursor.fetchone()

    if not row:
        return

    sender = row[0]

    # TEXT
    if message.content_type == "text":

        await bot.send_message(
            sender,
            f"💬 Sizga javob keldi\n\n{message.text}"
        )

        await bot.send_message(
            ADMIN_ID,
            f"↩️ Javob\n\n"
            f"👤 @{message.from_user.username}\n"
            f"🆔 {message.from_user.id}\n\n"
            f"{message.text}"
        )

    # PHOTO
    elif message.content_type == "photo":

        await bot.send_photo(
            sender,
            message.photo[-1].file_id,
            caption="💬 Sizga rasm bilan javob keldi"
        )

        await bot.send_photo(
            ADMIN_ID,
            message.photo[-1].file_id,
            caption=f"🖼 Javob rasm\n👤 @{message.from_user.username}\n🆔 {message.from_user.id}"
        )

    # VIDEO
    elif message.content_type == "video":

        await bot.send_video(
            sender,
            message.video.file_id,
            caption="💬 Sizga video javob keldi"
        )

        await bot.send_video(
            ADMIN_ID,
            message.video.file_id,
            caption=f"🎬 Javob video\n👤 @{message.from_user.username}\n🆔 {message.from_user.id}"
        )

#SAVOL
@dp.message_handler(content_types=['text'])
async def send_text(message: types.Message):

    if message.from_user.id not in links:
        return

    receiver = links[message.from_user.id]

    if spam(message.from_user.id):
        await message.answer("⏳ Juda tez yozayapsiz")
        return

    sent = await bot.send_message(
        receiver,
        f"💌 Sizga anonim savol\n\n{message.text}\n\n↩️ Reply qilib javob yozing"
    )

    cursor.execute(
        "INSERT INTO messages VALUES(?,?,?)",
        (sent.message_id, message.from_user.id, receiver)
    )

    conn.commit()

    await bot.send_message(
        ADMIN_ID,
        f"📩 Savol\n\n"
        f"👤 @{message.from_user.username}\n"
        f"🆔 {message.from_user.id}\n"
        f"🎯 Receiver: {receiver}\n\n"
        f"{message.text}"
    )

    me = await bot.get_me()

    link = f"https://t.me/{me.username}?start={receiver}"

    await message.answer(
        f"✅ Savolingiz yuborildi!\n\n"
        f"🔗 Sizning anonim linkingiz:\n{link}"
    )

# RASM
@dp.message_handler(content_types=['photo'])
async def photo(message: types.Message):

    if message.from_user.id not in links:
        return

    receiver = links[message.from_user.id]

    sent = await bot.send_photo(
        receiver,
        message.photo[-1].file_id,
        caption="💌 Sizga anonim rasm"
    )

    cursor.execute(
        "INSERT INTO messages VALUES(?,?,?)",
        (sent.message_id, message.from_user.id, receiver)
    )

    conn.commit()

    await bot.send_photo(
        ADMIN_ID,
        message.photo[-1].file_id,
        caption=f"🖼 Anonim rasm\n\n"
        f"👤 @{message.from_user.username}\n"
        f"🆔 ID: {message.from_user.id}"
    )


# VIDEO
@dp.message_handler(content_types=['video'])
async def video(message: types.Message):

    if message.from_user.id not in links:
        return

    receiver = links[message.from_user.id]

    sent = await bot.send_video(
        receiver,
        message.video.file_id,
        caption="💌 Sizga anonim video"
    )

    cursor.execute(
        "INSERT INTO messages VALUES(?,?,?)",
        (sent.message_id, message.from_user.id, receiver)
    )

    conn.commit()

    await bot.send_video(
        ADMIN_ID,
        message.video.file_id,
        caption=f"🎥 Anonim video\n\n"
        f"👤 @{message.from_user.username}\n"
        f"🆔 ID: {message.from_user.id}"
    )


# ADMIN PANEL
@dp.message_handler(commands=['admin'])
async def admin(message: types.Message):

    if message.from_user.id!=ADMIN_ID:
        return

    keyboard=ReplyKeyboardMarkup(resize_keyboard=True)

    keyboard.add(
    KeyboardButton("📊 Statistika"),
    KeyboardButton("📈 Top anonimlar")
    )

    keyboard.add(
    KeyboardButton("📢 Broadcast")
    )

    await message.answer("👨‍💻 Admin panel",reply_markup=keyboard)


# STATISTIKA
@dp.message_handler(lambda m: m.text=="📊 Statistika")
async def stats(message: types.Message):

    if message.from_user.id!=ADMIN_ID:
        return

    cursor.execute("SELECT COUNT(*) FROM users")

    users=cursor.fetchone()[0]

    await message.answer(f"👥 Userlar: {users}")


# TOP (FAKAT ADMIN)
@dp.message_handler(lambda m: m.text=="📈 Top anonimlar")
async def top(message: types.Message):

    if message.from_user.id!=ADMIN_ID:
        return

    cursor.execute("SELECT user,count FROM stats ORDER BY count DESC LIMIT 10")

    rows=cursor.fetchall()

    text="🏆 Eng ko‘p savol olgan userlar\n\n"

    for i,row in enumerate(rows):

        text+=f"{i+1}. ID {row[0]} — {row[1]} savol\n"

    await message.answer(text)


# BROADCAST
@dp.message_handler(lambda m: m.text=="📢 Broadcast")
async def bc(message: types.Message):

    global broadcast_mode

    if message.from_user.id!=ADMIN_ID:
        return

    broadcast_mode=True

    await message.answer("📢 Yuboriladigan matnni yozing")


@dp.message_handler(lambda m: m.from_user.id==ADMIN_ID)
async def send_bc(message: types.Message):

    global broadcast_mode

    if not broadcast_mode:
        return

    cursor.execute("SELECT id FROM users")

    users=cursor.fetchall()

    for user in users:

        try:
            await bot.send_message(user[0],message.text)
        except:
            pass

    broadcast_mode=False

    await message.answer("✅ Xabar yuborildi")


if __name__ == "__main__":
    executor.start_polling(dp)