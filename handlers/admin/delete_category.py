from telegram.ext import *
from telegram import *
from config import Config
from database.manager.all_managers import *
from bot.state_manager import StateManager
from database.models.category import Category
from database.models.product import Product
from bot.callback_data_manager import CallbackDataManager
from typing import List
from functools import partial
from bot.mode import Mode
import asyncio



def set_delete_category_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mode"] = Mode.ADMIN_DELETE_CATEGORY

def is_delete_category_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    return context.user_data["mode"] == Mode.ADMIN_DELETE_CATEGORY


async def _start_keyboard_and_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    categories = await CategoryManager.get_categories()
    keyboard = [[InlineKeyboardButton(text=category.name, callback_data=f"{CallbackDataManager.DELETE_CATEGORY}{category.id}")] for category in categories]
    message = f"Hãy chọn một category để xóa"
    return [InlineKeyboardMarkup(keyboard), message]


async def start_delete_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Run only in private chat
    if update.effective_chat.type != 'private':
        await update.message.reply_text("❌ Hãy chat lệnh này riêng, không chat ở đây")
        return ConversationHandler.END 
    
    # Check if user enter the password
    args = context.args 
    if not args or len(args) != 1:
        await update.message.reply_text("❌ Bạn chưa nhập mật khẩu! Vui lòng nhập: `/admin_add_category <password>`")
        return ConversationHandler.END

    # Check password
    password = args[0]
    if password == Config.TELEGRAM_ADMIN_PASSWORD:
        set_delete_category_mode(update, context)

        markup, message = _start_keyboard_and_text(update, context)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=message,
            reply_markup=markup,
            parse_mode="HTML"
        )

    else:
        await update.message.reply_text("❌ Sai mật khẩu!")
    return ConversationHandler.END



async def choose_delete_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    delete_category_id = query.data[len(CallbackDataManager.DELETE_CATEGORY):]
    category = await CategoryManager.get_category(delete_category_id)

    if category is None:
        await query.edit_message_text(f"Danh mục bạn đã chọn đã không còn tồn tại!")
        return

    message = f"Bạn có chắc là muốn xóa danh mục `{category.name}`. Nếu danh mục còn tồn tại sản phẩm, tôi sẽ gửi trả lại bạn hết."
    keyboard = [
        [InlineKeyboardButton("Xác nhận xóa", callback_data=f"{CallbackDataManager.CONFIRM_DELETE_CATEGORY}{category.id}")]
    ]
    await query.edit_message_text(
        text=message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )


async def confirm_delete_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    delete_category_id = query.data[len(CallbackDataManager.CONFIRM_DELETE_CATEGORY):]

    # category = Container.category_manager().get_category(delete_category_id)

    # if category is None:
    #     await query.edit_message_text(f"Danh mục bạn đã chọn đã không còn tồn tại!")
    #     return
    
    transactions = [
        partial(ProductManager.delete_products, category_id=delete_category_id),
        partial(CategoryManager.delete_category, category_id=delete_category_id)
    ]
    results = await CategoryManager.exec_transactions(transactions)
    products: List[Product] = results[0]
    category: Category = results[1]

    message = f"Đã xóa danh mục `{category.name}`. Chuẩn bị gửi trả sản phẩm nếu có..."
    await query.edit_message_text(
        text=message,
        parse_mode="HTML"
    )

    for product in products:
        if product.user_id == -1:
            await context.bot.forward_message(
                chat_id=update.effective_chat.id,
                from_chat_id=product.backup_chat_id,
                message_id=product.backup_message_id
            )
            await asyncio.sleep(0.2)



handlers = [
    CommandHandler("admin_delete_category", start_delete_category),
    CallbackQueryHandler(choose_delete_category, pattern=f"^{CallbackDataManager.DELETE_CATEGORY}.*"),
    CallbackQueryHandler(confirm_delete_category, pattern=f"^{CallbackDataManager.CONFIRM_DELETE_CATEGORY}.*")
]