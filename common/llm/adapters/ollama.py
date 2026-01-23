import json
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
            api_key="ollama",
        )
        self._kwargs = kwargs

    async def structured_chat(self, messages: list[dict[str, str]], response_format: type[T]) -> T:
        schema = response_format.model_json_schema()
        json_instruction = f"\n\nRespond with valid JSON matching this schema:\n{schema}"

        modified_messages = messages.copy()
        if modified_messages:
            last_msg = modified_messages[-1].copy()
            last_msg["content"] = last_msg["content"] + json_instruction
            modified_messages[-1] = last_msg

        response = await self.async_client.chat.completions.create(
            model=self._model,
            messages=modified_messages,
            response_format={"type": "json_object"},
            temperature=self._kwargs.get("temperature", 0.0),
        )

        content = response.choices[0].message.content
        try:
            json_data = json.loads(content)
            return response_format.model_validate(json_data)
        except Exception as e:
            logger.error("Ollama JSON parsing/validation failed: %s: %s", type(e).__name__, str(e))
            raise

    async def chat(self, messages: list[dict[str, str]]) -> str:
        try:
            response = await self.async_client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=0.0,
            )

            return response.choices[0].message.content
        except Exception as e:
            logger.error("Ollama chat failed: %s: %s", type(e).__name__, str(e))
            raise
