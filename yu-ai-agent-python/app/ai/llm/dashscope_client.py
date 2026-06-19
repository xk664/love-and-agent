"""
DashScope API Client Configuration
"""
from typing import List, Optional

import dashscope
from dashscope import TextEmbedding, Generation

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class DashScopeClient:
    """
    DashScope API Client
    Handles LLM and Embedding operations via DashScope
    """

    def __init__(self):
        self._configure()

    def _configure(self):
        """Configure DashScope API"""
        if settings.dashscope.DASHSCOPE_API_KEY:
            dashscope.api_key = settings.dashscope.DASHSCOPE_API_KEY
            logger.info("DashScope API configured")
        else:
            logger.warning("DashScope API key not configured")

    async def generate_text(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate text using DashScope LLM

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

            response = Generation.call(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                result_format="message",
                **kwargs
            )

            if response.status_code == 200:
                content = response.output.choices[0].message.content
                logger.debug(f"Generated text with model {model}")
                return content
            else:
                error_msg = f"DashScope API error: {response.code} - {response.message}"
                logger.error(error_msg)
                raise Exception(error_msg)

        except Exception as e:
            logger.error(f"Text generation failed: {str(e)}")
            raise

    async def get_embedding(
        self,
        text: str,
        model: Optional[str] = None,
        **kwargs
    ) -> List[float]:
        """
        Get text embedding using DashScope

        Args:
            text: Input text
            model: Embedding model name (default: from config)
        """
        model = model or settings.dashscope.DASHSCOPE_EMBEDDING_MODEL

        try:
            response = TextEmbedding.call(
                model=model,
                input=text,
                **kwargs
            )

            if response.status_code == 200:
                embedding = response.output["embeddings"][0]["embedding"]
                logger.debug(f"Generated embedding with model {model}")
                return embedding
            else:
                error_msg = f"DashScope embedding error: {response.code} - {response.message}"
                logger.error(error_msg)
                raise Exception(error_msg)

        except Exception as e:
            logger.error(f"Embedding generation failed: {str(e)}")
            raise

    async def get_embeddings_batch(
        self,
        texts: List[str],
        model: Optional[str] = None,
        **kwargs
    ) -> List[List[float]]:
        """
        Get embeddings for multiple texts

        Args:
            texts: List of input texts
            model: Embedding model name (default: from config)
        """
        model = model or settings.dashscope.DASHSCOPE_EMBEDDING_MODEL

        try:
            response = TextEmbedding.call(
                model=model,
                input=texts,
                **kwargs
            )

            if response.status_code == 200:
                embeddings = [item["embedding"] for item in response.output["embeddings"]]
                logger.debug(f"Generated {len(embeddings)} embeddings with model {model}")
                return embeddings
            else:
                error_msg = f"DashScope batch embedding error: {response.code} - {response.message}"
                logger.error(error_msg)
                raise Exception(error_msg)

        except Exception as e:
            logger.error(f"Batch embedding generation failed: {str(e)}")
            raise

    async def chat(
        self,
        messages: List[dict],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ):
        """
        Chat completion using DashScope

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
            response = Generation.call(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                result_format="message",
                stream=stream,
                **kwargs
            )

            if stream:
                # Return generator for streaming
                for chunk in response:
                    if chunk.status_code == 200:
                        content = chunk.output.choices[0].message.content
                        yield content
                    else:
                        raise Exception(f"Stream error: {chunk.code}")
            else:
                if response.status_code == 200:
                    content = response.output.choices[0].message.content
                    logger.debug(f"Chat completed with model {model}")
                    return content
                else:
                    error_msg = f"DashScope chat error: {response.code} - {response.message}"
                    logger.error(error_msg)
                    raise Exception(error_msg)

        except Exception as e:
            logger.error(f"Chat failed: {str(e)}")
            raise


# Global DashScope client instance
dashscope_client = DashScopeClient()
