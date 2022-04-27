import os
import sys
import time
import requests
import logging

from dotenv import load_dotenv

from telegram import Bot

from http import HTTPStatus
from urllib.error import HTTPError


load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
LAST_CHECK = 599
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


class ApiAnswerException(Exception):
    """Кастомная ошибка ответа API."""

    pass


class MassageNotSent(Exception):
    """Кастомная ошибка сообщения."""

    pass


class CheckNotPassed(Exception):
    """Кастомная ошибка проверки ответа API."""

    pass


class WrongParseStatus(Exception):
    """Кастомная ошибка статуса парсинга."""

    pass


def send_message(bot, message):
    """Отправка сообщения о проверке."""
    try:
        logging.info('Сообщение пользователю {TELEGRAM_CHAT_ID} отправляется')
        sending = bot.send_massage(TELEGRAM_CHAT_ID, message)
        if sending.status_code != HTTPStatus.OK:
            raise MassageNotSent
    except MassageNotSent as error:
        MassageNotSent('Сообщения пользователю {TELEGRAM_CHAT_ID} '
                       f'не отправлено. Причина: {error}')
    else:
        logging.info('Сообщение пользователю {TELEGRAM_CHAT_ID} отправлено')
        return sending


def get_api_answer(current_timestamp):
    """Проверка допустпонсти API."""
    try:
        timestamp = current_timestamp or int(time.time())
        params = {'from_date': timestamp}
        response = requests.get(ENDPOINT,
                                headers=HEADERS,
                                params=params)
        if response.status_code != HTTPStatus.OK:
            raise HTTPError
    except HTTPError:
        message = f'ошибочный статус ответа по API: {response.status_code}'
        logging.error(message)
        raise HTTPError(message)
    return response.json()


def check_response(response):
    """Проверка данных ответа."""
    if not isinstance(response, dict):
        message = 'ответ пришел не в виде словаря.'
        raise TypeError(message)
    if 'homeworks' and 'current_date' not in response:
        message = 'Передан некорретный словарь.'
        raise CheckNotPassed(message)
    try:
        homework = response.get('homeworks')
    except CheckNotPassed as error:
        message = f'отсутствие ожидаемых ключей в ответе API: {error}'
        raise CheckNotPassed(message)
    if not isinstance(homework, list):
        message = 'Передан не список.'
        raise TypeError(message)
    return homework


def parse_status(homework):
    """Парсинг данных со страницы."""
    if homework == []:
        message = 'Обновлений нет'
        raise WrongParseStatus(message)
    homework_status = homework.get('status')
    homework_name = homework.get('homework_name')
    if homework_status == '':
        message = 'отствует статус домашней работы'
        raise WrongParseStatus(message)
    if homework_name == '':
        return None
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка токенов в окружении."""
    # Так построено задание. Если упростить не проходят тесты
    if not PRACTICUM_TOKEN:
        logging.critical('Отсутствует обязательная переменная окружения:'
                         'PRACTICUM_TOKEN Программа принудительно остановлена.'
                         )
        return False
    if not TELEGRAM_TOKEN:
        logging.critical('Отсутствует обязательная переменная окружения:'
                         'TELEGRAM_TOKEN Программа принудительно остановлена.'
                         )
        return False
    if not TELEGRAM_CHAT_ID:
        logging.critical('Отсутствует обязательная переменная окружения:'
                         'TELEGRAM_CHAT_ID Программа принудительно остановлена'
                         )
        return False
    return True


def main():
    """Основная логика работы бота."""
    current_timestamp = int(time.time())
    if not check_tokens():
        sys.exit(0)
    while True:
        try:
            current_timestamp = {'from_date': current_timestamp - LAST_CHECK}
            get = get_api_answer(current_timestamp)
            check = check_response(get)
            parse = parse_status(check[0])
            send_message(Bot(token=TELEGRAM_TOKEN), parse)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    logging.basicConfig(format=('%(asctime)s - %(name)s - %(levelname)s'
                                ' - %(message)s - %(funcName)s - %(lineno)s'),
                        filename='main.log',
                        level=logging.INFO)
    main()
