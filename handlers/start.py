from telegram.ext import *
from telegram import *
from services.container import Container
from bot.callback_data_manager import CallbackDataManager
from bot.mode import Mode
from firebase_admin import firestore


def set_user_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mode"] = Mode.USER

def is_add_product_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    return context.user_data["mode"] == Mode.USER


""" Auditted """
async def _generate_keyboard_and_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Get services
    user_manager = Container.user_manager()
    category_manager = Container.category_manager()

    # Fetch user's balance and inventory information
    user = user_manager.get_user(update.effective_user.id)
    balance = user.balance

    # Category for all services and products
    categories = category_manager.get_categories()

    keyboard = [
        [InlineKeyboardButton("Mua tài khoản", callback_data=CallbackDataManager.PURCHASE_FEATURE)],
        [InlineKeyboardButton("Nạp tiền", callback_data=CallbackDataManager.DEPOSIT_FEATURE)],
        [InlineKeyboardButton("Load lại", callback_data=CallbackDataManager.REFRESH)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message=(
        "🎉 <b>Chào mừng bạn đến với shop</b> 🎉\n\n"
        f"💰 <b>Số dư của bạn:</b> <code>{balance} VNĐ</code>\n"
        f"📌 <b>Các dịch vụ cung cấp:</b>\n\n"
    )
    for category in categories:
        message += f"<b>{category.name}:</b> <code>{category.avai_products}</code> | Giá: {category.price} VND\n"
    message += "\n\n📞 Liên hệ hỗ trợ nếu cần giúp đỡ!"

    return [reply_markup, message]
    

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

    await test_transaction()

    
async def test_transaction():
    db = Container.db().get_firestore()
    transaction = db.transaction()
    city_ref = db.collection("cities").document("SF")

    @firestore.async_transactional
    async def update_in_transaction(transaction, city_ref):
        snapshot = await city_ref.get(transaction=transaction)
        transaction.update(city_ref, {"population": snapshot.get("population") + 1})

    await update_in_transaction(transaction, city_ref)
 