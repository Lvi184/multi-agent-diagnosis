from app.services.llm_client import DeepSeekClient


class BaseAgent:
    name = 'BaseAgent'

    def __init__(self):
        self.llm = DeepSeekClient()
