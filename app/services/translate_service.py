from dotenv import load_dotenv
import os
import requests
from babel import Locale

class Translate:
    def __init__(self):
        load_dotenv()
        self.google_api_key = os.getenv('GOOGLE_API_KEY')
        self.api_base = "https://translation.googleapis.com/language/translate/v2"

    def translate(self, text, target_language):
        # use the nmt model to translate for free 500K characters per month
        url = f"{self.api_base}?q={text}&target={target_language}&model=nmt&key={self.google_api_key}"
        response = requests.get(url)

        data = response.json()
        translated_text = data["data"]["translations"][0]["translatedText"]

        return translated_text
    
    def get_language_name_in_chinese(self, language_code):
        try:
            locale = Locale.parse(language_code)
        except:
            return None

        # return the traditional chinese name of the language
        return locale.get_display_name('zh_Hant_TW')
