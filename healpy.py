from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.filters import Text
from config_reader import config

import asyncio
import logging

from aiogram import Bot, Dispatcher, executor, types
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=config.bot_token.get_secret_value(), parse_mode="HTML")
dp = Dispatcher(bot)
URL = 'https://randomfox.ca/floof/'


@dp.message_handler(Command("start"))
async def cmd_start(message: types.Message):
    kb = [
        [
            types.KeyboardButton(text="Прогноз погоды"),
            types.KeyboardButton(text="Конвертация валюты"),
            types.KeyboardButton(text="Пришли лису!"),
            types.KeyboardButton(text="Создай опрос"),
        ],
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True
    )
    await message.answer("Выберите пункт меню:", reply_markup=keyboard)


@dp.message_handler(Text("Прогноз погоды"))
async def with_puree(message: types.Message):
    await message.reply("Жара!")


@dp.message_handler(Text("Конвертация валюты"))
async def with_puree(message: types.Message):
    await message.reply("В рублях или в евро?")


@dp.message_handler(Text("Пришли котика!"))
async def cats(message: types.Message):
    await bot.send_photo(message.chat.id, photo='https://yandex.ru/images/search?img_url=http%3A%2F%2Fon-desktop.com%2Fwps%2FAnimals___Cats_Red_Cat_with_open_mouth_044663_.jpg&lr=120226&pos=0&rpt=simage&source=serp&stype=image&text=rjn')


@dp.message_handler(Text("Создай опрос"))
async def without_puree(message: types.Message):
    await message.reply("Попозже!")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
