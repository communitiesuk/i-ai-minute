import logging
from typing import TypeVar

from openai import AsyncOpenAI

from common.settings import get_settings

from .base import ModelAdapter

settings = get_settings()
T = TypeVar("T")
logger = logging.getLogger(__name__)


class OllamaModelAdapter(ModelAdapter):
    def __init__(
        self,
        model: str,
        base_url: str,
        **kwargs,
    ) -> None:
        self._model = model
        self.async_client = AsyncOpenAI(
            base_url=base_url,
            api_key="ollama", # Ollama doesn't typically require an API key, but client needs one
        )
        self._kwargs = kwargs

    async def structured_chat(self, messages: list[dict[str, str]], response_format: type[T]) -> T:
        # Ollama via OpenAI compat layer supports JSON mode but structured outputs (pydantic) 
        # via the .beta.chat.completions.parse are newer and might not be fully supported by all ollama versions
        # or all models. However, standard approach is to try .parse if the library allows it.
        # But commonly with Ollama we stick to standard chat with json_mode + pydantic validation manually 
        # OR we rely on the client library's parsing if it works.
        # Given we are using the 'openai' python library, let's try the .parse method as it's the interface 
        # required by the ChatBot class.
        # Note: If this fails, we might need a more manual approach (request json, parse with pydantic).
        
        # For robustness with common/llm/client.py expecting a pydantic model response:
        response = await self.async_client.beta.chat.completions.parse(
            model=self._model, messages=messages, response_format=response_format, **self._kwargs
        )
        return response.choices[0].message.parsed

    async def chat(self, messages: list[dict[str, str]]) -> str:
        response = await self.async_client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=0.0,
            # max_tokens might be optional or handled differently
        )
        return response.choices[0].message.content
