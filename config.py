import os
from dotenv import load_dotenv

# Load biến môi trường từ .env
load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")  # Token của bot Telegram
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/db_name")  # DB URL
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")  # Redis Cache
    PAYMENT_API_KEY = os.getenv("PAYMENT_API_KEY")  # API key của hệ thống thanh toán
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # URL webhook nếu dùng chế độ webhook
    ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))  # ID admin
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"  # Debug mode (True/False)
    PRICE_PER_ACC = 2000
    MINIMUM_DEPOSIT_AMOUNT = 20000

    TELEGRAM_ADMIN_PASSWORD = "123"

    BIN_CODE = 970422
    BANK_ACCOUNT_NUMBER = "0905770857"
    BANK_ACCOUNT_NAME = "NGUYEN DANG KHOA"