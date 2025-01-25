from telegram.ext import *
from telegram import *
import logging
import numpy as np
import threading
from view.message_methods import MessageMethods, CallbackDataButton
from services.payos_payment import PayOsPayment
from services.database import Database
from services.ipayment import BasicPaymentInfo
from services.local_storage import LocalStorage


class BotState:
    START=0
    ENTER_ACCOUNT_AMOUNT=1
    CONFIRM_PURCHASE=2
    ENTER_DEPOSIT_AMOUNT=3
    CONFIRM_DEPOSIT=4

class Bot:
    PRICE_PER_ACC = 20000

    def __init__(self, token: str):
        self._token = token
        self.db = Database.gI()
        self.payos = PayOsPayment()
        self._app = Application.builder().token(self._token).build()
        self._app.add_handler(ConversationHandler(
            entry_points=[CommandHandler("start", self.start)],
            states={
                BotState.START: [CallbackQueryHandler(self.handle_button_at_start_state)],
                BotState.ENTER_ACCOUNT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_account_amount_message)],
                BotState.CONFIRM_PURCHASE: [CallbackQueryHandler(self.handle_button_at_confirm_purchase_state)],
                BotState.ENTER_DEPOSIT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_deposit_amount_message)],
                BotState.CONFIRM_DEPOSIT: [CallbackQueryHandler(self.handle_button_at_confirm_deposit_state)]
            },
            fallbacks=[
                CommandHandler("start", self.start)
            ]
        ))

        # Init log
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
        self._logger = logging.getLogger(__name__)
        self._logger.info("Setting done! Running...")
        self._app.run_polling()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Cancel payment before starting
        user = self.db.get_user(update.effective_user.id)
        if user.latest_payment_id != -1:
            data = self.payos.get_payment(user.latest_payment_id)
            if data.status == "PENDING":
                self.payos.cancel_payment(user.latest_payment_id)
            elif data.status == "PAID":
                user.balance += int(data.amountPaid)
                await context.bot.send_message(
                    chat_id=update.effective_user.id,
                    text=f"Bạn đã nạp thêm số tiền {data.amountPaid} VND"
                )
            user.latest_payment_id = -1
            self.db.save_user(update.effective_user.id, user)

        # Send message
        await self.send_start_message(update, context)
        return BotState.START

    async def handle_button_at_start_state(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Clear buttons
        query = update.callback_query
        await query.edit_message_reply_markup()
        
        # Handle respectively
        if query.data == CallbackDataButton.REFRESH:
            await self.send_start_message(update, context)
            return BotState.START

        elif query.data == CallbackDataButton.BUY_REQUEST:
            await MessageMethods.enter_account_amount(update, context)
            return BotState.ENTER_ACCOUNT_AMOUNT

        elif query.data == CallbackDataButton.DEPOSIT_REQUEST:
            await self.send_enter_deposit_amount_message(update, context)
            return BotState.ENTER_DEPOSIT_AMOUNT
        
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Lỗi không mong muốn! Hãy bắt đầu lại!"
            )
            await self.send_start_message(update, context)
            return BotState.START

    async def handle_button_at_confirm_purchase_state(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.edit_message_reply_markup()

        if query.data == CallbackDataButton.REFRESH:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Đã hủy mua!"
            )
            await self.send_start_message(update, context)
            return BotState.START

        elif query.data == CallbackDataButton.CONFIRM_PURCHASE:
            quantity = context.user_data["purchase_quantity"]
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Đã mua thành công! Chuẩn bị gửi {quantity} sessions cho các account khác nhau..."
            )
            for count in range(1, quantity + 1):
                await context.bot.send_document(
                    chat_id=update.effective_chat.id,
                    document=open("local/+12172822539.session", 'rb'),
                    caption=f"Session {count}\n"
                            f"2FA: drop",
                    parse_mode="HTML"
                )
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Hoàn tất đơn hàng"
            )
            await self.send_start_message(update, context) 
            return BotState.START

        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Lỗi không mong muốn! Hãy bắt đầu lại!"
            )
            await self.send_start_message(update, context)
        return BotState.START

    async def handle_account_amount_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text
        if text and text.isnumeric():
            quantity = int(text)
            context.user_data["purchase_quantity"] = quantity
            await self.send_confirm_account_purchase_message(update, context, quantity, self.PRICE_PER_ACC)
            return BotState.CONFIRM_PURCHASE
        else:
            await context.bot.send_message(update.message.chat_id, text="Không hợp lệ! Vui lòng nhập lại số lượng: ")
            return BotState.ENTER_ACCOUNT_AMOUNT

    async def handle_deposit_amount_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text
        if text and text.isnumeric():
            amount = int(text)
            
            # Create payment link
            user = self.db.get_user(update.effective_user.id)
            if user.latest_payment_id != -1:
                self.payos.cancel_payment(user.latest_payment_id)

            new_order_id = LocalStorage.generate_new_order_id()
            basic_payment_info = self.payos.create_new_payment(new_order_id, 1, amount)
            
            # Save latest payment id of user to easy for canceling if needs
            user.latest_payment_id = new_order_id
            self.db.save_user(update.effective_user.id, user)
            
            # Response to user
            await self.send_bank_account_message(update, context, basic_payment_info)
            return BotState.CONFIRM_DEPOSIT
        else:
            await context.bot.send_message(update.message.chat_id, text="Không hợp lệ! Vui lòng nhập lại số tiền cần nạp: ")
            return BotState.ENTER_DEPOSIT_AMOUNT

    async def handle_button_at_confirm_deposit_state(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Clear buttons
        query = update.callback_query
        await query.answer()

        # Handle respectively
        if query.data == CallbackDataButton.REFRESH:
            user = self.db.get_user(update.effective_user.id)
            if user.latest_payment_id != -1:
                data = self.payos.get_payment(user.latest_payment_id)
                if data.status == "PENDING":
                    self.payos.cancel_payment(user.latest_payment_id)
                    user.latest_payment_id = -1
                    self.db.save_user(update.effective_user.id, user)
            await query.delete_message()
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Giao dịch đã bị hủy bỏ!"
            )
            await self.send_start_message(update, context)
            return BotState.START
        
        elif query.data == CallbackDataButton.CONFIRM_DEPOSIT:
            user = self.db.get_user(update.effective_user.id)
            data = self.payos.get_payment(user.latest_payment_id)

            if data.status == "PAID":
                user.latest_payment_id = -1
                user.balance += int(data.amountPaid)
                self.db.save_user(update.effective_user.id, user)
                await query.delete_message()
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"Bạn đã nạp {data.amountPaid} VND thành công"
                )
                await self.send_start_message(update, context)
                return BotState.START
            
            else:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="Chưa hoàn thành giao dịch, hãy thanh toán sau đó bấm Xác nhận lại!"
                )
                return BotState.CONFIRM_DEPOSIT
    
        else:
            await query.delete_message()
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Lỗi không mong muốn! Hãy bắt đầu lại!"
            )
            await self.send_start_message(update, context)
            return BotState.START

    async def send_start_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = self.db.get_user(update.effective_user.id)
        total_available_accounts = self.db.count_new_accounts()
        await MessageMethods.start(update, context, user.balance, total_available_accounts)

    async def send_enter_deposit_amount_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await MessageMethods.enter_deposit_amount(update, context)

    async def send_bank_account_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE, basic_payment_info: BasicPaymentInfo):
        await MessageMethods.confirm_deposit(update, context, basic_payment_info)

    async def send_enter_account_amount_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await MessageMethods.enter_account_amount(update, context)

    async def send_confirm_account_purchase_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE, quantity, price_per_acc):
        await MessageMethods.confirm_purchase(update, context, quantity, price_per_acc)

    async def error(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self._logger.error(f"Error occurred: {context.error}")
        if context:
            await context.bot.send_message(f"Oops! Something went wrong: {context.error}")

        


