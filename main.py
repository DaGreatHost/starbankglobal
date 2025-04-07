# StarBank Global Official Bot v2 – Full Production Bot
# Developed with ❤️ by Telegram Bot Builder Pro

import json
import qrcode
import io
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

API_ID = 22646749
API_HASH = "96f7ef944faa58a4a7b228015a847d18"
BOT_TOKEN = "7584295897:AAH4tyqfjNmFBQQDKbMhJzqdMu6MgpryYJM"
ADMIN_ID = 6887793763
TON_WALLET = "UQAwroBrBTSzzVYx_IXpR-R_KJ_mZQgmT7uNsUZdJ5MM68ep"

app = Client("starbank_bot_v2", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Load products
with open("star_packages.json", "r") as f:
    star_packages = json.load(f)

LANG = {
    "en": {
        "welcome": "Welcome to *StarBank Global*! 🌟",
        "choose_pack": "Please select a package below:",
        "ref_panel": "👥 *Referrals:* {count}\n🏆 *Rank:* {rank}\n🔗 Referral Link:\n{link}",
        "lang_select": "🌐 Please choose your language:"
    },
    "tl": {
        "welcome": "Maligayang pagdating sa *StarBank Global*! 🌟",
        "choose_pack": "Pumili ng star package sa ibaba:",
        "ref_panel": "👥 *Mga Imbitado:* {count}\n🏆 *Antas:* {rank}\n🔗 Referral Link:\n{link}",
        "lang_select": "🌐 Pumili ng wika:"
    }
}

user_lang = {}
user_referrals = {}
user_orders = {}
promo_codes = {"FREE100": 100}

def get_rank(count):
    if count >= 500:
        return "👑 Official Reseller"
    elif count >= 100:
        return "🧠 Influencer"
    else:
        return "👶 Starter"


@app.on_message(filters.command("start"))
async def start(client, message):
    user_id = message.from_user.id
    args = message.text.split()
    user_lang[user_id] = "en"
    if len(args) > 1 and args[1].isdigit():
        ref = int(args[1])
        if ref != user_id:
            user_referrals.setdefault(ref, set()).add(user_id)
    await show_main_menu(client, message, "en")

# Language selector removed

async def show_main_menu(client, message_or_query, lang):
    buttons = [[InlineKeyboardButton(f"{name} - {data['price']}", callback_data=f"buy_{name}")]
            for name, data in star_packages.items()]
    text = LANG[lang]["welcome"] + "\n\n" + LANG[lang]["choose_pack"]

    text = LANG[lang]["welcome"] + "\n\n" + LANG[lang]["choose_pack"]

    if isinstance(message_or_query, Message):
        await message_or_query.reply(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="markdown")
    else:
        await message_or_query.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="markdown")

   
        

@app.on_callback_query(filters.regex("buy_"))
async def buy_package(client, query):
    pack = query.data.replace("buy_", "")
    link = star_packages[pack]["link"]
    qr = qrcode.make(link)
    bio = io.BytesIO()
    bio.name = "qr.png"
    qr.save(bio, "PNG")
    bio.seek(0)
    await client.send_photo(query.from_user.id, photo=bio, caption=f"🔗 *{pack}*\n{link}", parse_mode="markdown")
    await query.answer()

@app.on_message(filters.command("affiliate"))
async def affiliate_panel(client, message):
    uid = message.from_user.id
    lang = user_lang.get(uid, "en")
    ref_count = len(user_referrals.get(uid, set()))
    rank = get_rank(ref_count)
    link = f"https://t.me/StarbankGlobal_Officialbot?start={uid}"
    msg = LANG[lang]["ref_panel"].format(count=ref_count, rank=rank, link=link)
    await message.reply(msg, parse_mode="markdown")

@app.on_message(filters.command("claim_reward"))
async def claim_reward(client, message):
    uid = message.from_user.id
    count = len(user_referrals.get(uid, set()))
    reward = (count // 100) * 100
    if reward > 0:
        await client.send_message(ADMIN_ID, f"🎁 User {uid} is claiming {reward} stars.\nPlease verify and deliver.")
        await message.reply("✅ Your claim has been sent to admin.")
    else:
        await message.reply("❌ You don’t have enough invites yet. (100 required)")

@app.on_message(filters.command("broadcast") & filters.user(ADMIN_ID))
async def broadcast(client, message):
    if len(message.command) < 2:
        return await message.reply("Usage: /broadcast Your message here")
    msg = message.text.split(" ", 1)[1]
    count = 0
    for uid in user_lang:
        try:
            await client.send_message(uid, msg)
            count += 1
        except:
            continue
    await message.reply(f"📣 Sent to {count} users.")

@app.on_message(filters.command("balance") & filters.user(ADMIN_ID))
async def show_balance(client, message):
    await message.reply(f"💰 Your TON wallet:\n`{TON_WALLET}`", parse_mode="markdown")


@app.on_message(filters.command("promo"))
async def promo_code(client, message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Use: /promo CODE")
        return
    code = args[1].strip().upper()
    reward = promo_codes.get(code)
    if reward:
        await client.send_message(ADMIN_ID, f"🎁 User {message.from_user.id} used promo code {code} and should receive {reward} stars.")
        await message.reply(f"🎉 Promo valid! You've earned {reward} stars. Admin will verify soon.")
    else:
        await message.reply("❌ Invalid promo code.")


app.run()
