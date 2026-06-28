"""
LLM Client - OpenAI Compatible API Client
Supports MiMo and other OpenAI-compatible APIs
"""
from typing import List, Optional, Generator

from openai import OpenAI

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class DashScopeClient:
    """
    LLM Client using OpenAI-compatible API
    Supports MiMo, DashScope, and other compatible endpoints
    """

    def __init__(self):
        self._client = None
        self._embedding_client = None
        self._configure()

    def _configure(self):
        """Configure OpenAI-compatible client"""
        # 聊天模型客户端（MiMo）
        api_key = settings.dashscope.DASHSCOPE_API_KEY
        base_url = settings.dashscope.DASHSCOPE_BASE_URL

        if api_key:
            self._client = OpenAI(
                api_key=api_key,
                base_url=base_url,
            )
            logger.info(f"LLM client configured: base_url={base_url}")
        else:
            logger.warning("LLM API key not configured")

        # Embedding 专用客户端（DeepSeek）
        embedding_api_key = settings.dashscope.embedding_api_key
        embedding_base_url = settings.dashscope.embedding_base_url

        if embedding_api_key:
            self._embedding_client = OpenAI(
                api_key=embedding_api_key,
                base_url=embedding_base_url,
            )
            logger.info(f"Embedding client configured: base_url={embedding_base_url}")
        else:
            logger.warning("Embedding API key not configured")

    def generate_text(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate text using LLM

        Args:
            prompt: User prompt
            model: Model name (default: from config)
            temperature: Temperature (default: from config)
            max_tokens: Max tokens (default: from config)
            system_prompt: System prompt for chat models
        """
        model = model or settings.dashscope.DASHSCOPE_MODEL
        temperature = temperature or settings.openai.OPENAI_TEMPERATURE
        max_tokens = max_tokens or settings.openai.OPENAI_MAX_TOKENS

        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = self._client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            content = response.choices[0].message.content
            logger.debug(f"Generated text with model {model}")
            return content

        except Exception as e:
            logger.error(f"Text generation failed: {str(e)}")
            raise

    def get_embedding(
        self,
        text: str,
        model: Optional[str] = None,
        **kwargs
    ) -> List[float]:
        """
        Get text embedding

        Args:
            text: Input text
            model: Embedding model name (default: from config)
        """
        model = model or settings.dashscope.DASHSCOPE_EMBEDDING_MODEL
        client = self._embedding_client or self._client

        try:
            response = client.embeddings.create(
                model=model,
                input=text,
            )

            embedding = response.data[0].embedding
            logger.debug(f"Generated embedding with model {model}")
            return embedding

        except Exception as e:
            logger.error(f"Embedding generation failed: {str(e)}")
            raise

    def get_embeddings_batch(
        self,
        texts: List[str],
        model: Optional[str] = None,
        batch_size: int = 25,  # API 限制最多 25 个
        **kwargs
    ) -> List[List[float]]:
        """
        Get embeddings for multiple texts

        Args:
            texts: List of input texts
            model: Embedding model name (default: from config)
            batch_size: 每批最多处理的数量（API 限制最多 25）
        """
        model = model or settings.dashscope.DASHSCOPE_EMBEDDING_MODEL
        client = self._embedding_client or self._client

        all_embeddings = []

        # 分批处理
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            try:
                response = client.embeddings.create(
                    model=model,
                    input=batch,
                )
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
                logger.debug(f"Generated {len(batch_embeddings)} embeddings (batch {i // batch_size + 1})")
            except Exception as e:
                logger.error(f"Batch embedding generation failed at batch {i // batch_size + 1}: {str(e)}")
                raise

        logger.debug(f"Total generated {len(all_embeddings)} embeddings with model {model}")
        return all_embeddings

    def chat(
        self,
        messages: List[dict],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ):
        """
        Chat completion

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name (default: from config)
            temperature: Temperature (default: from config)
            max_tokens: Max tokens (default: from config)
            stream: Enable streaming
        """
        model = model or settings.dashscope.DASHSCOPE_MODEL
        temperature = temperature or settings.openai.OPENAI_TEMPERATURE
        max_tokens = max_tokens or settings.openai.OPENAI_MAX_TOKENS

        try:
            if stream:
                return self._chat_stream(model, messages, temperature, max_tokens)

            response = self._client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False,
            )
            content = response.choices[0].message.content
            logger.debug(f"Chat completed with model {model}")
            return content

        except Exception as e:
            logger.error(f"Chat failed: {str(e)}")
            raise

    def _chat_stream(self, model, messages, temperature, max_tokens):
        """Streaming chat - separate method to avoid turning chat() into a generator"""
        try:
            response = self._client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"Stream chat failed: {str(e)}")
            raise


# Global client instance
dashscope_client = DashScopeClient()
