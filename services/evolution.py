import requests
from django.conf import settings


class EvolutionAPI:
    def __init__(self):
        """
        Initializes the Evolution API client using configuration settings.
        """
        self.__base_url: str = settings.EVOLUTION_API_BASE_URL
        self.__api_key: str = settings.EVOLUTION_API_KEY
        self.__instance_name: str = settings.INSTANCE_NAME

    def __str__(self):
        return f"Evolution API client for instance '{self.__instance_name}', base URL: {self.__base_url}, API key: {self.__api_key}"

    def instance_exists(self):
        url = f"{self.__base_url}/instance/fetchInstances?instanceName={self.__instance_name}"

        headers = {"apikey": self.__api_key, "Content-Type": "application/json"}

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            if isinstance(data, dict) and "instance" in data:
                instances = [data]
            elif isinstance(data, list):
                instances = data
            else:
                return False

            for item in instances:
                instance = item.get("instance")
                if (
                    isinstance(instance, dict)
                    and instance.get("instanceName") == self.__instance_name
                ):
                    return True

        except requests.RequestException as e:
            print(f"Failed to retrieve instance status: {e}")

        return False

    def send_text_message(self, number: str, text: str, delay: int = 0) -> bool:
        """
        Sends a text message using the Evolution API.

        :param number: Recipient's phone number in international format (e.g., "5511999999999").
        :param text: Message text.
        :param delay: Optional delay in seconds before sending the message.
        :return: True if the message was sent successfully, False otherwise.
        """
        url = f"{self.__base_url}/message/sendText/{self.__instance_name}"

        payload = {
            "number": number,
            "options": {"delay": delay},
            "textMessage": {"text": text},
        }

        headers = {"apikey": self.__api_key, "Content-Type": "application/json"}

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            response_data = response.json()

            if response_data.get("key") and response_data["key"].get("id"):
                return True
            else:
                # Se a resposta não for sucesso, lança exceção
                raise Exception(f"Erro ao enviar mensagem: {response_data}")
        except requests.RequestException as e:
            print(f"Failed to send message: {e}")
            raise

    def instance_connect(self) -> dict:
        """
        Connects to the instance and retrieves the configuration data.

        :return: A dictionary with the response data or an empty dictionary if the connection fails.
        """
        url = f"{self.__base_url}/instance/connect/{self.__instance_name}"

        headers = {"apikey": self.__api_key, "Content-Type": "application/json"}

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Ensures the request was successful
            return response.json()  # Return the JSON response from the API
        except requests.RequestException as e:
            print(f"Failed to connect to instance: {e}")

        return {}  # Return an empty dictionary in case of failure

    def get_instance_status(self) -> str:
        """
        Retrieves the connection state of the instance.

        :return: A string representing the state of the instance ('open' or 'close').
        """
        url = f"{self.__base_url}/instance/connectionState/{self.__instance_name}"

        headers = {"apikey": self.__api_key, "Content-Type": "application/json"}

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Ensures the request was successful
            data = response.json()

            # Check if the 'instance' and 'state' keys are present in the response data
            status = data.get("instance", {}).get("state", "")

            if status == "open":
                return "Connected"
            elif status == "close":
                return "Disconnected"
            else:
                return "Connecting"
        except requests.RequestException as e:
            print(f"Failed to retrieve instance status: {e}")
            return "Error"

    def logout_instance(self) -> str:
        """
        Logs out the instance from the Evolution API.

        :return: A string indicating the logout status ('Success', 'Failed', or 'Error').
        """
        url = f"{self.__base_url}/instance/logout/{self.__instance_name}"

        headers = {"apikey": self.__api_key, "Content-Type": "application/json"}

        try:
            response = requests.delete(url, headers=headers)
            response.raise_for_status()  # Ensures the request was successful
            data = response.json()

            if data.get("status") == "SUCCESS":
                return True
            else:
                return False
        except requests.RequestException as e:
            print(f"Failed to log out: {e}")
            return "Error"
