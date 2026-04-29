import json
from typing import Any, Dict, List, Optional
import httpx
from app.core.config import settings


class DeepSeekClient:
    """Minimal OpenAI-compatible DeepSeek chat client.

    The project can run without a key. If DEEPSEEK_API_KEY is empty, agents fall back
    to rule-based logic, which is useful for demo, tests and thesis presentation.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.deepseek_api_key
        self.base_url = settings.deepseek_base_url.rstrip('/')
        self.model = settings.deepseek_model
        self.timeout = settings.deepseek_timeout

    @property
    def available(self) -> bool:
        return bool(self.api_key) and settings.enable_llm

    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.2) -> str:
        if not self.available:
            raise RuntimeError('DeepSeek API key is not configured or LLM is disabled.')
        url = f'{self.base_url}/v1/chat/completions'
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }
        payload = {
            'model': self.model,
            'messages': messages,
            'temperature': temperature,
        }
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
        return data['choices'][0]['message']['content']

    def json_chat(self, system: str, user: str, fallback: Dict[str, Any]) -> Dict[str, Any]:
        if not self.available:
            return fallback
        try:
            text = self.chat([
                {'role': 'system', 'content': system + '\n你必须只输出合法 JSON，不要输出 Markdown。'},
                {'role': 'user', 'content': user},
            ])
            text = text.strip()
            if text.startswith('```'):
                text = text.strip('`')
                if text.lower().startswith('json'):
                    text = text[4:].strip()
            return json.loads(text)
        except Exception as exc:
            result = dict(fallback)
            result['_llm_error'] = str(exc)
            return result
