from telegram.ext import *
from telegram import *
from services.container import Container
import handlers.start as start_handlers
from exceptions.product_exceptions import NotEnoughProductsError
from bot.state_manager import StateManager
from bot.callback_data_manager import CallbackDataManager
from typing import List
from database.models.product import Product


""" Partially auditted """
async def start_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    # Category for all services and products
    categories = Container.category_manager().get_categories()
    keyboard = [[InlineKeyboardButton(category.name, callback_data=category.id)] for category in categories]
    keyboard.append([InlineKeyboardButton("Quay lại", callback_data=CallbackDataManager.TURN_BACK_START_FROM_PURCHASE)])

    await query.edit_message_text(
        text="Vô mua hàng đi cu em",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    return StateManager.CHOOSE_PURCHASE_CATEGORY


""" Partially auditted """
async def choose_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == CallbackDataManager.TURN_BACK_START_FROM_PURCHASE:
        await start_handlers.start(update, context)
        return ConversationHandler.END

    # Save category_id except the state turn back from choosing quantity state
    if query.data != CallbackDataManager.RELOAD_QUANTITY_STATE and query.data != CallbackDataManager.TURN_BACK_QUANTITY_FROM_CONFIRM:
        context.user_data["purchase_category"] = query.data

    # Setup keyboard to select quantity
    keyboard = [
        [
            InlineKeyboardButton(text="1", callback_data="1"), 
            InlineKeyboardButton(text="2", callback_data="2"), 
            InlineKeyboardButton(text="5", callback_data="5"), 
            InlineKeyboardButton(text="10", callback_data="10")
        ]
    ]
    keyboard.append([InlineKeyboardButton("Quay lại", callback_data=CallbackDataManager.TURN_BACK_CATEGORY_FROM_QUANTITY)])

    await query.edit_message_text(
        text=f"Đã chọn {query.data}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
    )
    return StateManager.CHOOSE_PURCHASE_QUANTITY


""" Partially auditted """
async def choose_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == CallbackDataManager.TURN_BACK_CATEGORY_FROM_QUANTITY:
        return await start_purchase(update, context)        
    elif query.data == CallbackDataManager.RELOAD_QUANTITY_STATE:
        return await choose_category(update, context)

    user_manager = Container.user_manager()
    category_manager = Container.category_manager()
    product_manager = Container.product_manager()

    user = user_manager.get_user(update.effective_user.id)

    category_id = context.user_data["purchase_category"]
    category = category_manager.get_category(category_id)
    
    quantity = int(query.data)
    context.user_data["purchase_quantity"] = quantity
    
    total_price = quantity * category.price
    
    if quantity > category.avai_products:
        keyboard = [[InlineKeyboardButton("Quay lại", callback_data=CallbackDataManager.RELOAD_QUANTITY_STATE)]]
        await query.edit_message_text(text="Tôi không đủ số lượng để bán!", reply_markup=InlineKeyboardMarkup(keyboard))
        return StateManager.CHOOSE_PURCHASE_QUANTITY
    elif total_price > user.balance:
        keyboard = [[InlineKeyboardButton("Quay lại", callback_data=CallbackDataManager.RELOAD_QUANTITY_STATE)]]
        await query.edit_message_text(text="Số tiền của bạn không đủ để mua!", reply_markup=InlineKeyboardMarkup(keyboard))
        return StateManager.CHOOSE_PURCHASE_QUANTITY

    # Setup keyboard to confirm purchase
    keyboard = [
        [
            InlineKeyboardButton(text="Quay lại", callback_data=CallbackDataManager.TURN_BACK_QUANTITY_FROM_CONFIRM), 
            InlineKeyboardButton(text=f"Xác nhận trả {total_price} VNĐ", callback_data=CallbackDataManager.CONFIRM_PAY_PURCHASE), 
        ]
    ]
    await query.edit_message_text(
        text=f"Đã chọn {query.data}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
    )
    return StateManager.CONFIRM_PURCHASE


""" Partially auditted """
async def confirm_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == CallbackDataManager.TURN_BACK_QUANTITY_FROM_CONFIRM:
        return await choose_category(update, context)
    
    user_manager = Container.user_manager()
    category_manager = Container.category_manager()
    product_manager = Container.product_manager()

    category_id = context.user_data["purchase_category"]
    quantity = context.user_data["purchase_quantity"]
    category = category_manager.get_category(category_id)
    total_price = quantity * category.price

    user = user_manager.get_user(update.effective_user.id)

    if quantity > category.avai_products:
        keyboard = [[InlineKeyboardButton("Quay lại", callback_data=CallbackDataManager.RELOAD_QUANTITY_STATE)]]
        await query.edit_message_text(text="Tôi không đủ số lượng để bán!", reply_markup=InlineKeyboardMarkup(keyboard))
        return StateManager.CHOOSE_PURCHASE_QUANTITY
    elif total_price > user.balance:
        keyboard = [[InlineKeyboardButton("Quay lại", callback_data=CallbackDataManager.RELOAD_QUANTITY_STATE)]]
        await query.edit_message_text(text="Số tiền của bạn không đủ để mua!", reply_markup=InlineKeyboardMarkup(keyboard))
        return StateManager.CHOOSE_PURCHASE_QUANTITY



    await query.delete_message()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Xác nhận mua thành công! Chuẩn bị gửi sản phẩm...",
        parse_mode="HTML"
    )
    try:
        await _send_product(update, context, category_id, quantity, total_price)

        keyboard = [[InlineKeyboardButton("Bắt đầu lại", callback_data=CallbackDataManager.REFRESH)]]
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Cảm ơn bạn đã tin tưởng nha!\n\nBấm /start để bắt đầu lại và cũng như lấy hướng dẫn sử dụng ạ.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
    except NotEnoughProductsError as e:
        print(e)
        keyboard = [[InlineKeyboardButton("Bắt đầu lại", callback_data=CallbackDataManager.REFRESH)]]
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Số lượng bất ngờ không đủ. Vui lòng bắt đầu lái",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
    return ConversationHandler.END


""" Partially auditted """
async def _send_product(update: Update, context: ContextTypes.DEFAULT_TYPE, category_id: str, quantity: int, total_price: int):
    user_manager = Container.user_manager()
    category_manager = Container.category_manager()
    product_manager = Container.product_manager()

    transactions = []
    transactions.append(product_manager.buy_products_transaction(category_id=category_id, user_id=update.effective_user.id, limit=quantity))
    transactions.append(user_manager.add_balance_transaction(update.effective_user.id, -total_price))
    products, _ = await Container.db().exec_transactions(transactions)
    products: List[Product]

    for index, product in enumerate(products):
        category_manager.transfer_avai_to_sold(category_id, update.effective_user.id, product.id)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Sản phẩm {index}"
        )
        await context.bot.forward_message(
            chat_id=update.effective_chat.id,
            from_chat_id=product.backup_storage_group_id,
            message_id=product.backup_message_id
        )


