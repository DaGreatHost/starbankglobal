from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import sqlite3
import time
from datetime import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# SQLite Setup
conn = sqlite3.connect("users.db")
c = conn.cursor()
c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        referred_by INTEGER,
        is_vip INTEGER DEFAULT 0,
        credits INTEGER DEFAULT 0,
        invites INTEGER DEFAULT 0,
        last_bonus INTEGER DEFAULT 0
    )
""")
conn.commit()

# Star Packages
TON_BASE = "https://app.tonkeeper.com/transfer/UQAwroBrBTSzzVYx_IXpR-R_KJ_mZQgmT7uNsUZdJ5MM68ep"
STAR_PACKAGES = [
    {"label": "⭐ 50 - $0.80", "url": f"{TON_BASE}?amount=209700000&text=buy_stars=50"},
    {"label": "⭐ 75 - $1.20", "url": f"{TON_BASE}?amount=315800000&text=buy_stars=75"},
    {"label": "⭐ 100 - $1.50", "url": f"{TON_BASE}?amount=393200000&text=buy_stars=100"},
    {"label": "⭐ 150 - $2.20", "url": f"{TON_BASE}?amount=577400000&text=buy_stars=150"},
    {"label": "⭐ 250 - $4.00", "url": f"{TON_BASE}?amount=1049900000&text=buy_stars=250"},
    {"label": "⭐ 350 - $5.50", "url": f"{TON_BASE}?amount=1443600000&text=buy_stars=350"},
    {"label": "⭐ 500 - $8.00", "url": f"{TON_BASE}?amount=2099700000&text=buy_stars=500"},
    {"label": "⭐ 750 - $12.10", "url": f"{TON_BASE}?amount=3176900000&text=buy_stars=750"},
    {"label": "⭐ 1,000 - $15.50", "url": f"{TON_BASE}?amount=4068200000&text=buy_stars=1000"},
    {"label": "⭐ 1,500 - $22.00", "url": f"{TON_BASE}?amount=5774000000&text=buy_stars=1500"},
    {"label": "⭐ 2,500 - $40.00", "url": f"{TON_BASE}?amount=10780000000&text=buy_stars=2500"},
    {"label": "⭐ 5,000 - $80.00", "url": f"{TON_BASE}?amount=21560000000&text=buy_stars=5000"},
    {"label": "⭐ 10,000 - $160.00", "url": f"{TON_BASE}?amount=43120000000&text=buy_stars=10000"},
    {"label": "⭐ 25,000 - $410.00", "url": f"{TON_BASE}?amount=110510000000&text=buy_stars=25000"},
    {"label": "⭐ 50,000 - $810.00", "url": f"{TON_BASE}?amount=221310000000&text=buy_stars=50000"},
    {"label": "⭐ 100,000 - $1600.00", "url": f"{TON_BASE}?amount=399000000000&text=buy_stars=100000"},
    {"label": "⭐ 150,000 - $2380.00", "url": f"{TON_BASE}?amount=595000000000&text=buy_stars=150000"},
    {"label": "⭐ 500,000 - $7700.00", "url": f"{TON_BASE}?amount=1920200000000&text=buy_stars=500000"},
    {"label": "⭐ 1,000,000 - $15500.00", "url": f"{TON_BASE}?amount=3865340000000&text=buy_stars=1000000"},
]

@dp.message_handler(commands=["start"])
async def start(msg: types.Message):
    user_id = msg.from_user.id
    args = msg.get_args()

    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    if not c.fetchone():
        referred_by = int(args.replace("ref_", "")) if args.startswith("ref_") else None
        c.execute("INSERT INTO users (user_id, referred_by) VALUES (?, ?)", (user_id, referred_by))
        conn.commit()

        if referred_by:
            c.execute("UPDATE users SET invites = invites + 1 WHERE user_id=?", (referred_by,))
            conn.commit()
            c.execute("SELECT invites FROM users WHERE user_id=?", (referred_by,))
            invites = c.fetchone()[0]
            if invites % 20 == 0:
                c.execute("UPDATE users SET credits = credits + 10 WHERE user_id=?", (referred_by,))
                conn.commit()

    kb = InlineKeyboardMarkup(row_width=2)
    for pkg in STAR_PACKAGES:
        kb.add(InlineKeyboardButton(pkg["label"], url=pkg["url"]))

    await msg.answer("👋 Welcome to the Telegram Stars Store!\nEarn stars via referrals and daily bonus.\nSelect a package to buy below:", reply_markup=kb)

@dp.message_handler(commands=["balance"])
async def balance(msg: types.Message):
    user_id = msg.from_user.id
    c.execute("SELECT credits, invites, is_vip FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    if not row:
        return await msg.reply("You are not registered yet. Send /start")
    credits, invites, is_vip = row
    await msg.answer(f"🌟 Your Balance:\nCredits: {credits}⭐\nInvites: {invites}\nVIP: {'✅' if is_vip else '❌'}")

@dp.message_handler(commands=["bonus"])
async def bonus(msg: types.Message):
    user_id = msg.from_user.id
    now = int(time.time())
    c.execute("SELECT last_bonus FROM users WHERE user_id=?", (user_id,))
    last_bonus = c.fetchone()[0]
    if now - last_bonus < 86400:
        next_claim = datetime.fromtimestamp(last_bonus + 86400)
        return await msg.reply(f"⏳ You can claim your next bonus on {next_claim.strftime('%Y-%m-%d %H:%M:%S')}")
    c.execute("UPDATE users SET credits = credits + 3, last_bonus = ? WHERE user_id=?", (now, user_id))
    conn.commit()
    await msg.reply("🎁 You received +3⭐ daily bonus! Come back tomorrow.")

@dp.message_handler(commands=["withdraw"])
async def withdraw(msg: types.Message):
    user_id = msg.from_user.id
    c.execute("SELECT credits, is_vip FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    if not row:
        return await msg.reply("You are not registered yet. Send /start")
    credits, is_vip = row
    if not is_vip:
        return await msg.reply("⚠ You must be a VIP to withdraw. Buy at least 50⭐ to become VIP.")
    if credits < 100:
        return await msg.reply("❌ Minimum 100⭐ required to withdraw.")
    await msg.answer("🎉 Withdrawal request accepted! We'll review and process it soon.")
    await bot.send_message(ADMIN_ID, f"🚀 Withdraw Request:\nUser: {user_id}\nCredits: {credits}⭐")

@dp.message_handler(commands=["vip"])
async def vip(msg: types.Message):
    user_id = msg.from_user.id
    c.execute("UPDATE users SET is_vip = 1 WHERE user_id=?", (user_id,))
    conn.commit()
    await msg.reply("👑 You are now a VIP! You can now withdraw once you reach 100⭐.")

@dp.message_handler(commands=["myreferral"])
async def myreferral(msg: types.Message):
    user_id = msg.from_user.id
    await msg.reply(f"📄 Your Referral Link:\nhttps://t.me/StarbankGlobal_Officialbot?start=ref_{user_id}")

@dp.message_handler(commands=["admin_stats"])
async def admin_stats(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        return
    c.execute("SELECT COUNT(*) FROM users")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM users WHERE is_vip=1")
    vips = c.fetchone()[0]
    c.execute("SELECT user_id, invites FROM users ORDER BY invites DESC LIMIT 1")
    top = c.fetchone()
    await msg.answer(f"📊 Admin Stats:\nTotal Users: {total}\nVIPs: {vips}\nTop Referrer: {top[0]} with {top[1]} invites")

@dp.message_handler(lambda m: m.text.startswith("/admin_vip "))
async def admin_vip(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        return
    parts = msg.text.split()
    if len(parts) != 2:
        return await msg.reply("Usage: /admin_vip USERID")
    uid = int(parts[1])
    c.execute("UPDATE users SET is_vip=1 WHERE user_id=?", (uid,))
    conn.commit()
    await msg.reply(f"User {uid} is now VIP")

@dp.message_handler(lambda m: m.text.startswith("/admin_credit "))
async def admin_credit(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        return
    parts = msg.text.split()
    if len(parts) != 3:
        return await msg.reply("Usage: /admin_credit USERID AMOUNT")
    uid = int(parts[1])
    amount = int(parts[2])
    c.execute("UPDATE users SET credits = credits + ? WHERE user_id=?", (amount, uid))
    conn.commit()
    await msg.reply(f"Added {amount}⭐ to user {uid}")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
