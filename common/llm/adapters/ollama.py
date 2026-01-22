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
        logger.info("Initialized OllamaModelAdapter with model=%s, base_url=%s", model, base_url)

    async def structured_chat(self, messages: list[dict[str, str]], response_format: type[T]) -> T:
        try:
            logger.info("Ollama structured_chat request: model=%s, messages=%d messages", self._model, len(messages))
            logger.debug("Ollama request messages: %s", messages)
            logger.debug("Ollama response_format: %s", response_format)

            # Add JSON schema instruction to the last message
            schema = response_format.model_json_schema()
            json_instruction = f"\n\nRespond with valid JSON matching this schema:\n{schema}"

            modified_messages = messages.copy()
            if modified_messages:
                last_msg = modified_messages[-1].copy()
                last_msg["content"] = last_msg["content"] + json_instruction
                modified_messages[-1] = last_msg

            logger.debug("Modified last message with JSON schema instruction")

            # Use JSON mode instead of .parse()
            response = await self.async_client.chat.completions.create(
                model=self._model,
                messages=modified_messages,
                response_format={"type": "json_object"},
                temperature=self._kwargs.get("temperature", 0.0),
            )

            content = response.choices[0].message.content
            logger.info("Ollama structured_chat raw response: %d chars", len(content) if content else 0)
            logger.debug("Ollama raw JSON response: %s", content)

            json_data = json.loads(content)
            parsed = response_format.model_validate(json_data)

            logger.info("Ollama structured_chat successfully parsed to %s", type(parsed).__name__)
            logger.debug("Ollama parsed output: %s", parsed)

            return parsed
        except Exception as e:
            logger.error("Ollama structured_chat failed: %s: %s", type(e).__name__, str(e))
            logger.error("Model: %s, Messages count: %d", self._model, len(messages))
            logger.error("Response format: %s", response_format)
            if "content" in locals():
                logger.error("Raw response content: %s", content)
            logger.exception("Full error details:")
            raise

    async def chat(self, messages: list[dict[str, str]]) -> str:
        try:
            logger.info("Ollama chat request: model=%s, messages=%d messages", self._model, len(messages))
            logger.debug("Ollama request messages: %s", messages)

            response = await self.async_client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=0.0,
            )

            content = response.choices[0].message.content
            logger.info("Ollama chat response received: %d chars", len(content) if content else 0)
            logger.debug("Ollama response content: %s", content)

            return content
        except Exception as e:
            logger.error("Ollama chat failed: %s: %s", type(e).__name__, str(e))
            logger.error("Model: %s, Messages count: %d", self._model, len(messages))
            logger.exception("Full error details:")
            raise
