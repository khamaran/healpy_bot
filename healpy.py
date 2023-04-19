from config_reader import config

import asyncio
import logging

from aiogram import Bot, Dispatcher, executor, types
# from aiogram.filters.command import Command
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=config.bot_token.get_secret_value(), parse_mode="HTML")
dp = Dispatcher(bot)


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    """
    Этот обработчик будет вызван, когда пользователь
    нажмет кнопки `/start` or `/help`
    """
    name = message.from_user.full_name
    await message.reply("Привет, {}!\nI'm HealpyBot!\n".format(name))


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
