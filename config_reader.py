import os

from pydantic import BaseSettings, SecretStr
from dotenv import load_dotenv
load_dotenv()

weather_key = os.getenv('WEATHER_API_KEY')


class Settings(BaseSettings):
    bot_token: SecretStr
    CURRENT_WEATHER_API_CALL = (
            'https://api.openweathermap.org/data/2.5/weather?'
            'lat={latitude}&lon={longitude}&'
            'appid=' + weather_key + '&units=metric'
    )

    class Config:
        # Имя файла, откуда будут прочитаны данные
        # (относительно текущей рабочей директории)
        env_file = '.env'
        env_file_encoding = 'utf-8'


config = Settings()
