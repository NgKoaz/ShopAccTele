from telegram.ext import *
from telegram import *
from states.bot_states import BotStates
from callback_data.callback_data import CallbackData
from callback_data.callback_data import CallbackData
from services.container import Container
from config import Config
from services.ipayment import BasicPaymentInfo
import handlers.start as start_handlers


async def _send_bill(update: Update, context: ContextTypes.DEFAULT_TYPE, basic_info: BasicPaymentInfo):
    db = Container.db()
    bank_name = db.get_bank_name(basic_info.bin)

    # Send message
    keyboard = [
        [
            InlineKeyboardButton("Hủy", callback_data=CallbackData.REFRESH), 
            InlineKeyboardButton("Xác nhận", callback_data=CallbackData.CONFIRM_DEPOSIT)
        ]
    ]
    message = (f"Hãy chuyển tiền vào:\n"
        f"Ngân hàng: {bank_name}\n"
        f"Số tài khoản: {basic_info.account_number}\n"
        f"Chủ tài khoản: {basic_info.account_name}\n"
        f"Số tiền: {basic_info.amount} {basic_info.currency}\n"
        f"Nội dung: {basic_info.description}\n"
        f"Thời gian hết hạn: {basic_info.expired_at}")
    
    qr_url = f"https://img.vietqr.io/image/{basic_info.bin}-{basic_info.account_number}-vietqr_pro.jpg?addInfo={basic_info.description}&amount={basic_info.amount}"
    await context.bot.send_photo(
        chat_id=update.effective_chat.id, 
        photo=qr_url, 
        caption=message,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


""" Called by another handler """
async def start_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Nhập số tiền cần nạp:"
    )
    return BotStates.ASK_DEPOSIT_AMOUNT


async def ask_deposit_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text and text.isnumeric():
        amount = int(text)

        # Prevent depositing below minimun amount
        if amount < Config.MINIMUM_DEPOSIT_AMOUNT:
            await context.bot.send_message(
                chat_id=update.message.chat_id, 
                text=f"Số tiền nạp tối thiểu là {Config.MINIMUM_DEPOSIT_AMOUNT} VND"
            )
            return BotStates.ASK_DEPOSIT_AMOUNT

        db = Container.db()
        payos = Container.payos()
        # Create payment link
        user = db.get_user(update.effective_user.id)
        if user.latest_payment_id != -1:
            payos.cancel_payment(user.latest_payment_id)

        new_order_id = db.get_new_order_id()
        basic_payment_info = payos.create_new_payment(new_order_id, 1, amount)
        
        # Save latest payment id of user to easy for canceling if needs
        user.latest_payment_id = new_order_id
        db.save_user(update.effective_user.id, user)
        
        # Response to user
        await _send_bill(update, context, basic_payment_info)
        return BotStates.CONFIRM_DEPOSIT

    # Fallback
    await context.bot.send_message(chat_id=update.message.chat_id, text="Không hợp lệ! Vui lòng nhập lại số tiền cần nạp: ")
    return BotStates.ASK_DEPOSIT_AMOUNT


async def confirm_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Clear buttons
    query = update.callback_query
    await query.answer()

    db = Container.db()
    payos = Container.payos()

    # Handle respectively
    if query.data == CallbackData.REFRESH:
        user = db.get_user(update.effective_user.id)
        if user.latest_payment_id != -1:
            data = payos.get_payment(user.latest_payment_id)
            if data.status == "PENDING":
                payos.cancel_payment(user.latest_payment_id)
                user.latest_payment_id = -1
                db.save_user(update.effective_user.id, user)
        await query.delete_message()
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Giao dịch đã bị hủy bỏ!"
        )
        return await start_handlers.start(update, context)
    
    elif query.data == CallbackData.CONFIRM_DEPOSIT:
        user = db.get_user(update.effective_user.id)
        data = payos.get_payment(user.latest_payment_id)

        if data.status == "PAID":
            user.latest_payment_id = -1
            user.balance += int(data.amountPaid)
            db.save_user(update.effective_user.id, user)
            await query.delete_message()
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Bạn đã nạp {data.amountPaid} VND thành công"
            )
            return await start_handlers.start(update, context)
        
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Chưa hoàn thành giao dịch, hãy thanh toán sau đó bấm Xác nhận lại!"
            )
            return BotStates.CONFIRM_DEPOSIT

    else:
        await query.delete_message()
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Lỗi không mong muốn! Hãy bắt đầu lại!"
        )
        return await start_handlers.start(update, context)
