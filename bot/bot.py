from telegram.ext import *
from telegram import *
import logging
import numpy as np
import asyncio
from services.payos_payment import PayOsPayment
from services.database import Database
from services.cloud_storage import CloudStorage
from services.container import Container
from models.product import Product
from states.bot_states import BotStates
import handlers.start as start_handlers
import handlers.purchase as purchase_handlers
import handlers.deposit as deposit_handlers
import handlers.admin as admin_handlers
from config import Config


class Bot:
    TEMP_DIR = "temp"
    PRICE_PER_ACC = 0

    def __init__(self, token: str):
        self._token = token
        self.db = Container.db()
        self.storage = CloudStorage()
        self.payos = PayOsPayment()
        self.lock = asyncio.Lock() 
        self._app = Application.builder().token(self._token).build()
        self._app.add_handler(ConversationHandler(
            entry_points=[
                CommandHandler("start", start_handlers.start),

                CommandHandler("set_storage", admin_handlers.set_storage),
                CommandHandler("add", admin_handlers.start_add_files),
            ],
            states={
                BotStates.START: [CallbackQueryHandler(start_handlers.choose_service)],
                BotStates.ASK_PURCHASE_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, purchase_handlers.ask_purchase_amount)],
                BotStates.CONFIRM_PURCHASE: [CallbackQueryHandler(purchase_handlers.confirm_purchase)],
                BotStates.ASK_DEPOSIT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, deposit_handlers.ask_deposit_amount)],
                BotStates.CONFIRM_DEPOSIT: [CallbackQueryHandler(deposit_handlers.confirm_deposit)],

                #Admin States
                BotStates.SELECT_CATEGORY: [CallbackQueryHandler(admin_handlers.select_category)],
                BotStates.RECEIVE_FILES: [MessageHandler(filters.ATTACHMENT, admin_handlers.receive_files), CommandHandler("stop", admin_handlers.stop_receive_files)]
            },
            fallbacks=[
                CommandHandler("start", start_handlers.start), 
                CommandHandler("set_storage", admin_handlers.set_storage),
                CommandHandler("add", admin_handlers.start_add_files),
            ]
        ))

        # Init log
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
        self._logger = logging.getLogger(__name__)
        self._logger.info("Setting done! Running...")
        self._app.run_polling()

    async def send_tdata(self, update: Update, context: ContextTypes.DEFAULT_TYPE, amount_of_accounts: int):
        # amount_of_accounts always greater than 0 and <= 100
        accounts = self.storage.read_new_accounts(limit=amount_of_accounts)
        print(accounts)
        index = 1
        message = ""
        for account in accounts:
            link=self.storage.get_download_link(account["id"])
            message += f"Account {index} |SDT: {account['name']} |Link: {link}\n"
            index += 1

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=message,
            parse_mode="HTML"
        )

    async def error(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self._logger.error(f"Error occurred: {context.error}")
        if context:
            await context.bot.send_message(f"Oops! Something went wrong: {context.error}")


