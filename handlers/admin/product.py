from telegram.ext import *
from telegram import *
from config import Config
from services.container import Container
from bot.state_manager import StateManager
from bot.callback_data_manager import CallbackDataManager
from database.models.product import Product
from bot.mode import Mode


def set_add_product_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mode"] = Mode.ADMIN_ADD_PRODUCT

def is_add_product_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    return context.user_data["mode"] == Mode.ADMIN_ADD_PRODUCT


async def start_add_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Run only in private chat
    if update.effective_chat.type != 'private':
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

        set_add_product_mode(update, context)

        # Construct keyboard
        categories = Container.category_manager().get_categories()
        keyboard = [[InlineKeyboardButton(category.name, callback_data=category.id)] for category in categories]
        await update.message.reply_text(
            "Hãy chọn loại sản phẩm muốn thêm!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return StateManager.SELECT_CATEGORY_FOR_PRODUCT
    else:
        await update.message.reply_text("❌ Sai mật khẩu!")
    return ConversationHandler.END


async def select_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_add_product_mode(update, context):
        return ConversationHandler.END

    # Clear buttons
    query = update.callback_query
    await query.edit_message_text(
        text="Hãy gửi file liên quan tới loại sản phẩm này hoặc có thể thêm mô tả hoặc cả hai!"
    )
    
    # Handle respectively
    category_id = query.data
    context.user_data["adding_category_id"] = category_id

    return StateManager.SEND_PRODUCT


async def send_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_add_product_mode(update, context):
        return ConversationHandler.END

    category_id = context.user_data["adding_category_id"]
    
    message = update.message
    # Check if the message is text and copy it
    reply_markup = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton(text="Hủy", callback_data=CallbackDataManager.CANCEL_ADD_PRODUCT)],
                [InlineKeyboardButton(text="Đăng bán", callback_data=f"{CallbackDataManager.ACCEPT_ADDING_PRODUCT}{category_id}")]
            ]
        )
    if update.message.text:
        await context.bot.send_message(
            chat_id=message.chat_id,
            text=message.text,
            reply_markup=reply_markup,
            reply_to_message_id=message.message_id  # Optional: makes it a reply to the original message
        )
    elif update.message.document:
        await context.bot.send_document(
            chat_id=message.chat_id,
            document=message.document.file_id,      # Send the document back
            caption=message.caption,                # Include the caption if available
            reply_to_message_id=message.message_id, # Optional: makes it a reply to the original message
            reply_markup=reply_markup
        )
    return StateManager.SEND_PRODUCT


async def stop_receive_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"✅ Stop receiving!"
    )
    return ConversationHandler.END



""" Global handler """
""" With paterrn ^ADD_PRODUCT.* """
async def accept_adding_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = Container.db()
    setting = db.get_setting()
    storage_group_id = setting.storage_group_id
    
    query = update.callback_query
    await query.edit_message_reply_markup()

    # Forward to storage file group
    forwarded_message = await context.bot.forward_message(
                                    chat_id=storage_group_id,  
                                    from_chat_id=update.effective_chat.id,
                                    message_id=update.effective_message.id
                                )

    # Get message_id of forwarded message
    forwarded_message_id = forwarded_message.message_id
    forwarded_chat_id = forwarded_message.chat_id

    query = update.callback_query
    category_id = query.data[len(CallbackDataManager.ACCEPT_ADDING_PRODUCT):].strip()

    if len(category_id) == 0:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Lỗi lập trình kêu thằng admin ra đây sửa tao vớiiiiii"
        )
        return
    

    product_manager = Container.product_manager()
    category_manager = Container.category_manager()

    product_id = product_manager.generate_product_id(category_id)
    product = Product(
        id=product_id,
        user_id="",
        backup_message_id=forwarded_message_id,
        backup_storage_group_id=forwarded_chat_id
    )
    
    product_manager.save_product(category_id, product)

    # Count products in category
    category = category_manager.get_category(category_id)
    category.avai_products += 1
    category_manager.save_category(category_id, category)

    keyboard=[[
        InlineKeyboardButton(text="Bấm vào để xóa ra khỏi gian hàng", callback_data=f"{CallbackDataManager.DELETE_PRODUCT}|{category.id}|{product.id}")
    ]]

    query = update.callback_query
    await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))


""" Global handler """
async def cancel_adding_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.delete_message()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Đã hủy đăng bán sản phẩm",
        parse_mode="HTML"
    )


async def delete_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    parts = query.data.split("|")
    if len(parts) != 3:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Lỗi lập trình, không đủ tham số"
        )
        return
    
    category_id = parts[1]
    product_id = parts[2]
    product_manager = Container.product_manager()
    product = product_manager.get_product(category_id, product_id)
    if product is None:
        await query.edit_message_text(text="Sản phẩm này đã được bán hoặc không tồn tại nữa!")
        return
    else:
        product_manager.delete_product(category_id, product_id)
        await query.delete_message()
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Đã xóa vật phẩm",
            parse_mode="HTML"
        )
        await context.bot.delete_message(
            chat_id=product.backup_storage_group_id,
            message_id=product.backup_message_id
        )
        return



add_product_conversation_handler = ConversationHandler(
    entry_points=[
        CommandHandler("admin_add_product", start_add_product)                
    ],
    states={
        StateManager.SELECT_CATEGORY_FOR_PRODUCT: [CallbackQueryHandler(select_category)],
        StateManager.SEND_PRODUCT: [MessageHandler((filters.TEXT | filters.ATTACHMENT) & ~filters.COMMAND, send_product)]
    },
    fallbacks=[
        CommandHandler("admin_stop_add_product", stop_receive_files)
    ]
)


accept_posting_query_handler = CallbackQueryHandler(accept_adding_product, pattern=f"^{CallbackDataManager.ACCEPT_ADDING_PRODUCT}.*")
cancel_posting_query_handler = CallbackQueryHandler(cancel_adding_product, pattern=f"^{CallbackDataManager.CANCEL_ADD_PRODUCT}.*$")
delete_product_query_handler = CallbackQueryHandler(delete_product, pattern=f"^{CallbackDataManager.DELETE_PRODUCT}.*$")
