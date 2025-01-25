from telegram.ext import *
from telegram import *
import numpy as np

from services.ipayment import BasicPaymentInfo
from services.database import Database


class CallbackDataButton:
    REFRESH="refresh"
    BUY_REQUEST="buy_request"
    DEPOSIT_REQUEST="deposit_request"
    CONFIRM_PURCHASE="confirm_purchase"
    CONFIRM_DEPOSIT="comfirm_deposit"

class MessageMethods:
    @staticmethod
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE, balance, total_available_accounts):
        keyboard = [
            [
                InlineKeyboardButton("Re-fresh", callback_data=CallbackDataButton.REFRESH), 
                InlineKeyboardButton("Mua tài khoản", callback_data=CallbackDataButton.BUY_REQUEST)
            ],
            [
                InlineKeyboardButton("Nạp tiền", callback_data=CallbackDataButton.DEPOSIT_REQUEST)
            ]
        ]
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=
                f"Chào bạn đến với shop!\n"
                f"Số dư của bạn là: <b>{balance} VNĐ</b>\n"
                f"Số tài khoản Telegram có sẵn của chúng tôi là: <b>{total_available_accounts}</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )

    @staticmethod
    async def enter_account_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Nhập số lượng account cần mua:"
        )
    
    @staticmethod
    async def confirm_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE, quantity, price_per_account):
        keyboard = [
            [
                InlineKeyboardButton("Hủy", callback_data=CallbackDataButton.REFRESH), 
                InlineKeyboardButton("Xác nhận", callback_data=CallbackDataButton.CONFIRM_PURCHASE)
            ]
        ]
        await context.bot.send_message(
            chat_id=update.message.chat_id, 
            text=f"Xác nhận là bạn muốn mua với số lượng <b>{quantity}</b> với giá <b>{price_per_account * quantity} VND</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )

    @staticmethod
    async def enter_deposit_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Nhập số tiền cần nạp:"
        )

    @staticmethod
    async def confirm_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE, basic_info: BasicPaymentInfo):
        bank_name = Database.gI().get_bank_name(basic_info.bin)
        # Send message
        keyboard = [
            [
                InlineKeyboardButton("Hủy", callback_data=CallbackDataButton.REFRESH), 
                InlineKeyboardButton("Xác nhận", callback_data=CallbackDataButton.CONFIRM_DEPOSIT)
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


