from aiogram.dispatcher.filters.state import StatesGroup, State


class CurrencyConversionState(StatesGroup):
    currency_amount = State()
    currency_from = State()
    currency_to = State()
