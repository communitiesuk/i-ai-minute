import logging
from typing import TypeVar

from openai import AsyncAzureOpenAI
from openai.types.chat import ChatCompletion
from openai.types.chat.chat_completion import Choice

from common.settings import get_settings

from .base import ModelAdapter

settings = get_settings()
T = TypeVar("T")
logger = logging.getLogger(__name__)


class OpenAIModelAdapter(ModelAdapter):
    def __init__(
        self,
        model: str,
        api_key: str,
        azure_endpoint: str,
        azure_deployment: str,
        api_version: str = "2024-10-21",
        **kwargs,
    ) -> None:

        self._model = model
        
 
        if not azure_endpoint:
            raise ValueError("Azure Endpoint is required for Azure OpenAI")
        if not azure_deployment:
            raise ValueError("Azure Deployment name is required for Azure OpenAI")
    
        arguments_for_client = {
            "api_key": api_key,
            "api_version": api_version,
        }


        endpoint = azure_endpoint.rstrip("/")
        arguments_for_client["base_url"] = f"{endpoint}/deployments/{azure_deployment}"

        self.async_azure_client = AsyncAzureOpenAI(**arguments_for_client)
        self._kwargs = kwargs

    async def structured_chat(self, messages: list[dict[str, str]], response_format: type[T]) -> T:
        response = await self.async_azure_client.beta.chat.completions.parse(
            model=self._model, messages=messages, response_format=response_format, **self._kwargs
        )
        choice = self.handle_response(response)

        return choice.message.parsed

    async def chat(self, messages: list[dict[str, str]]) -> str:
        response = await self.async_azure_client.chat.completions.create(
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
