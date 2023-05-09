import requests
import os
import json
import time
import logging

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils.exceptions import NetworkError
from aiohttp.client_exceptions import ClientConnectorError
from requests.exceptions import ConnectionError, ReadTimeout
from dotenv import load_dotenv


load_dotenv()
devman_token = os.environ.get('DEVMAN_TOKEN')
bot = Bot(token=os.environ.get('BOT_TOKEN'))
user_id = os.environ.get('USER_ID')
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
logging.basicConfig(level=logging.INFO)


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.answer('Стартую. Направляю запрос Devmanу.')
    url = 'https://dvmn.org/api/long_polling/'
    headers = {'Authorization': f'Token {devman_token}'}
    timeout = 100
    payload = {'timestamp': None}
    while True:
        try:
            response = requests.get(url, headers=headers, params=payload, timeout=timeout)
            response.raise_for_status()
            logging.info(response.url)
            devman_response_in_format = response.json()
            logging.info(json.dumps(devman_response_in_format, indent=2, ensure_ascii=False))
            if devman_response_in_format['status'] == 'timeout':
                payload['timestamp'] = devman_response_in_format['timestamp_to_request']
                await message.answer('Нет обновлений.')
            elif devman_response_in_format['status'] == 'found':
                payload['timestamp'] = devman_response_in_format['last_attempt_timestamp']
                reply_message = f'Преподаватель проверил работу "{devman_response_in_format["new_attempts"][0]["lesson_title"]}"!\n' \
                                f'{devman_response_in_format["new_attempts"][0]["lesson_url"]}\n'
                if devman_response_in_format["new_attempts"][0]["is_negative"]:
                    reply_message = f'{reply_message} К сожалению в работе нашлись ошибки.'
                else:
                    reply_message = f'{reply_message} Преподавателю все понравилось. ' \
                                    f'Можно приступать к следующему уроку!'
                await message.answer(reply_message)
        except ReadTimeout:
            logging.info(f'Превышено время ожидания. Прошло {timeout} сек. Повтор.')
            await message.answer(f'Превышено время ожидания. Прошло {timeout} сек. Повтор.')
        except (ConnectionError, NetworkError, ClientConnectorError) as error:
            logging.info(f'Ошибка. Потеря соединения. {error}')
            time.sleep(5)


if __name__ == '__main__':
    executor.start_polling(dp)
