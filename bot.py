import os
import json
import logging
import gspread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from google.oauth2.service_account import Credentials

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN', '7570067641:AAHIG4RXrdJhIIuSgkZmojBge4cI5q7TXN4')
ADMIN_ID = int(os.environ.get('ADMIN_ID', '1481352341'))
SHEET_ID = os.environ.get('SHEET_ID', '')

STATUSES = {
    'preparing': ('⚙️ Tayyorlanmoqda', '#CCE5FF'),
    'delivering': ('🚚 Yetkazilmoqda', '#D4EDDA'),
    'delivered': ('✅ Yetkazildi', '#D1ECF1'),
    'cancelled': ('❌ Bekor qilindi', '#F8D7DA'),
}

STATUS_MESSAGES = {
    'preparing': "⚙️ Hurmatli {name}!\n\nBuyurtmangiz ({order_id}) tayyorlanmoqda.\nTez orada yetkazib beramiz! 🚀",
    'delivering': "🚚 Hurmatli {name}!\n\nBuyurtmangiz ({order_id}) yo'lda!\nKuryer siz bilan bog'lanadi. 📞",
    'delivered': "✅ Hurmatli {name}!\n\nBuyurtmangiz ({order_id}) yetkazildi!\nXaridingiz uchun rahmat! 🎉\n\nCarvon Store",
    'cancelled': "❌ Hurmatli {name}!\n\nBuyurtmangiz ({order_id}) bekor qilindi.\nSavollar uchun: @Carvonshopbot",
}

def get_sheet():
    try:
        creds_json = os.environ.get('GOOGLE_CREDS', '{}')
        creds_dict = json.loads(creds_json)
        scopes = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        gc = gspread.authorize(creds)
        sh = gc.open_by_key(SHEET_ID)
        return sh.worksheet('Buyurtmalar')
    except Exception as e:
        logger.error(f"Sheet error: {e}")
        return None

def update_sheet_status(order_id, status_text):
    try:
        sheet = get_sheet()
        if not sheet:
            return False
        records = sheet.get_all_records()
        for i, row in enumerate(records, start=2):
            if str(row.get('Buyurtma ID', '')) == str(order_id):
                sheet.update_cell(i, 10, status_text)
                return True
        return False
    except Exception as e:
        logger.error(f"Update error: {e}")
        return False

def get_order_info(order_id):
    try:
        sheet = get_sheet()
        if not sheet:
            return None
        records = sheet.get_all_records()
        for row in records:
            if str(row.get('Buyurtma ID', '')) == str(order_id):
                return row
        return None
    except Exception as e:
        logger.error(f"Get order error: {e}")
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛍️ Carvon Store Admin Bot\n\nBuyurtmalar avtomatik keladi va siz tugmalar orqali statusni o'zgartirasiz!"
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data.split(':')
    action = data[0]
    order_id = data[1]
    
    if action == 'status':
        new_status_key = data[2]
        status_text, _ = STATUSES[new_status_key]
        
        order = get_order_info(order_id)
        if not order:
            await query.edit_message_text(f"❌ Buyurtma {order_id} topilmadi!")
            return
        
        update_sheet_status(order_id, status_text)
        
        customer_chat_id = order.get('Chat ID', '')
        customer_name = order.get('Mijoz ismi', 'Mijoz')
        
        if customer_chat_id:
            msg = STATUS_MESSAGES[new_status_key].format(
                name=customer_name,
                order_id=order_id
            )
            try:
                await context.bot.send_message(chat_id=int(customer_chat_id), text=msg)
                customer_notified = "✅ Mijozga xabar yuborildi"
            except:
                customer_notified = "⚠️ Mijozga xabar yuborilmadi"
        else:
            customer_notified = "⚠️ Mijoz Chat ID yo'q"
        
        await query.edit_message_text(
            f"✅ Status yangilandi!\n\n"
            f"📦 Buyurtma: {order_id}\n"
            f"👤 Mijoz: {customer_name}\n"
            f"📊 Yangi status: {status_text}\n"
            f"📱 {customer_notified}"
        )

async def new_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bu funksiya webhook orqali chaqiriladi"""
    pass

def send_order_notification(bot_token, admin_id, order_data):
    """Yangi buyurtma kelganda admin ga tugmali xabar yuborish"""
    import requests
    
    order_id = order_data.get('order_id', '#000000')
    
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "⚙️ Tayyorlanmoqda", "callback_data": f"status:{order_id}:preparing"},
                {"text": "🚚 Yetkazilmoqda", "callback_data": f"status:{order_id}:delivering"}
            ],
            [
                {"text": "✅ Yetkazildi", "callback_data": f"status:{order_id}:delivered"},
                {"text": "❌ Bekor qilish", "callback_data": f"status:{order_id}:cancelled"}
            ]
        ]
    }
    
    text = (
        f"🛍️ YANGI BUYURTMA {order_id}!\n\n"
        f"👤 Mijoz: {order_data.get('name', '')}\n"
        f"📞 Telefon: {order_data.get('phone', '')}\n"
        f"📍 Manzil: {order_data.get('address', '')}\n"
        f"💳 To'lov: {order_data.get('payment', '')}\n"
        f"📦 {order_data.get('items', '')}\n"
        f"💰 Jami: {order_data.get('total', '')}\n"
        f"📝 Izoh: {order_data.get('note', 'Yo\'q')}"
    )
    
    requests.post(
        f"https://api.telegram.org/bot{bot_token}/sendMessage",
        json={
            "chat_id": admin_id,
            "text": text,
            "reply_markup": keyboard
        }
    )

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    logger.info("Bot ishga tushdi!")
    app.run_polling()

if __name__ == '__main__':
    main()
