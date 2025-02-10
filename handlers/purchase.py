from telegram.ext import *
from telegram import *
from states.bot_states import BotStates
from callback_data.callback_data import CallbackData
from callback_data.callback_data import CallbackData
from services.container import Container

import asyncio
import handlers.start as start_handlers
from config import Config


lock = asyncio.Lock() 

async def _send_confirm_purchase_message(update: Update, context: ContextTypes.DEFAULT_TYPE, quantity, price_per_account):
    # Setup keyboard
    keyboard = [
        [
            InlineKeyboardButton("Hủy", callback_data=CallbackData.REFRESH), 
            InlineKeyboardButton("Xác nhận", callback_data=CallbackData.CONFIRM_PURCHASE)
        ]
    ]
    await context.bot.send_message(
        chat_id=update.message.chat_id, 
        text=f"Xác nhận là bạn muốn mua với số lượng <b>{quantity}</b> với giá <b>{price_per_account * quantity} VND</b>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )


""" Called by another handler """
async def start_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Nhập số lượng account cần mua (hoặc nhập số 0 để thoát):"
    )
    return BotStates.ASK_PURCHASE_AMOUNT


""" Handler for ConversationHandler """
async def ask_purchase_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text and text.isnumeric():
        quantity = int(text)

        if quantity == 0:
            return await start_handlers.start(update, context)
        
        if quantity > 100:
            await context.bot.send_message(update.message.chat_id, text="Số lượng mua chỉ tối đa là 100/lượt!")
            return BotStates.ASK_PURCHASE_AMOUNT

        db = Container.db()
        num_avai_account = db.count_new_accounts()
        if quantity > num_avai_account:
            await context.bot.send_message(update.message.chat_id, text=f"Số lượng mua vượt quá số lượng có sẵn là {num_avai_account}!")
            return BotStates.ASK_PURCHASE_AMOUNT

        # Go to a next state of purchase process
        context.user_data["purchase_quantity"] = quantity
        await _send_confirm_purchase_message(update, context, quantity, price_per_account=Config.PRICE_PER_ACC)
        return BotStates.CONFIRM_PURCHASE
    else:
        await context.bot.send_message(update.message.chat_id, text="Không hợp lệ! Vui lòng nhập lại số lượng: ")
        return BotStates.ASK_PURCHASE_AMOUNT


async def confirm_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Clear buttons
    query = update.callback_query
    await query.edit_message_reply_markup()

    # Handle cancel button
    if query.data == CallbackData.REFRESH:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Đã hủy mua!"
        )
        return await start_handlers.start()

    # Handle confirm button
    elif query.data == CallbackData.CONFIRM_PURCHASE:
        async with lock: 
            quantity = context.user_data["purchase_quantity"]

            db = Container.db()
            # Check quantity with database
            if quantity > db.count_new_accounts():
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"Quá số lượng account hiện có!"
                )
                return await start_handlers.start(update, context)
            
            # Check amount of user's money
            user = db.get_user(update.effective_user.id)
            total_price = quantity * Config.PRICE_PER_ACC
            if total_price > user.balance:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"Số tiền hiện tại không đủ để thanh toán"
                )
                return await start_handlers.start(update, context)

            # Validated data
            ## Deduct user's balance
            user.balance -= total_price
            db.save_user(update.effective_user.id, user)

            ## Send acknownledge
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Đã mua thành công! Chuẩn bị gửi {quantity} tdata cho các account khác nhau..."
            )
            ## Send purchased sessions
            # await self.send_tdata(update, context, quantity)
            ## Send acknowledge ending sending sessions
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Hoàn tất đơn hàng"
            )

            # Go back to initial state
            return await start_handlers.start(update, context)

    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Lỗi không mong muốn! Hãy bắt đầu lại!"
        )
        return await start_handlers.start(update, context)

