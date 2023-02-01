import requests

from utilities import read_filepaths

FILEPATHS = read_filepaths()


class AzureAPI:
    AZURE_API_URL = "https://signature.eastus.cts.speech.microsoft.com/api/v1/Signature/GenerateVoiceSignatureFromByteArray?language=en-us&enableTranscription=true"
    AZURE_API_KEY = open(FILEPATHS['AZURE_API_KEY']).read().strip()
    HEADERS = {
        "accept": "application/json",
        "Ocp-Apim-Subscription-Key": AZURE_API_KEY,
    }

    def __init__(self, audio_path):
        self.payload = open(audio_path, "rb").read()

        # self.response = requests.post(
        #     self.AZURE_API_URL,
        #     data=self.payload,
        #     headers=self.HEADERS,
        #     verify=False,  # ! some HTTPS issue
        # ).json()

    def get_transcription(self):
        try:
            return self.response.get("Transcription")
        except Exception:
            return " "

    @property
    def response(self):
        return requests.post(
            self.AZURE_API_URL,
            data=self.payload,
            headers=self.HEADERS,
            timeout=20,
            verify=False,  # ! some HTTPS issue
        ).json()
