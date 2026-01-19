import logging
from typing import TypeVar

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion
from openai.types.chat.chat_completion import Choice

from common.settings import get_settings

from .base import ModelAdapter

settings = get_settings()
T = TypeVar("T")
logger = logging.getLogger(__name__)


class DirectOpenAIModelAdapter(ModelAdapter):
    def __init__(
        self,
        model: str,
        api_key: str,
        **kwargs,
    ) -> None:
        self._model = model
        self.async_client = AsyncOpenAI(
            api_key=api_key,
        )
        self._kwargs = kwargs

    async def structured_chat(self, messages: list[dict[str, str]], response_format: type[T]) -> T:
        response = await self.async_client.beta.chat.completions.parse(
            model=self._model, messages=messages, response_format=response_format, **self._kwargs
        )
        choice = self.handle_response(response)

        return choice.message.parsed

    async def chat(self, messages: list[dict[str, str]]) -> str:
        response = await self.async_client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=0.0,
            max_tokens=16384,
        )
        choice = response.choices[0]
        self.choice_incomplete(choice, response)
        return choice.message.content

    @staticmethod
    def choice_incomplete(choice: Choice, response: ChatCompletion) -> bool:
        if choice.finish_reason == "length":
            logger.warning(
                "max output tokens reached: ID: %s prompt_tokens: %s completion_tokens %s",
                response.id,
                response.usage.prompt_tokens,
                response.usage.completion_tokens,
            )
            return True
        return False

    @staticmethod
    def handle_response(response: ChatCompletion) -> Choice:
        choice = response.choices[0]
        if choice.finish_reason == "length":
            logger.warning(
                "max output tokens reached: ID: %s prompt_tokens: %s completion_tokens %s",
                response.id,
                response.usage.prompt_tokens,
                response.usage.completion_tokens,
            )
        return choice
