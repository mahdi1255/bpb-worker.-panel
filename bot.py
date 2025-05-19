import logging
import asyncio
import hashlib
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler

TOKEN = "توکن_ربات_تو_اینجا_بذار"
GROUP_CHAT_ID = -1001234567890  # آیدی عددی گروه رو اینجا بذار

user_states = {}

logging.basicConfig(level=logging.INFO)

def check_strength(password):
    score = 0
    if len(password) >= 8:
        score += 1
    if any(c.islower() for c in password):
        score += 1
    if any(c.isupper() for c in password):
        score += 1
    if any(c.isdigit() for c in password):
        score += 1
    if any(c in "!@#$%^&*()_+-=" for c in password):
        score += 1

    if score <= 2:
        return "ضعیف"
    elif score == 3 or score == 4:
        return "متوسط"
    else:
        return "قوی"

async def check_pwned(password):
    sha1pass = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
    prefix = sha1pass[:5]
    suffix = sha1pass[5:]

    url = f"https://api.pwnedpasswords.com/range/{prefix}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                hashes = await resp.text()
                for line in hashes.splitlines():
                    if line.startswith(suffix):
                        return True
    return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🔍 تست پسورد", callback_data="check_password")]]
    await update.message.reply_text(
        "سلام! من ربات بررسی امنیت رمز عبور هستم.

"
        "رمز عبور خود را ارسال کنید تا امنیت آن را بررسی کنم.

"
        "🔒 نگران نباشید! هیچ رمز عبوری در سرور یا دیتای ما ذخیره نمی‌شود.
"
        "فقط بررسی می‌شود که آیا رمز شما در دیتابیس‌های هک شده لو رفته یا خیر.

"
        "همچنین می‌توانید با /generate رمز قوی دریافت کنید.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    user = update.effective_user
    await context.bot.send_message(
        chat_id=GROUP_CHAT_ID,
        text=f"🆕 کاربر جدید:
👤 {user.full_name}
🆔 @{user.username or '---'}
🔽 دستور /start را زد."
    )

async def generate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import random, string
    password = ''.join(random.choices(string.ascii_letters + string.digits + "!@#$%^&*", k=12))
    await update.message.reply_text(f"🔐 رمز پیشنهادی:
`{password}`", parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_states[user_id] = "awaiting_password"
    await query.message.reply_text("🔑 لطفاً رمز عبور خود را ارسال کنید:")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_states.get(user_id) == "awaiting_password":
        password = update.message.text
        strength = check_strength(password)
        pwned = await check_pwned(password)
        msg = f"✅ قدرت رمز: *{strength}*
"
        if pwned:
            msg += "❗️ این رمز در دیتابیس‌های هک شده پیدا شده است. لطفاً سریعاً آن را تغییر دهید!"
        else:
            msg += "🔒 این رمز در دیتابیس‌های لو رفته یافت نشد."
        await update.message.reply_text(msg, parse_mode="Markdown")
        del user_states[user_id]

async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("generate", generate))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("ربات در حال اجراست...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())