from telegram.ext import *
from telegram import *
import logging
from services.container import Container
import handlers.start as start_handlers
import handlers.purchase as purchase_handlers
import handlers.deposit as deposit_handlers
from handlers.admin.category import add_category_conversation_handler
from handlers.admin.product import cancel_posting_query_handler, accept_posting_query_handler, add_product_conversation_handler, delete_product_query_handler
import handlers.admin.delete_category as delete_category_handlers
import handlers.admin.storage as storage_handlers
from bot.state_manager import StateManager
from bot.callback_data_manager import CallbackDataManager
from bank.mb import check_transaction_history
import threading


class Bot:
    def __init__(self, token: str):
        self._token = token
        self.db = Container.db()
        self._app = Application.builder().token(self._token).build()

        """ Initialize logger """
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
        self._logger = logging.getLogger(__name__)
        self._logger.info("Setting done! Running...")

        """ Setting up handlers """
        """ Command start """
        self._app.add_handler(CommandHandler("start", start_handlers.start))
        
        """ Refresh feature """
        self._app.add_handler(CallbackQueryHandler(start_handlers.start, pattern=f"^({CallbackDataManager.REFRESH})$"))

        """ Purchasing feature """
        self._app.add_handler(ConversationHandler(
            entry_points=[
                CallbackQueryHandler(purchase_handlers.start_purchase, pattern=f"^{CallbackDataManager.PURCHASE_FEATURE}$"),
            ],
            states={
                StateManager.CHOOSE_PURCHASE_CATEGORY: [CallbackQueryHandler(purchase_handlers.choose_category)],
                StateManager.CHOOSE_PURCHASE_QUANTITY: [CallbackQueryHandler(purchase_handlers.choose_quantity)],
                StateManager.CONFIRM_PURCHASE: [CallbackQueryHandler(purchase_handlers.confirm_purchase)],
            },
            fallbacks=[
                
            ],
            per_message=True
        ))
        

        """ Deposit feature """
        self._app.add_handler(CallbackQueryHandler(deposit_handlers.start_deposit, pattern=f"^{CallbackDataManager.DEPOSIT_FEATURE}$"))
        self._app.add_handler(CallbackQueryHandler(deposit_handlers.turn_back_start, pattern=f"^{CallbackDataManager.TURN_BACK_START_FROM_DEPOSIT}$"))


        """ Admin handlers """
        # Set storage handler
        self._app.add_handler(CommandHandler("admin_set_storage", storage_handlers.set_storage))
        # Conversation handler for adding product
        self._app.add_handlers([
            add_product_conversation_handler, accept_posting_query_handler, cancel_posting_query_handler, delete_product_query_handler
        ])
        # Conversation handler for adding category
        self._app.add_handler(add_category_conversation_handler)

        """ ADMIN DELETE CATEGORY HANDLERS """
        self._app.add_handlers(delete_category_handlers.handlers)

        self.run_thread_checking_transation_history()
        self._app.run_polling()
    
    def run_thread_checking_transation_history(self):
        thread = threading.Thread(target=check_transaction_history)
        thread.daemon = True
        thread.start()

    async def error(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self._logger.error(f"Error occurred: {context.error}")
        if context:
            await context.bot.send_message(f"Oops! Something went wrong: {context.error}")


