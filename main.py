from telegram.ext import *
from dotenv import load_dotenv
import os
from services.container import Container
from bot.bot import Bot



load_dotenv()
bot = Bot(token=os.getenv("TOKEN"))



