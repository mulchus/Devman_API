import requests
import os
import time
import logging
import telegram

from requests.exceptions import ConnectionError, ReadTimeout
from dotenv import load_dotenv
from textwrap import dedent


class MyLogsHandler(logging.Handler):
    def __int__(self, bot, user_id):
        self.bot = bot
        self.user_id = user_id

    def emit(self, record):
        log_entry = self.format(record)
        self.bot.send_message(self.user_id, log_entry)


def main():
    load_dotenv()
    bot = telegram.Bot(os.environ.get('TELEGRAM_TOKEN'))
    user_id = os.environ.get('TELEGRAM_USER_ID')
    devman_token = os.environ.get('DEVMAN_TOKEN')

    logger = logging.getLogger("event_logging")
    logger.setLevel(logging.INFO)
    logger_settings = MyLogsHandler(bot, user_id)
    logger_settings.setLevel(logging.INFO)
    logger_settings.setFormatter(logging.Formatter("%(asctime)s: %(levelname)s; %(message)s",
                                                   datefmt="%d/%b/%Y %H:%M:%S"))
    logger.addHandler(logger_settings)

    url = 'https://dvmn.org/api/long_polling/'
    headers = {'Authorization': f'Token {devman_token}'}
    timeout = 100
    pause_verification = 600
    payload = {'timestamp': None}
    start_message = 'Стартую. Направляю запрос Devmanу.'
    logger.info(start_message)
    while True:
        try:
            response = requests.get(url, headers=headers, params=payload, timeout=timeout)
            response.raise_for_status()
            about_checks = response.json()
            if about_checks['status'] == 'timeout':
                payload['timestamp'] = about_checks['timestamp_to_request']
                # logger.info('Нет обновлений.')
            elif about_checks['status'] == 'found':
                payload['timestamp'] = about_checks['last_attempt_timestamp']
                reply_message = dedent(f'''
                    Преподаватель проверил работу:
                    "{about_checks["new_attempts"][0]["lesson_title"]}"!
                    {about_checks["new_attempts"][0]["lesson_url"]}
                ''')
                if about_checks["new_attempts"][0]["is_negative"]:
                    reply_message += 'К сожалению в работе нашлись ошибки.'
                else:
                    reply_message += 'Преподавателю все понравилось. Можно приступать к следующему уроку!'
                logger.info(dedent(reply_message))
        except ReadTimeout:
            logger.error(f'Превышено время ожидания. Прошло {timeout} сек. Повтор.')
        except (ConnectionError, telegram.error.NetworkError, telegram.error.TelegramError) as error:
            logger.error(f'Потеря или ошибка соединения. {error}')
            time.sleep(5)
        except Exception as err:
            logger.error('Бот упал с ошибкой:')
            logger.exception(err)

        time.sleep(pause_verification)


if __name__ == '__main__':
    main()
