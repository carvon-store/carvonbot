import os
cat > bot.py << 'EOF'
import os
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "7570067641:AAHIG4RXrdJhIIuSgkZmojBge4cI5q7TXN4"
ADMIN_ID = 1481352341
SUPABASE_URL = "https://scmzqkunlcdqhxuydqcd.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNjbXpxa3VubGNkcWh4dXlkcWNkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzg2NjMwOTgsImV4cCI6MjA5NDIzOTA5OH0.yrxpfcw9-FuddqAV76BTcvd4MwzOsV7syfG9k6qUaP0"

STATUS_NAMES = {"preparing":"⚙️ Tayyorlanmoqda","delivering":"🚚 Yetkazilmoqda","delivered":"✅ Yetkazildi","cancelled":"❌ Bekor qilindi"}
STATUS_MESSAGES = {"preparing":"⚙️ {name}! Buyurtmangiz ({order_id}) tayyorlanmoqda! 🚀","delivering":"🚚 {name}! Buyurtmangiz ({order_id}) yolda! 📞","delivered":"✅ {name}! Buyurtmangiz ({order_id}) yetkazildi! Rahmat! 🎉","cancelled":"❌ {name}! Buyurtmangiz ({order_id}) bekor qilindi."}

def update_status(order_id, status):
    try:
        encoded_id = requests.utils.quote(order_id)
        r = requests.patch(
            f"{SUPABASE_URL}/rest/v1/orders?order_id=eq.{encoded_id}",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=representation"
            },
            json={"status": status}
        )
        logger.info(f"Supabase update: {r.status_code} {r.text}")
        return r.status_code in [200, 204]
    except Exception as e:
        logger.error(f"Supabase error: {e}")
        return False

def make_keyboard(order_id, chat_id, name, current=None):
    all_s = [("preparing","⚙️ Tayyorlanmoqda"),("delivering","🚚 Yetkazilmoqda"),("delivered","✅ Yetkazildi"),("cancelled","❌ Bekor qilish")]
    buttons = []
    row = []
    for key, label in all_s:
        if key != current:
            row.append(InlineKeyboardButton(label, callback_data=f"s:{order_id}:{chat_id}:{key}:{name}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot ishlayapti!")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split(":")
    if len(parts) < 4: return
    order_id, chat_id, status_key = parts[1], parts[2], parts[3]
    name = parts[4] if len(parts) > 4 else "Mijoz"
    status_text = STATUS_NAMES.get(status_key, status_key)
    
    success = update_status(order_id, status_text)
    
    notified = "Mijoz ID yoq"
    if chat_id and chat_id != "0":
        msg = STATUS_MESSAGES.get(status_key,"").format(name=name, order_id=order_id)
        try:
            await context.bot.send_message(chat_id=int(chat_id), text=msg)
            notified = "✅ Mijozga xabar yuborildi"
        except Exception as e:
            notified = f"⚠️ Xabar yuborilmadi: {e}"
    
    kb = make_keyboard(order_id, chat_id, name, current=status_key)
    await query.edit_message_text(
        f"📦 {order_id}\n👤 {name}\n📊 {status_text}\n📱 {notified}\n{'✅ Supabase yangilandi' if success else '❌ Supabase xatolik'}\n\nKeyingi status:",
        reply_markup=kb
    )

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    logger.info("✅ Bot ishga tushdi!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
EOF
