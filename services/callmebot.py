import urllib.parse

import requests
from django.conf import settings


class CallMeBot:
    def __init__(self):
        self.__api_key = settings.CALLMEBOT_API_KEY
        self.__phone_number = settings.CALLMEBOT_PHONE_NUMBER
        self.__base_url = f"{settings.CALLMEBOT_API_URL}?phone={self.__phone_number}&apikey={self.__api_key}"

    def send_text_message(self, message):
        message_formatted = self.format_message_for_callmebot(message)
        url = f"{self.__base_url}&text={message_formatted}"
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(f"Erro ao enviar mensagem: {response.text}")
        return response

    def format_message_for_callmebot(self, message):
        # Codifica toda a mensagem para URL de forma segura
        return urllib.parse.quote_plus(message)
