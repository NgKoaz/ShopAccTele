from telegram.ext import *
from dotenv import load_dotenv
import os
from bot.bot import Bot
import asyncio
from services.database import Database



load_dotenv()
bot = Bot(token=os.getenv("TOKEN"))


asyncio.run(Database().get_setting())



