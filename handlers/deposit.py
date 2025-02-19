from telegram.ext import *
from telegram import *
from bot.callback_data_manager import CallbackDataManager
from database.manager.all_managers import *
import handlers.start as start_handlers
from config import Config


async def _generate_chat_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bank_name = await CommonManager.get_bank_name(Config.BIN_CODE)

    keyboard = [
        [InlineKeyboardButton("Quay lại", callback_data=CallbackDataManager.TURN_BACK_START_FROM_DEPOSIT)]
    ]
    
    message = (f"Hãy chuyển tiền vào:\n"
        f"Ngân hàng: {bank_name}\n"
        f"Số tài khoản: {Config.BANK_ACCOUNT_NUMBER}\n"
        f"Chủ tài khoản: {Config.BANK_ACCOUNT_NAME}\n"
        f"Nội dung: TELE{update.effective_user.id}\n"
        f"Lưu ý tiền sẽ tự động nạp sau khoảng 20 - 30s. Nếu tiền không được cộng thì hãy liên hệ với @bum_chiu_bum_chiu")
    
    qr_url = f"https://img.vietqr.io/image/{Config.BIN_CODE}-{Config.BANK_ACCOUNT_NUMBER}-vietqr_pro.jpg?addInfo=TELE{update.effective_user.id}"

    return [InlineKeyboardMarkup(keyboard), message, qr_url]


""" Auditted """
async def start_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup, message, qr_url = await _generate_chat_text(update, context)
    query = update.callback_query
    await query.edit_message_media(
        media=InputMediaPhoto(
            media=qr_url,  # The new image URL or file ID
            caption=message,  # The new caption
            parse_mode="HTML"
        ),
        reply_markup=reply_markup  # Keep the inline buttons
    )


""" Auditted """
async def turn_back_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.delete_message()
    return await start_handlers.start(update, context)
