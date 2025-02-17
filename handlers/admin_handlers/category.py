from telegram.ext import *
from telegram import *
from config import Config
from services.container import Container
from bot.state_manager import StateManager
from database.models.category import Category
from bot.callback_data_manager import CallbackDataManager
from bot.mode import Mode
import json
import os
from io import BytesIO



def set_add_category_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mode"] = Mode.ADMIN_ADD_CATEGORY

def is_add_category_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    return context.user_data["mode"] == Mode.ADMIN_ADD_CATEGORY



async def start_add_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Run only in private chat
    if update.effective_chat.type != 'private':
        await update.message.reply_text("❌ Hãy chat lệnh này riêng, không chat ở đây")
        return ConversationHandler.END 
    
    # Check if user enter the password
    args = context.args 
    if not args or len(args) != 1:
        await update.message.reply_text("❌ Bạn chưa nhập mật khẩu! Vui lòng nhập: `/admin_add_category <password>`")
        return ConversationHandler.END

    # Check password
    password = args[0]
    if password == Config.TELEGRAM_ADMIN_PASSWORD:
        set_add_category_mode(update, context)

        category = Category(name="...", price=123456789, adding_instruction="...", avai_products=0, sold_products=0)
        json_data = json.dumps({key: value for key, value in category.__dict__.items() if key not in ["id", "avai_products", "sold_products", "next_product_id"]}, indent=4)
        json_file = BytesIO(json_data.encode())
        json_file.name = "category.json"

        await update.message.reply_document(
            document=json_file,
            caption="Hãy tải file này về điền các giá trị tương ứng rồi quay lại gửi cho tôi. Bây giờ tôi sẽ chờ bạn gửi lại... \n\n\n Bấm /admin_stop_add_category",
            parse_mode="HTML"
        )
        return StateManager.GET_CATEGORY_FILE
    else:
        await update.message.reply_text("❌ Sai mật khẩu!")
    return ConversationHandler.END


async def get_category_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_add_category_mode(update, context):
        return ConversationHandler.END

    file = update.message.document
    file_name = file.file_name
    if file.mime_type == "application/json":
        file_path = f"temp/{file_name}"

        try:
            # Download creating category file
            telegram_file = await file.get_file()
            await telegram_file.download_to_drive(custom_path=file_path)  

            # Read and parse JSON file
            with open(file_path, "r", encoding="utf-8") as f:
                json_data = json.load(f)

            category = Category(
                id=Container.category_manager().generate_category_id(),
                name=json_data["name"],
                price=json_data["price"],
                adding_instruction=json_data["adding_instruction"],
                avai_products=0,
                sold_products=0,
                next_product_id=0
            )

            # Save it into database
            Container.category_manager().save_category(category_id=category.id, category=category)

            await update.message.reply_text("Tạo xong! Bấm /start để check.")

            return ConversationHandler.END
        except json.JSONDecodeError:
            update.message.reply_text("Error: The file contains invalid JSON. Please check and try again.")
        finally:
            # Cleanup: Delete the file after processing
            if os.path.exists(file_path):
                os.remove(file_path)
                
    else:
        update.message.reply_text("Please send a valid JSON file.")
    return StateManager.GET_CATEGORY_FILE


async def stop_add_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("OK! Tôi đã hủy nhận file.")
    return ConversationHandler.END


add_category_conversation_handler = ConversationHandler(
    entry_points=[
        CommandHandler("admin_add_category", start_add_category)                
    ],
    states={
        StateManager.GET_CATEGORY_FILE: [MessageHandler(filters.ATTACHMENT, get_category_file)],
    },
    fallbacks=[
        CommandHandler("admin_stop_add_category", stop_add_category)
    ]
)