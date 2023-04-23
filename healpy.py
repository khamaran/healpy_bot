import os
import asyncio
import logging
import requests
from aiogram.dispatcher import FSMContext

from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.filters import Text
from config_reader import config
from aiogram import Bot, Dispatcher, executor, types
from dotenv import load_dotenv
from coordinates import get_coordinates
from currency import CurrencyConversionState
from weather_api_service import get_weather
from aiogram.contrib.fsm_storage.memory import MemoryStorage

load_dotenv()
conversion_key = os.getenv('CURRENCY_API_KEY')

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=config.bot_token.get_secret_value(), parse_mode="HTML")
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
URL_1 = 'https://randomfox.ca/floof/'
URL_2 = "https://api.apilayer.com/exchangerates_data/convert?"


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


@dp.message_handler(Text("Пришли лису!"))
async def fox(message: types.Message):
    await bot.send_photo(message.chat.id, get_new_image())


def weather():
    """Возвращает сообщение о температуре погоды."""
    wthr = get_weather(get_coordinates())
    return f'{wthr.location}, {wthr.description}\n' \
           f'Temperature is {wthr.temperature}°C, feels like {wthr.temperature_feeling}°C'


@dp.message_handler(Text("Прогноз погоды"))
async def show_weather(message: types.Message):
    await message.answer(text=weather())


def conversion(currency_amount, currency_from, currency_to):
    """Возвращает сообщение с конвертацией валюты."""
    payload = {}
    headers = {
        "apikey": conversion_key
    }
    params = 'to=' + currency_to + '&from=' + currency_from + '&amount=' + currency_amount
    response = requests.request("GET", URL_2 + params, headers=headers, data=payload)
    response = response.json()
    result = response.get('result')
    return result


@dp.message_handler(Text('Конвертация валюты'))
async def currency(message: types.Message):
    await message.answer('Введите сумму:')
    await CurrencyConversionState.currency_amount.set()


@dp.message_handler(state=CurrencyConversionState.currency_amount)
async def get_сurrency_amount(message: types.Message, state: FSMContext):
    await state.update_data(currency_amount=message.text)
    await message.answer('Отлично! Теперь введите код конвертируемой валюты:')
    await CurrencyConversionState.currency_from.set()


@dp.message_handler(state=CurrencyConversionState.currency_from)
async def get_сurrency_from(message: types.Message, state: FSMContext):
    await state.update_data(currency_from=message.text)
    await message.answer('Отлично! Теперь введите код валюты, в которую конвертируем:')
    await CurrencyConversionState.currency_to.set()


@dp.message_handler(state=CurrencyConversionState.currency_to)
async def get_сurrency_amount(message: types.Message, state: FSMContext):
    await state.update_data(currency_to=message.text)
    data = await state.get_data()
    await message.answer('Подождите! Идёт расчёт!')
    await message.answer(conversion(data['currency_amount'], data['currency_from'], data['currency_to']))
    await state.finish()


@dp.message_handler(Text("Создай опрос"))
async def poll(message: types.Message):
    await message.reply("Попозже!")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
