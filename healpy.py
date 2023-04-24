import os
import asyncio
import logging
import requests
from aiogram.dispatcher import FSMContext

from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.filters import Text
from aiogram.utils import deep_linking

from config_reader import config
from aiogram import Bot, Dispatcher, types
from dotenv import load_dotenv
from currency import CurrencyConversionState
from polls import PollState
from weather_api_service import get_weather
from aiogram.contrib.fsm_storage.memory import MemoryStorage

load_dotenv()
conversion_key = os.getenv('CURRENCY_API_KEY')

polls_database = {}
polls_owners = {}

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
PROXY_URL = 'http://proxy.server:3128'
bot = Bot(token=config.bot_token.get_secret_value(), parse_mode="HTML", proxy=PROXY_URL)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
FOX_URL = 'https://randomfox.ca/floof/'
CURRENCY_URL = "https://api.apilayer.com/exchangerates_data/convert?"

def get_main_keyboard():
    kb = [
        [
            types.KeyboardButton(text="Прогноз погоды"
                                 ),
            types.KeyboardButton(text="Конвертация валюты"),
            types.KeyboardButton(text="Пришли лису!"),
            types.KeyboardButton(text="Создать опрос"),
        ],
    ]
    return types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True
    )


@dp.message_handler(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Выбери пункт меню:", reply_markup=get_main_keyboard())


def get_new_image():
    """ Получить новую картинку лисы (или котика,
    если что-то не так с API с лисами)."""
    try:
        response = requests.get(FOX_URL)
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


def weather(latitude, longitude):
    """Возвращает сообщение о температуре погоды."""
    wthr = get_weather(latitude, longitude)
    return f'{wthr.location}, {wthr.description}\n' \
           f'Temperature is {wthr.temperature}°C, feels like {wthr.temperature_feeling}°C'


def get_location_keyboard():
    keyboard = types.ReplyKeyboardMarkup()
    button = types.KeyboardButton("Поделиться локацией", request_location=True)
    keyboard.add(button)
    return keyboard


@dp.message_handler(content_types=['location'])
async def handle_location(message: types.Message):
    lat = message.location.latitude
    lon = message.location.longitude
    reply = weather(lat, lon)
    await message.answer(reply, reply_markup=get_main_keyboard())


@dp.message_handler(Text("Прогноз погоды"))
async def cmd_locate_me(message: types.Message):
    reply = "Нажмите на кнопку внизу, чтобы поделиться своей локацией!"
    await message.answer(reply, reply_markup=get_location_keyboard())


def conversion(currency_amount, currency_from, currency_to):
    """Возвращает сообщение с конвертацией валюты."""
    payload = {}
    headers = {
        "apikey": conversion_key
    }
    params = 'to=' + currency_to + '&from=' + currency_from + '&amount=' + currency_amount
    response = requests.request("GET", CURRENCY_URL + params, headers=headers, data=payload)
    response = response.json()
    result = response.get('result')
    return result


@dp.message_handler(Text('Конвертация валюты'))
async def currency(message: types.Message):
    await message.answer('Введите сумму:')
    await CurrencyConversionState.currency_amount.set()


@dp.message_handler(state=CurrencyConversionState.currency_amount)
async def get_currency_amount(message: types.Message, state: FSMContext):
    await state.update_data(currency_amount=message.text)
    await message.answer('Отлично! Теперь введите код конвертируемой валюты:')
    await CurrencyConversionState.currency_from.set()


@dp.message_handler(state=CurrencyConversionState.currency_from)
async def get_currency_from(message: types.Message, state: FSMContext):
    await state.update_data(currency_from=message.text)
    await message.answer('Отлично! Теперь введите код валюты, в которую конвертируем:')
    await CurrencyConversionState.currency_to.set()


@dp.message_handler(state=CurrencyConversionState.currency_to)
async def get_currency_amount(message: types.Message, state: FSMContext):
    await state.update_data(currency_to=message.text)
    data = await state.get_data()
    await message.answer('Подождите! Идёт расчёт!')
    await message.answer(conversion(data['currency_amount'], data['currency_from'], data['currency_to']))
    await state.finish()


@dp.message_handler(Text("Создать опрос"))
async def poll(message: types.Message):
    if message.chat.type == types.ChatType.PRIVATE:
        poll_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        poll_keyboard.add(types.KeyboardButton(text="Вперёд!",
                                               request_poll=types.KeyboardButtonPollType(type=types.PollType.REGULAR)))
        poll_keyboard.add(types.KeyboardButton(text="Отмена"))
        await message.answer("Нажмите на кнопку ниже и создайте опрос! "
                             "Внимание: в дальнейшем он будет публичным (неанонимным).", reply_markup=poll_keyboard)
    else:
        words = message.text.split()
        # Только команда /start без параметров. В этом случае отправляем в личку с ботом.
        if len(words) == 1:
            bot_info = await bot.get_me()  # Получаем информацию о нашем боте
            keyboard = types.InlineKeyboardMarkup()  # Создаём клавиатуру с URL-кнопкой для перехода в ЛС
            move_to_dm_button = types.InlineKeyboardButton(text="Перейти в ЛС",
                                                           url=f"t.me/{bot_info.username}?start=anything")
            keyboard.add(move_to_dm_button)
            await message.reply("Не выбран ни один опрос. Пожалуйста, перейдите в личные сообщения с ботом, "
                                "чтобы создать новый.", reply_markup=keyboard)
        # Если у команды /start или /startgroup есть параметр, то это, скорее всего, ID опроса.
        # Проверяем и отправляем.
        else:
            poll_owner = polls_owners.get(words[1])
            if not poll_owner:
                await message.reply(
                    "Опрос удалён, недействителен или уже запущен в другой группе. Попробуйте создать новый.")
                return
            for saved_poll in polls_database[
                poll_owner
            ]:  # Проходим по всем сохранённым викторинам от конкретного user ID
                if saved_poll.poll_id == words[1]:  # Нашли нужную викторину, отправляем её.
                    msg = await bot.send_poll(chat_id=message.chat.id, question=saved_poll.question,
                                              is_anonymous=False, options=saved_poll.options, type="poll",
                                              correct_option_id=saved_poll.correct_option_id)
                    polls_owners[msg.poll.id] = poll_owner  # ID викторины при отправке уже другой, создаём запись.
                    del polls_owners[words[1]]  # Старую запись удаляем.
                    saved_poll.poll_id = msg.poll.id  # В "хранилище" викторин тоже меняем ID викторины на новый
                    saved_poll.chat_id = msg.chat.id  # ... а также сохраняем chat_id ...
                    saved_poll.message_id = msg.message_id  # ... и message_id для последующего закрытия викторины.


@dp.message_handler(lambda message: message.text == "Отмена")
async def action_cancel(message: types.Message):
    await message.answer('Действие отменено.', reply_markup=get_main_keyboard())


@dp.message_handler(content_types=["poll"])
async def polls(message: types.Message):
    # Если юзер раньше не присылал запросы, выделяем под него запись
    if not polls_database.get(str(message.from_user.id)):
        polls_database[str(message.from_user.id)] = []

    # Если юзер решил вручную отправить не опрос, а викторину, откажем ему.
    if message.poll.type != "regular":
        await message.reply("Извините, я принимаю только опросы (regular)!")
        return

    # Сохраняем себе опрос в память
    polls_database[str(message.from_user.id)].append(PollState(
        poll_id=message.poll.id,
        question=message.poll.question,
        options=[o.text for o in message.poll.options],
        owner_id=message.from_user.id)
    )
    # Сохраняем информацию о его владельце для быстрого поиска в дальнейшем
    polls_owners[message.poll.id] = str(message.from_user.id)

    await message.reply(
        f"Опрос сохранен. Общее число сохранённых опросов: {len(polls_database[str(message.from_user.id)])}")


@dp.inline_handler()  # Обработчик любых инлайн-запросов
async def inline_query(query: types.InlineQuery):
    results = []
    user_polls = polls_database.get(str(query.from_user.id))
    if user_polls:
        for poll in user_polls:
            keyboard = types.InlineKeyboardMarkup()
            start_poll_button = types.InlineKeyboardButton(
                text="Отправить в группу",
                url=await deep_linking.get_startgroup_link(poll.poll_id)
            )
            keyboard.add(start_poll_button)
            results.append(types.InlineQueryResultArticle(
                id=poll.poll_id,
                title=poll.question,
                input_message_content=types.InputTextMessageContent(
                    message_text="Нажмите кнопку ниже, чтобы отправить опрос в группу."),
                reply_markup=keyboard
            ))
    await query.answer(switch_pm_text="Создать опрос", switch_pm_parameter="_",
                       results=results, cache_time=120, is_personal=True)


@dp.poll_answer_handler()
async def handle_poll_answer(poll_answer: types.PollAnswer):
    """
    Это хендлер на новые ответы в опросах (Poll) и викторинах (Quiz)
    Реагирует на изменение голоса. В случае отзыва голоса тоже срабатывает!
    Чтобы не было путаницы:
    * poll_answer - ответ на активный опрос
    * saved_poll - опрос, находящийся в нашем "хранилище" в памяти
    :param poll_answer: объект PollAnswer с информацией о голосующем
    """
    poll_owner = polls_owners.get(poll_answer.poll_id)
    if not poll_owner:
        logging.error(f"Не могу найти автора опроса с poll_answer.poll_id = {poll_answer.poll_id}")
        return


@dp.poll_handler(lambda active_poll: active_poll.is_closed is True)
async def just_poll_answer(active_poll: types.Poll):
    """
    Реагирует на закрытие опроса/викторины. Если убрать проверку на poll.is_closed == True,
    то этот хэндлер будет срабатывать при каждом взаимодействии с опросом/викториной, наравне
    с poll_answer_handler
    Чтобы не было путаницы:
    * active_poll - викторина, в которой кто-то выбрал ответ
    * saved_poll - викторина, находящаяся в нашем "хранилище" в памяти
    Этот хэндлер частично повторяет тот, что выше, в части, касающейся поиска нужного опроса в нашем "хранилище".
    :param active_poll: Объект Poll.
    """
    poll_owner = polls_owners.get(active_poll.id)
    if not poll_owner:
        logging.error(f"Не могу найти автора опроса с active_poll.id = {active_poll.id}")
        return
    for num, saved_poll in enumerate(polls_database[poll_owner]):
        if saved_poll.poll_id == active_poll.id:
            await bot.send_message(saved_poll.chat_id, "Опрос закончен, всем спасибо!", parse_mode="HTML")
            # Удаляем викторину из обоих наших "хранилищ"
            del polls_owners[active_poll.id]
            del polls_database[poll_owner][num]


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
