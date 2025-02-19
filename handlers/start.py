from telegram.ext import *
from telegram import *
from bot.callback_data_manager import CallbackDataManager
from database.manager.all_managers import *
from bot.mode import Mode


def set_user_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mode"] = Mode.USER

def is_add_product_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    return context.user_data["mode"] == Mode.USER


""" Auditted """
async def _generate_keyboard_and_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Fetch user's balance and inventory information
    user = await UserManager.get_user(update.effective_user.id)  

    keyboard = [
        [InlineKeyboardButton("Mua tài khoản", callback_data=CallbackDataManager.PURCHASE_FEATURE)],
        [InlineKeyboardButton("Nạp tiền", callback_data=CallbackDataManager.DEPOSIT_FEATURE)],
        [InlineKeyboardButton("Load lại", callback_data=CallbackDataManager.REFRESH)]
    ]

    message=(
        "🎉 <b>Chào mừng bạn đến với shop</b> 🎉\n\n"
        f"💰 <b>Số dư của bạn:</b> <code>{user.balance} VNĐ</code>\n"
        f"📌 <b>Các dịch vụ cung cấp:</b>\n\n"
    )

    categories = await CategoryManager.get_categories()
    for category in categories:
        message += f"<b>{category.name}:</b> <code>{category.avai_products}</code> | Giá: {category.price} VND\n"
    message += "\n\n📞 Liên hệ hỗ trợ nếu cần giúp đỡ!"

    return [InlineKeyboardMarkup(keyboard), message]
    

async def _send_hint_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    commands = [
        ('start', 'Bắt đầu nói chuyện với bot'),
        ('help', 'Show help message'),
        ('admin_add_category', '[ADMIN ONLY] Thêm danh mục'),
        ('admin_add_product', '[ADMIN ONLY] Thêm sản phẩm'),
    ]
    # Set the commands for the bot
    await bot.set_my_commands(commands)


""" Auditted """
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    set_user_mode(update, context)

    reply_markup, message = await _generate_keyboard_and_text(update, context)
    query = update.callback_query
    if query:
        if query.data == CallbackDataManager.REFRESH:
            await query.edit_message_reply_markup()
            await query.edit_message_text(
                text=message,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
        elif query.data == CallbackDataManager.TURN_BACK_START_FROM_DEPOSIT:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=message,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
        elif query.data == CallbackDataManager.TURN_BACK_START_FROM_PURCHASE:
            await query.edit_message_text(
                text=message,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
    else:
        await _send_hint_commands(update, context)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=message,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
