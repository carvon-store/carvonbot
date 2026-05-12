import os
import json
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN', '7570067641:AAHIG4RXrdJhIIuSgkZmojBge4cI5q7TXN4')
ADMIN_ID = int(os.environ.get('ADMIN_ID', '1481352341'))
SHEET_URL = os.environ.get('SHEET_URL', '')

STATUS_MESSAGES = {
    'preparing': "⚙️ Hurmatli {name}!\n\nBuyurtmangiz ({order_id}) tayyorlanmoqda.\nTez orada yetkazib beramiz! 🚀",
    'delivering': "🚚 Hurmatli {name}!\n\nBuyurtmangiz ({order_id}) yo'lda!\nKuryer siz bilan bog'lanadi. 📞",
    'delivered': "✅ Hurmatli {name}!\n\nBuyurtmangiz ({order_id}) yetkazildi!\nXaridingiz uchun rahmat! 🎉\n\nCarvon Store",
    'cancelled': "❌ Hurmatli {name}!\n\nBuyurtmangiz ({order_id}) bekor qilindi.\nSavollar uchun: @Carvonshopbot",
}

STATUS_NAMES = {
    'preparing': '⚙️ Tayyorlanmoqda',
    'delivering': '🚚 Yetkazilmoqda',
    'delivered': '✅ Yetkazildi',
    'cancelled': '❌ Bekor qilindi',
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛍️ Carvon Store Admin Bot\n\n"
        "✅ Bot ishlayapti!\n\n"
        "Yangi buyurtma kelganda tugmalar orqali statusni o'zgartira olasiz.\n"
        "Mijozga avtomatik xabar ketadi! 🚀"
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    parts = query.data.split(':')
    if len(parts) < 4:
        return

    order_id = parts[1]
    customer_chat_id = parts[2]
    status_key = parts[3]
    customer_name = parts[4] if len(parts) > 4 else "Mijoz"

    status_text = STATUS_NAMES.get(status_key, status_key)

    if SHEET_URL:
        try:
            url = SHEET_URL + '?data=' + requests.utils.quote(json.dumps({
                'action': 'update_status',
                'order_id': order_id,
                'status': status_text
            }))
            requests.get(url, timeout=10)
        except Exception as e:
            logger.error(f"Sheet error: {e}")

    notified = "⚠️ Mijoz Chat ID yo'q"
    if customer_chat_id and customer_chat_id != '0':
        msg = STATUS_MESSAGES.get(status_key, '').format(
            name=customer_name, order_id=order_id
        )
        try:
            await context.bot.send_message(chat_id=int(customer_chat_id), text=msg)
            notified = "✅ Mijozga xabar yuborildi"
        except Exception as e:
            logger.error(f"Send error: {e}")
            notified = "⚠️ Mijozga xabar yuborilmadi"

    await query.edit_message_text(
        f"✅ Status yangilandi!\n\n"
        f"📦 {order_id}\n"
        f"👤 {customer_name}\n"
        f"📊 {status_text}\n"
        f"📱 {notified}"
    )

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    logger.info("✅ Bot ishga tushdi!")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
