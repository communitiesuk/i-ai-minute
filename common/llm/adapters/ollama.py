import json
import logging
from typing import Any

from openai import AsyncOpenAI
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionDeveloperMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)

from common.settings import get_settings

from .base import ModelAdapter, T

settings = get_settings()
logger = logging.getLogger(__name__)


class OllamaModelAdapter(ModelAdapter):
    def __init__(
        self,
        model: str,
        base_url: str,
        **kwargs: Any,
    ) -> None:
        self._model = model
        self.async_client = AsyncOpenAI(
            base_url=base_url,
            api_key="ollama",
        )
        self._kwargs = kwargs

    @staticmethod
    def _convert_to_openai_message(msg: dict[str, str]) -> ChatCompletionMessageParam:
        role = msg["role"]
        content = msg["content"]

        if role == "system":
            return ChatCompletionSystemMessageParam(role="system", content=content)
        elif role == "user":
            return ChatCompletionUserMessageParam(role="user", content=content)
        elif role == "assistant":
            return ChatCompletionAssistantMessageParam(role="assistant", content=content)
        elif role == "developer":
            return ChatCompletionDeveloperMessageParam(role="developer", content=content)
        else:
            error_msg = f"Invalid role: {role}"
            raise ValueError(error_msg)

    async def structured_chat(self, messages: list[dict[str, str]], response_format: type[T]) -> T:
        # Get the full schema
        schema = response_format.model_json_schema()

        def parse_schema(s):
            if "type" not in s:
                if "anyOf" in s:
                    return " | ".join([parse_schema(x) for x in s["anyOf"]])
                return "any"

            type_ = s["type"]
            if type_ == "object":
                props = s.get("properties", {})
                obj_repr = "{\n"
                for name, info in props.items():
                    desc = f" // {info.get('description', '')}" if info.get("description") else ""
                    obj_repr += f'  "{name}": {parse_schema(info)},{desc}\n'
                obj_repr += "}"
                return obj_repr
            elif type_ == "array":
                items = s.get("items", {})
                return f"[{parse_schema(items)}]"
            elif type_ == "string":
                return '"string"'
            elif type_ == "integer" or type_ == "number":
                return "number"
            elif type_ == "boolean":
                return "boolean"
            return type_

        # Resolve $defs if present
        def resolve_refs(s, root_schema):
            if isinstance(s, dict):
                if "$ref" in s:
                    ref_path = s["$ref"].split("/")
                    ref_node = root_schema
                    for part in ref_path[1:]:
                        ref_node = ref_node[part]
                    return resolve_refs(ref_node, root_schema)
                return {k: resolve_refs(v, root_schema) for k, v in s.items()}
            elif isinstance(s, list):
                return [resolve_refs(x, root_schema) for x in s]
            return s

        resolved_schema = resolve_refs(schema, schema)
        json_template = parse_schema(resolved_schema)

        json_instruction = f"""

You must respond with ONLY valid JSON in this exact format (no markdown, no code blocks):
{json_template}

Provide actual values for each field, not the type definitions or placeholders like <string>."""

        modified_messages = messages.copy()
        if modified_messages:
            last_msg = modified_messages[-1].copy()
            last_msg["content"] = last_msg["content"] + json_instruction
            modified_messages[-1] = last_msg

        openai_messages = [self._convert_to_openai_message(msg) for msg in modified_messages]


        response = await self.async_client.chat.completions.create(
            model=self._model,
            messages=openai_messages,
            response_format={"type": "json_object"},
            temperature=self._kwargs.get("temperature", 0.0),
        )

        content = response.choices[0].message.content

        if content is None:
            msg = "Received empty response from Ollama"
            raise ValueError(msg)

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
            openai_messages = [self._convert_to_openai_message(msg) for msg in messages]

            response = await self.async_client.chat.completions.create(
                model=self._model,
                messages=openai_messages,
                temperature=0.0,
            )

            content = response.choices[0].message.content
            if content is None:
                msg = "Received empty response from Ollama"
                raise ValueError(msg)
            return content
        except Exception as e:
            logger.error("Ollama chat failed: %s: %s", type(e).__name__, str(e))
            raise
