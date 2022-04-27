import os
import sys
import time

from http import HTTPStatus
import requests
import logging

from dotenv import load_dotenv

from telegram import Bot

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



def get_api_answer(current_timestamp):
    """Проверка допустпонсти API."""
    try:
        timestamp = current_timestamp or int(time.time())
        needed_response = 200
        params = {'from_date': timestamp}
        response = requests.get(ENDPOINT,
                                headers=HEADERS,
                                params=params)
        if response.status_code != needed_response:
            raise HTTPError
    except HTTPError:
        message = f'ошибочный статус ответа по API: {response.status_code}'
        logging.error(message)
        raise HTTPError(message)
    else:
        
        print(response)
        print(HTTPStatus.OK)
        return response.json()

get_api_answer(0)