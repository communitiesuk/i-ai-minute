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
        # Get the schema and extract just the properties for clearer instructions
        schema = response_format.model_json_schema()
        
        # Build a clearer instruction that focuses on the actual fields, not the full schema
        properties = schema.get("properties", {})
        field_descriptions = []
        for field_name, field_info in properties.items():
            field_type = field_info.get("type", "string")
            field_desc = field_info.get("description", "")
            field_descriptions.append(f'  "{field_name}": <{field_type}> {field_desc}')
        
        fields_str = "\n".join(field_descriptions)
        
        json_instruction = f"""

You must respond with ONLY valid JSON in this exact format (no markdown, no code blocks):
{{
{fields_str}
}}

Provide actual values for each field, not the schema definition."""

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
        
        # Strip markdown code blocks if present
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]  # Remove ```json
        elif content.startswith("```"):
            content = content[3:]  # Remove ```
        if content.endswith("```"):
            content = content[:-3]  # Remove closing ```
        content = content.strip()
        
        try:
            json_data = json.loads(content)
            
            # Check if the LLM returned the schema instead of actual data
            if "properties" in json_data and "type" in json_data:
                logger.error("Ollama returned JSON schema instead of data. Raw content: %s", content)
                raise ValueError("LLM returned schema definition instead of actual values")
            
            return response_format.model_validate(json_data)
        except Exception as e:
            logger.error("Ollama JSON parsing/validation failed: %s: %s", type(e).__name__, str(e))
            logger.error("Raw response content: %s", content)
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
