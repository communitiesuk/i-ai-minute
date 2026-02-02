import logging
from typing import TypeVar

from openai import AsyncAzureOpenAI
from openai.types.chat import ChatCompletion
from openai.types.chat.chat_completion import Choice

from .base import ModelAdapter

T = TypeVar("T")
logger = logging.getLogger(__name__)

class AzureAPIMModelAdapter(ModelAdapter):
    def __init__(
        self,
        url: str,
        deployment: str,
        api_version: str,
        access_token: str,
        subscription_key: str,
    ) -> None:
        self._deployment = deployment
        self.async_apim_client = AsyncAzureOpenAI(
            base_url=url,
            api_key="", # Dummy key unused by APIM
            api_version=api_version,
            default_headers={
                "Authorization": f"Bearer {access_token}",
                "Ocp-Apim-Subscription-Key": subscription_key,
            },
        )

    async def structured_chat(
        self, messages: list[dict[str, str]], response_format: type[T]
    ) -> T:
        response = await self.async_apim_client.beta.chat.completions.parse(
            model=self._deployment,
            messages=messages,
            response_format=response_format,
        )
        choice = response.choices[0]
        self.choice_incomplete(choice, response)
        return choice.message.parsed

    async def chat(self, messages: list[dict[str, str]]) -> str:

        response = await self.async_apim_client.chat.completions.create(
            model=self._deployment, # Use deployment name as model
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
