import os
import json
import asyncio
from typing import AsyncGenerator, Optional
from sqlalchemy.orm import Session


class LLMService:
    """Supports OpenAI, Anthropic (Claude), Volcano Engine (火山引擎)"""

    async def stream_chat(
        self,
        messages: list,
        provider: str,
        api_key: str,
        model_name: str,
        base_url: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        if provider == "anthropic":
            async for chunk in self._stream_anthropic(messages, api_key, model_name):
                yield chunk
        elif provider == "openai":
            async for chunk in self._stream_openai(messages, api_key, model_name, base_url):
                yield chunk
        elif provider == "volcano":
            volcano_url = base_url or "https://ark.volcengineapi.com/api/v3"
            async for chunk in self._stream_openai(messages, api_key, model_name, volcano_url):
                yield chunk
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    async def _stream_openai(
        self,
        messages: list,
        api_key: str,
        model_name: str,
        base_url: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url if base_url else None
        )
        stream = await client.chat.completions.create(
            model=model_name,
            messages=messages,
            stream=True,
            max_tokens=4096,
        )
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def _stream_anthropic(
        self,
        messages: list,
        api_key: str,
        model_name: str,
    ) -> AsyncGenerator[str, None]:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=api_key)

        # Extract system message if present
        system_msg = None
        chat_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                chat_messages.append({"role": msg["role"], "content": msg["content"]})

        kwargs = {
            "model": model_name,
            "max_tokens": 4096,
            "messages": chat_messages,
        }
        if system_msg:
            kwargs["system"] = system_msg

        async with client.messages.stream(**kwargs) as stream:
            async for text in stream.text_stream:
                yield text

    async def complete(
        self,
        messages: list,
        provider: str,
        api_key: str,
        model_name: str,
        base_url: Optional[str] = None,
    ) -> str:
        """Non-streaming completion"""
        result = []
        async for chunk in self.stream_chat(messages, provider, api_key, model_name, base_url):
            result.append(chunk)
        return "".join(result)


def get_llm_config_for_agent(agent_type: str, db: Session):
    """Get the best LLM config for a given agent type"""
    from models import LLMConfig
    # Try agent-specific config first
    config = db.query(LLMConfig).filter(
        LLMConfig.agent_type == agent_type,
        LLMConfig.is_active == True
    ).first()
    if not config:
        # Fall back to "all" config
        config = db.query(LLMConfig).filter(
            LLMConfig.agent_type == "all",
            LLMConfig.is_active == True
        ).first()
    return config
