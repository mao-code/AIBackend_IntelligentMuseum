from abc import ABC, abstractmethod
from dotenv import load_dotenv
import os

class RAGInterface(ABC):
    def __init__(self):
        load_dotenv()
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
    
    @abstractmethod
    def generate_response(self, question):
        pass

    @abstractmethod
    def generate_response_with_retrieval(self, question):
        pass