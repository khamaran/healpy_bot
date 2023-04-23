import asyncio
import logging
import requests

from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.filters import Text
from config_reader import config
from aiogram import Bot, Dispatcher, executor, types
from dotenv import load_dotenv
from coordinates import get_coordinates
from weather_api_service import get_weather

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=config.bot_token.get_secret_value(), parse_mode="HTML")
dp = Dispatcher(bot)
URL_1 = 'https://randomfox.ca/floof/'


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


def get_new_image():
    try:
        response = requests.get(URL_1)
    except Exception as error:
        logging.error(f'Ошибка при запросе к основному API: {error}')
        new_url = 'https://api.thecatapi.com/v1/images/search'
        response = requests.get(new_url)
        response = response.json()
        random_cat = response[0].get('url')
        return random_cat
    response = response.json()
    random_fox = response.get('image')
    return random_fox


def weather():
    """Возвращает сообщение о температуре погоды."""
    wthr = get_weather(get_coordinates())
    return f'{wthr.location}, {wthr.description}\n' \
           f'Temperature is {wthr.temperature}°C, feels like {wthr.temperature_feeling}°C'


@dp.message_handler(Text("Прогноз погоды"))
async def show_weather(message: types.Message):
    await message.answer(text=weather())


@dp.message_handler(Text("Конвертация валюты"))
async def currency(message: types.Message):
    await message.reply("В рублях или в евро?")


@dp.message_handler(Text("Пришли лису!"))
async def fox(message: types.Message):
    await bot.send_photo(message.chat.id, get_new_image())


@dp.message_handler(Text("Создай опрос"))
async def poll(message: types.Message):
    await message.reply("Попозже!")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
