import requests
import os
import json
import time
import logging
import telegram
import asyncio

from requests.exceptions import ConnectionError, ReadTimeout
from dotenv import load_dotenv
from textwrap import dedent


async def main():
    load_dotenv()
    devman_token = os.environ.get('DEVMAN_TOKEN')
    bot = telegram.Bot(os.environ.get('TELEGRAM_TOKEN'))
    user_id = os.environ.get('TELEGRAM_USER_ID')
    logging.basicConfig(level=logging.INFO)
    url = 'https://dvmn.org/api/long_polling/'
    headers = {'Authorization': f'Token {devman_token}'}
    timeout = 100
    payload = {'timestamp': None}
    await bot.send_message(user_id, 'Стартую. Направляю запрос Devmanу.')

    while True:
        try:
            response = requests.get(url, headers=headers, params=payload, timeout=timeout)
            response.raise_for_status()
            logging.info(response.url)
            devman_response_in_format = response.json()
            logging.info(json.dumps(devman_response_in_format, indent=2, ensure_ascii=False))
            if devman_response_in_format['status'] == 'timeout':
                payload['timestamp'] = devman_response_in_format['timestamp_to_request']
                await bot.send_message(user_id, 'Нет обновлений.')
            elif devman_response_in_format['status'] == 'found':
                payload['timestamp'] = devman_response_in_format['last_attempt_timestamp']
                reply_message = f'''Преподаватель проверил работу \
"{devman_response_in_format["new_attempts"][0]["lesson_title"]}"! \
{devman_response_in_format["new_attempts"][0]["lesson_url"]}
'''
                if devman_response_in_format["new_attempts"][0]["is_negative"]:
                    reply_message = f'''{reply_message} \
К сожалению в работе нашлись ошибки.
'''
                else:
                    reply_message = f'''{reply_message} \
Преподавателю все понравилось. Можно приступать к следующему уроку!
'''
                await bot.send_message(user_id, dedent(reply_message))
        except ReadTimeout:
            logging.info(f'Превышено время ожидания. Прошло {timeout} сек. Повтор.')
            await bot.send_message(user_id, f'Превышено время ожидания. Прошло {timeout} сек. Повтор.')
        except (ConnectionError, telegram.error.NetworkError, telegram.error.TelegramError) as error:
            logging.info(f'Потеря или ошибка соединения. {error}')
            time.sleep(5)


if __name__ == '__main__':
    asyncio.run(main())
