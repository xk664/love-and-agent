"""
Redis 客户端单例
提供异步Redis连接，用于工作记忆缓存
"""

import redis.asyncio as redis

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class RedisClient:
    """Redis异步客户端单例"""

    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def get_client(self) -> redis.Redis:
        """获取Redis客户端实例"""
        if self._client is None:
            try:
                self._client = redis.from_url(
                    settings.redis.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True
                )
                # 测试连接
                await self._client.ping()
                logger.info(f"Redis连接成功: {settings.redis.REDIS_HOST}:{settings.redis.REDIS_PORT}")
            except Exception as e:
                logger.error(f"Redis连接失败: {e}")
                self._client = None
                raise
        return self._client

    async def close(self):
        """关闭Redis连接"""
        if self._client:
            await self._client.close()
            self._client = None
            logger.info("Redis连接已关闭")

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            client = await self.get_client()
            await client.ping()
            return True
        except Exception:
            return False


# 全局Redis客户端实例
redis_client = RedisClient()
