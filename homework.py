import os
import requests
import time
import logging

from dotenv import load_dotenv

from telegram import Bot

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='main.log')


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправка сообщения о проверке."""
    try:
        bot.send_massage(TELEGRAM_CHAT_ID, message)
        logging.info('Сообщение пользователю {TELEGRAM_CHAT_ID} отправлено')
    except Exception:
        logging.critical('Сообщения пользователю {TELEGRAM_CHAT_ID} нет')


def get_api_answer(current_timestamp):
    """Проверка допустпонсти API."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    headers = HEADERS
    response = requests.get(ENDPOINT,
                            headers=headers,
                            params=params)
    if response.status_code != 200:
        message = f'ошибочный статус ответа по API: {response.status_code}'
        raise Exception(message)
    return response.json()


def check_response(response):
    """Проверка данных ответа."""
    if type(response) != dict:
        message = 'ответ пришел не в виде словаря:'
        logging.error(message)
        raise TypeError(message)
    if 'homeworks' not in response:
        message = 'Передан некорретный словарь'
        logging.error(message)
        raise Exception(message)
    try:
        homework = response.get('homeworks')
    except Exception as error:
        message = f'отсутствие ожидаемых ключей в ответе API: {error}'
        raise Exception(message)
    if type(homework) != list:
        message = 'Передан не список'
        logging.error(message)
        raise TypeError(message)
    return homework


def parse_status(homework):
    """Парсинг данных со страницы."""
    if homework == []:
        message = 'Обновлений нет'
        raise Exception(message)
    else:
        homework_status = homework.get('status')
        homework_name = homework.get('homework_name')
        if homework_status == '':
            message = 'отствует статус домашней работы'
            raise Exception(message)
        if homework_name == '':
            return None

    verdict = HOMEWORK_STATUSES[homework_status]

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка токенов в окружении."""
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
    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    while True:
        try:

            get = get_api_answer(current_timestamp)
            check = check_response(get)
            parse = parse_status(check[0])
            send_message(bot, parse)
            current_timestamp = {'from_date': current_timestamp - 599}
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            time.sleep(RETRY_TIME)
        else:
            return None


if __name__ == '__main__':
    main()
