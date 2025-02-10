from telegram.ext import *
from telegram import *
from callback_data.callback_data import CallbackData
from config import Config
from services.container import Container
from states.bot_states import BotStates
from models.category import Category
import os


async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args  # Lấy các tham số sau lệnh
    if not args:
        await update.message.reply_text("❌ Bạn chưa nhập mật khẩu! Vui lòng nhập: `/admin yourpassword`")
        return ConversationHandler.END
    
    password = args[0]
    if password == Config.TELEGRAM_ADMIN_PASSWORD:
        await update.message.reply_text("✅ Xác thực thành công!")
    else:
        await update.message.reply_text("❌ Sai mật khẩu!")
    return ConversationHandler.END


async def look_up(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args  # Lấy các tham số sau lệnh
    if not args:
        await update.message.reply_text("❌ Bạn chưa nhập mật khẩu! Vui lòng nhập: `/admin yourpassword`")
        return ConversationHandler.END
    
    password = args[0]
    if password == Config.TELEGRAM_ADMIN_PASSWORD:
        await update.message.reply_text("✅ Xác thực thành công!")
    else:
        await update.message.reply_text("❌ Sai mật khẩu!")
    return ConversationHandler.END


async def start_add_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Run only in private chat
    if update.message.chat.type != 'private':
        await update.message.reply_text("❌ Hãy chat riêng, không chat ở đây")
        return ConversationHandler.END 
    
    # Check if user enter the password
    args = context.args 
    if not args or len(args) != 1:
        await update.message.reply_text("❌ Bạn chưa nhập mật khẩu! Vui lòng nhập: `/add <password>`")
        return ConversationHandler.END

    # Check password
    password = args[0]
    if password == Config.TELEGRAM_ADMIN_PASSWORD:
        db = Container.db()

        # Check store location
        setting = db.get_setting()
        if not setting:
            await update.message.reply_text("❌ Hãy vào nhóm và dùng /set_storage <password> để thiết lập nơi lưu trữ!")
            return ConversationHandler.END
            
        # Construct keyboard
        products = db.get_products()
        keyboard = [[InlineKeyboardButton(product.name, callback_data=product.id)] for product in products]
        await update.message.reply_text(
            "Hãy chọn loại sản phẩm muốn thêm!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return BotStates.SELECT_CATEGORY
    
    else:
        await update.message.reply_text("❌ Sai mật khẩu!")
    
    return ConversationHandler.END


async def select_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Clear buttons
    query = update.callback_query
    await query.edit_message_reply_markup()
    
    # Handle respectively
    category_id = query.data
    context.user_data["adding_category_id"] = category_id

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Hãy gửi file liên quan tới loại sản phẩm này!"
    )
    return BotStates.RECEIVE_FILES


async def receive_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = Container.db()
    setting = db.get_setting()
    file_name = update.message.document.file_name 
    file_id = update.message.document.file_id  
    chat_id = setting.storage_group_id
    clean_name = os.path.splitext(file_name)[0]
    category_id = context.user_data["adding_category_id"]

    # Check file name

    # Forward to storage file group
    forwarded_message = await update.message.forward(chat_id=chat_id)

    # Get message_id of forwarded message
    forwarded_message_id = forwarded_message.message_id
    forwarded_chat_id = forwarded_message.chat_id

    account = Category()
    account.category_id = category_id
    account.user_id = ""
    account.file_id = file_id
    account.backup_message_id = forwarded_message_id
    account.backup_storage_group_id = forwarded_chat_id
    
    db = Container.db()
    db.save_product(category_id, clean_name, account)

    # Send acknowledgement to user
    await update.message.reply_text(
        f"✅ File '{file_name}' (File ID: `{file_id}`) đã được gửi. category_id={category_id} | file_name={file_name} | file_id={file_id} \n"
    )
    return BotStates.RECEIVE_FILES


async def stop_receive_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"✅ Stopping here!"
    )
    return ConversationHandler.END


async def set_storage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Run only in group chat
    chat_type = update.message.chat.type
    if not chat_type in ["group", "supergroup"]:
        return ConversationHandler.END 
    
    # Check if user enter the password
    args = context.args 
    if not args or len(args) != 1:
        await update.message.reply_text("❌ Bạn chưa nhập mật khẩu! Vui lòng nhập: `/set_storage <password>`")
        return ConversationHandler.END
    
    # Check password
    password = args[0]
    if password == Config.TELEGRAM_ADMIN_PASSWORD:
        chat_id = update.effective_chat.id
        bot_info = await context.bot.get_chat_member(chat_id, context.bot.id)  
        if bot_info.status == "administrator":
            db = Container.db()
            setting = db.get_setting()
            setting.storage_group_id = chat_id
            db.save_setting(setting)
            await update.message.reply_text("✅ Tôi sẽ dùng nơi đây lưu trữ các file tdata hoặc các file liên quan!\n\n"
                                            "⚠️ Lưu ý bạn không nên tự ý xóa các file của tôi!")
        elif bot_info.status == "member":
            await update.message.reply_text("❌ Phải set tôi là administrator của group!")
        else:
            await update.message.reply_text("❌ Bot chưa có trong nhóm.")
    else:
        await update.message.reply_text("❌ Sai mật khẩu!")
    
    return ConversationHandler.END

