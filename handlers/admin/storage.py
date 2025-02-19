from telegram.ext import *
from telegram import *
from config import Config
from database.manager.all_managers import *


async def set_storage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Run only in group chat
    chat_type = update.message.chat.type
    if not chat_type in ["group", "supergroup"]:
        await update.message.reply_text("❌ Dùng sai câu lệnh! Liên hệ với admin để biết tác dụng về câu lệnh này.")
        return
    
    # Check if user enter the password
    args = context.args 
    if not args or len(args) != 1:
        await update.message.reply_text("❌ Nhập sai định dạng câu lệnh! Liên hệ với admin để biết cấu trúc của câu lệnh này.")
        return
    
    # Check password
    password = args[0]
    if password == Config.TELEGRAM_ADMIN_PASSWORD:
        chat_id = update.effective_chat.id
        bot_info = await context.bot.get_chat_member(chat_id, context.bot.id)  
        if bot_info.status == "administrator":
            await CommonManager.update_storage_chat_id(chat_id)
            await update.message.reply_text("✅ Tôi sẽ dùng nơi đây lưu trữ các file tdata hoặc các file liên quan!\n\n"
                                            "⚠️ Lưu ý bạn không nên tự ý xóa các file của tôi!")
        elif bot_info.status == "member":
            await update.message.reply_text("❌ Phải set tôi là administrator của group!")
        else:
            await update.message.reply_text("❌ Bot chưa có trong nhóm.")
    else:
        await update.message.reply_text("❌ Sai mật khẩu!")
    return
