from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'MoodAngels-LangGraph-DeepSeek'
    app_version: str = '2.0.0'

    llm_provider: str = 'deepseek'
    enable_llm: bool = True
    deepseek_api_key: str = ''
    deepseek_base_url: str = 'https://api.deepseek.com'
    deepseek_model: str = 'deepseek-chat'
    deepseek_timeout: int = 60

    use_real_langgraph: bool = False
    cors_allow_origins: str = '*'

    @property
    def cors_origins(self) -> List[str]:
        if self.cors_allow_origins.strip() == '*':
            return ['*']
        return [x.strip() for x in self.cors_allow_origins.split(',') if x.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
