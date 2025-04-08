from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import sqlite3
import time
from datetime import datetime, timedelta
import random

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# SQLite Database Setup
conn = sqlite3.connect("users.db", check_same_thread=False)
c = conn.cursor()
# Users table (if not exists)
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
# Purchases table for purchase history
c.execute("""
    CREATE TABLE IF NOT EXISTS purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        description TEXT,
        timestamp INTEGER
    )
""")
conn.commit()

# Predefined star packages (stars and prices) for simulating purchases
TON_BASE = "https://app.tonkeeper.com/transfer/UQAwroBrBTSzzVYx_IXpR-R_KJ_mZQgmT7uNsUZdJ5MM68ep"
STAR_PACKAGES = [
    {"label": "⭐ 50 - $0.80",   "url": f"{TON_BASE}?amount=209700000&text=buy_stars=50"},
    {"label": "⭐ 75 - $1.20",   "url": f"{TON_BASE}?amount=315800000&text=buy_stars=75"},
    {"label": "⭐ 100 - $1.50",  "url": f"{TON_BASE}?amount=393200000&text=buy_stars=100"},
    {"label": "⭐ 150 - $2.20",  "url": f"{TON_BASE}?amount=577400000&text=buy_stars=150"},
    {"label": "⭐ 250 - $4.00",  "url": f"{TON_BASE}?amount=1049900000&text=buy_stars=250"},
    {"label": "⭐ 350 - $5.50",  "url": f"{TON_BASE}?amount=1443600000&text=buy_stars=350"},
    {"label": "⭐ 500 - $8.00",  "url": f"{TON_BASE}?amount=2099700000&text=buy_stars=500"},
    {"label": "⭐ 750 - $12.10", "url": f"{TON_BASE}?amount=3176900000&text=buy_stars=750"},
    {"label": "⭐ 1,000 - $15.50","url": f"{TON_BASE}?amount=4068200000&text=buy_stars=1000"},
    {"label": "⭐ 1,500 - $22.00","url": f"{TON_BASE}?amount=5774000000&text=buy_stars=1500"},
    {"label": "⭐ 2,500 - $40.00","url": f"{TON_BASE}?amount=10780000000&text=buy_stars=2500"},
    {"label": "⭐ 5,000 - $80.00","url": f"{TON_BASE}?amount=21560000000&text=buy_stars=5000"},
    {"label": "⭐ 10,000 - $160.00","url": f"{TON_BASE}?amount=43120000000&text=buy_stars=10000"},
    {"label": "⭐ 25,000 - $410.00","url": f"{TON_BASE}?amount=110510000000&text=buy_stars=25000"},
    {"label": "⭐ 50,000 - $810.00","url": f"{TON_BASE}?amount=221310000000&text=buy_stars=50000"},
    {"label": "⭐ 100,000 - $1600.00","url": f"{TON_BASE}?amount=399000000000&text=buy_stars=100000"},
    {"label": "⭐ 150,000 - $2380.00","url": f"{TON_BASE}?amount=595000000000&text=buy_stars=150000"},
    {"label": "⭐ 500,000 - $7700.00","url": f"{TON_BASE}?amount=1920200000000&text=buy_stars=500000"},
    {"label": "⭐ 1,000,000 - $15500.00","url": f"{TON_BASE}?amount=3865340000000&text=buy_stars=1000000"}
]

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    """Handle /start command: register user, process referral, show menu."""
    user_id = message.from_user.id
    # Check if user already exists
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user_row = c.fetchone()
    # Parse referral code if present
    referral_id = None
    args = message.get_args()  # Aiogram method to get text after /start
    if args:
        try:
            ref_id = int(args.split()[0])
            if ref_id != user_id:
                referral_id = ref_id
        except:
            referral_id = None
    if user_row is None:
        # New user: insert into users table
        c.execute("INSERT INTO users (user_id, referred_by) VALUES (?, ?)", 
                  (user_id, referral_id))
        # If referred by someone, update their invites and possibly credits
        if referral_id:
            # Check if referrer exists in DB
            c.execute("SELECT credits, is_vip FROM users WHERE user_id=?", (referral_id,))
            ref_row = c.fetchone()
            if ref_row:
                ref_credits, ref_vip = ref_row
                bonus = 10  # reward for referrer
                new_ref_credits = ref_credits + bonus
                # Determine if referrer becomes VIP due to this bonus
                new_ref_vip = ref_vip
                if ref_vip == 0 and new_ref_credits >= 50:
                    new_ref_vip = 1
                c.execute("UPDATE users SET invites = invites + 1, credits = ?, is_vip = ? WHERE user_id = ?", 
                          (new_ref_credits, new_ref_vip, referral_id))
        conn.commit()
    else:
        # Existing user: ignore referral code (can't refer again), no DB change
        pass

    # Prepare the inline keyboard menu
    menu = InlineKeyboardMarkup(row_width=2)
    menu.add(
        InlineKeyboardButton("💰 Balance", callback_data="balance"),
        InlineKeyboardButton("🎁 Daily Bonus", callback_data="daily"),
        InlineKeyboardButton("📤 Withdraw", callback_data="withdraw"),
        InlineKeyboardButton("👑 VIP Info", callback_data="vip_info"),
        InlineKeyboardButton("🔗 Referral Link", callback_data="referral"),
        InlineKeyboardButton("📈 Leaderboard", callback_data="leaderboard"),
        InlineKeyboardButton("💸 Purchase History", callback_data="history"),
        InlineKeyboardButton("💬 Live Support", url="https://t.me/SBG_SupportBot")
    )
    # Send welcome message with the menu
    first_name = message.from_user.first_name
    welcome_text = f"Hello, {first_name}! Welcome to the bot.\nPlease use the menu below to navigate."
    await message.answer(welcome_text, reply_markup=menu)

@dp.callback_query_handler(lambda cb: cb.data in 
    ["balance", "daily", "withdraw", "vip_info", "referral", "leaderboard", "history"])
async def menu_button_handler(callback_query: types.CallbackQuery):
    """Handle all inline menu button presses."""
    user_id = callback_query.from_user.id
    action = callback_query.data
    # Acknowledge the callback to remove the loading indicator
    await callback_query.answer()
    if action == "balance":
        # Fetch current credits and VIP status
        c.execute("SELECT credits, is_vip FROM users WHERE user_id=?", (user_id,))
        row = c.fetchone()
        if row:
            credits, is_vip = row
        else:
            credits, is_vip = 0, 0  # default if somehow user not in DB
        status = "VIP ⭐" if is_vip == 1 else "Regular"
        balance_text = f"💰 Your balance: {credits}⭐\nStatus: {status}"
        await bot.send_message(user_id, balance_text)
    elif action == "daily":
        # Daily bonus logic
        c.execute("SELECT credits, last_bonus, is_vip FROM users WHERE user_id=?", (user_id,))
        row = c.fetchone()
        if not row:
            # If user not in DB (should not happen if /start was used), insert them
            c.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
            conn.commit()
            credits, last_bonus, is_vip = 0, 0, 0
        else:
            credits, last_bonus, is_vip = row
        now = int(time.time())
        one_day = 24 * 3600
        if now - last_bonus >= one_day:
            # Give daily bonus
            bonus = 10  # daily bonus amount
            new_credits = credits + bonus
            new_vip = is_vip
            # Check VIP threshold
            if is_vip == 0 and new_credits >= 50:
                new_vip = 1
            # Update user data
            c.execute("UPDATE users SET credits=?, last_bonus=?, is_vip=? WHERE user_id=?", 
                      (new_credits, now, new_vip, user_id))
            conn.commit()
            # Respond with success message
            reward_text = f"You received your daily bonus of {bonus}⭐!\nYour new balance is {new_credits}⭐."
            if new_vip == 1 and is_vip == 0:
                reward_text += " 🎉 You are now a VIP!"
            await bot.send_message(user_id, reward_text)
        else:
            # Calculate remaining time for next bonus
            next_time = last_bonus + one_day
            remaining = next_time - now
            # Format remaining time into hours and minutes
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            if hours > 0:
                time_text = f"{hours} hours and {minutes} minutes"
            else:
                time_text = f"{minutes} minutes"
            await bot.send_message(user_id, 
                                   f"🎁 You have already claimed your daily bonus.\nPlease wait {time_text} for the next one.")
    elif action == "withdraw":
        # Provide withdrawal instructions or info
        withdraw_text = ("📤 **Withdraw**\n"
                         "To withdraw your stars, please contact our live support @SBG_SupportBot. "
                         "They will assist you with the withdrawal process.")
        await bot.send_message(user_id, withdraw_text, parse_mode="Markdown")
    elif action == "vip_info":
        # Explain how to become VIP
        vip_text = ("👑 **VIP Info**\n"
                    "VIP status is awarded when you purchase at least 50⭐.\n"
                    "Once you have 50 or more stars, your account will be upgraded to VIP status. "
                    "VIP users may enjoy additional benefits!")
        await bot.send_message(user_id, vip_text, parse_mode="Markdown")
    elif action == "referral":
        # Generate the user's referral link and show their invite count
        # Get current invite count
        c.execute("SELECT invites FROM users WHERE user_id=?", (user_id,))
        row = c.fetchone()
        invites = row[0] if row else 0
        # Get bot username for link
        bot_username = (await bot.get_me()).username
        ref_link = f"https://t.me/{bot_username}?start={user_id}"
        ref_text = (f"🔗 **Your Referral Link:** {ref_link}\n"
                    f"Invite friends and earn rewards!\n"
                    f"📋 You have invited **{invites}** friends so far.")
        await bot.send_message(user_id, ref_text, parse_mode="Markdown")
    elif action == "leaderboard":
        # Query top 5 users by invites and credits
        # Top invites
        c.execute("SELECT user_id, invites FROM users ORDER BY invites DESC LIMIT 5")
        top_invites = c.fetchall()
        # Top credits
        c.execute("SELECT user_id, credits FROM users ORDER BY credits DESC LIMIT 5")
        top_credits = c.fetchall()
        leaderboard_text = "🏆 **Leaderboard:**\n"
        # Invites category
        if not top_invites or top_invites[0][1] == 0:
            leaderboard_text += "\n*Top Invites:*\n_No invites yet._"
        else:
            leaderboard_text += "\n*Top Invites:*\n"
            rank = 1
            for uid, inv_count in top_invites:
                # Skip users with 0 invites
                if inv_count == 0:
                    break
                # Get name/username of the user
                try:
                    user_info = await bot.get_chat(uid)
                    if user_info.username:
                        name = f"@{user_info.username}"
                    else:
                        # Use first name (and last name if available)
                        name = user_info.first_name
                        if user_info.last_name:
                            name += " " + user_info.last_name
                except:
                    name = f"User {uid}"
                leaderboard_text += f"{rank}. {name} – {inv_count} invites\n"
                rank += 1
        # Credits category
        if not top_credits or top_credits[0][1] == 0:
            leaderboard_text += "\n*Top Credits:*\n_No credits yet._"
        else:
            leaderboard_text += "\n*Top Credits:*\n"
            rank = 1
            for uid, cred in top_credits:
                if cred == 0:
                    break
                try:
                    user_info = await bot.get_chat(uid)
                    if user_info.username:
                        name = f"@{user_info.username}"
                    else:
                        name = user_info.first_name
                        if user_info.last_name:
                            name += " " + user_info.last_name
                except:
                    name = f"User {uid}"
                leaderboard_text += f"{rank}. {name} – {cred}⭐\n"
                rank += 1
        await bot.send_message(user_id, leaderboard_text, parse_mode="Markdown")
    elif action == "history":
        # Simulate a new purchase and show purchase history
        # Choose a random star package for dummy purchase
        package = random.choice(STAR_PACKAGES)
        label = package["label"]  # e.g. "⭐ 100 - $1.50"
        # Parse the star amount from label (remove the star emoji and extract number)
        try:
            # Label format is "⭐ X - $Y"
            parts = label.split()
            dash_index = parts.index('-')
            # Join parts that make up the number (in case of comma in number)
            amount_str = "".join(parts[1:dash_index]).replace(",", "")
            stars_bought = int(amount_str)
        except Exception as e:
            stars_bought = 0
        # Insert purchase record in DB
        timestamp = int(time.time())
        c.execute("INSERT INTO purchases (user_id, description, timestamp) VALUES (?, ?, ?)",
                  (user_id, label, timestamp))
        # Update user's credits balance
        if stars_bought > 0:
            # Fetch current credits and VIP status
            c.execute("SELECT credits, is_vip FROM users WHERE user_id=?", (user_id,))
            row = c.fetchone()
            if row:
                current_credits, current_vip = row
            else:
                current_credits, current_vip = 0, 0
                c.execute("INSERT OR IGNORE INTO users (user_id, credits) VALUES (?, ?)", 
                          (user_id, 0))
            new_credits = current_credits + stars_bought
            new_vip = current_vip
            if current_vip == 0 and new_credits >= 50:
                new_vip = 1
            c.execute("UPDATE users SET credits=?, is_vip=? WHERE user_id=?", 
                      (new_credits, new_vip, user_id))
        conn.commit()
        # Retrieve last 10 purchases from DB for this user
        c.execute("SELECT timestamp, description FROM purchases WHERE user_id=? ORDER BY id DESC LIMIT 10", 
                  (user_id,))
        records = c.fetchall()
        # Reverse to chronological order (oldest first)
        records.reverse()
        # Format the history list
        history_lines = []
        for ts, desc in records:
            dt = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
            history_lines.append(f"- {dt} – {desc}")
        if history_lines:
            history_text = "💸 **Your Purchase History:**\n" + "\n".join(history_lines)
        else:
            history_text = "💸 **Your Purchase History:**\n_No purchases yet._"
        await bot.send_message(user_id, history_text, parse_mode="Markdown")

# Admin-only commands (still available but not shown in menu)
@dp.message_handler(commands=['admin_stats'])
async def cmd_admin_stats(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return  # ignore if not admin
    # Gather some statistics
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM users WHERE is_vip=1")
    total_vips = c.fetchone()[0]
    c.execute("SELECT SUM(credits) FROM users")
    total_credits = c.fetchone()[0] or 0
    c.execute("SELECT SUM(invites) FROM users")
    total_invites = c.fetchone()[0] or 0
    stats_text = (f"📊 *Bot Statistics:*\n"
                  f"- Total users: {total_users}\n"
                  f"- VIP users: {total_vips}\n"
                  f"- Total stars (credits) in circulation: {total_credits}\n"
                  f"- Total invites: {total_invites}")
    await message.reply(stats_text, parse_mode="Markdown")

@dp.message_handler(commands=['admin_vip'])
async def cmd_admin_vip(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    # Expecting an argument (user_id) after command
    args = message.get_args()
    if not args:
        await message.reply("Usage: /admin_vip <user_id>")
        return
    try:
        target_id = int(args.split()[0])
    except:
        await message.reply("Invalid user ID format.")
        return
    # Update the user's VIP status
    c.execute("UPDATE users SET is_vip = 1 WHERE user_id = ?", (target_id,))
    conn.commit()
    # Notify admin
    await message.reply(f"User {target_id} has been granted VIP status.")

# (Other admin commands or logic can be added similarly, if needed)

# Start polling for updates
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
