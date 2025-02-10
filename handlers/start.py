from telegram.ext import *
from telegram import *
from states.bot_states import BotStates
from callback_data.callback_data import CallbackData
from services.container import Container
from handlers.deposit import start_deposit
from handlers.purchase import start_purchase


async def _preprocess_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Get services
    db = Container.db()
    payos = Container.payos()

    # Check last payment and send hello message
    user = db.get_user(update.effective_user.id)
    if user.latest_payment_id != -1:
        data = payos.get_payment(user.latest_payment_id)
        if data.status == "PENDING":
            payos.cancel_payment(user.latest_payment_id)
        elif data.status == "PAID":
            user.balance += int(data.amountPaid)
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text=f"Bạn đã nạp thêm số tiền {data.amountPaid} VND"
            )
        user.latest_payment_id = -1
        db.save_user(update.effective_user.id, user)


async def _send_messsage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Get services
    db = Container.db()

    # Fetch user's balance and inventory information
    user = db.get_user(update.effective_user.id)
    balance = user.balance

    # Category for all services and products
    categories = db.get_categories()

    # Setup keyboard
    keyboard = [[InlineKeyboardButton(category.name, callback_data=category.id)] for category in categories]
    keyboard.append([
            InlineKeyboardButton("Re-fresh", callback_data=CallbackData.REFRESH), 
            InlineKeyboardButton("Mua tài khoản", callback_data=CallbackData.BUY_REQUEST)
        ])
    keyboard.append([
            InlineKeyboardButton("Nạp tiền", callback_data=CallbackData.DEPOSIT_REQUEST)
        ])
    
    # Message
    message=(
        "🎉 <b>Chào mừng bạn đến với shop</b> 🎉\n\n"
        f"💰 <b>Số dư của bạn:</b> <code>{balance} VNĐ</code>\n"
        f"📌 <b>Các dịch vụ cung cấp:</b>\n\n"
    )
    for category in categories:
        message += f"<b>{category.name}:</b> <code>{category.avai_products}</code>\n"
    message += "\n\n📞 Liên hệ hỗ trợ nếu cần giúp đỡ!"
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    

""" Called by another handler and ConversationHandler """
""" Run when bot is in initial state of system """
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Handle old transaction
    await _preprocess_start(update, context)

    # Send message
    await _send_messsage(update, context)
    return BotStates.START


""" Choose one of those services in keyboard markup of _send_messsage function """ 
async def choose_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Clear buttons
    query = update.callback_query
    await query.edit_message_reply_markup()
    
    # Handle respectively
    if query.data == CallbackData.REFRESH:
        return await start(update, context)
    elif query.data == CallbackData.BUY_REQUEST:
        return await start_purchase(update, context)
    elif query.data == CallbackData.DEPOSIT_REQUEST:
        return await start_deposit(update, context)
    else:
        query.data

        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Lỗi không mong muốn! Hãy bắt đầu lại!"
        )
        return await start(update, context)

