"""
Configuration Management
Hybrid approach: Environment Variables + YAML Config Files
Priority: Environment Variables > Config File > Default Values
"""
import os
from pathlib import Path
from typing import Optional

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings


# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = BASE_DIR / "config"


def load_yaml_config(config_name: str = "config.yaml") -> dict:
    """Load YAML configuration file"""
    env = os.getenv("APP_ENV", "dev")
    config_file = CONFIG_DIR / f"{config_name.replace('.yaml', '')}-{env}.yaml"

    if not config_file.exists():
        config_file = CONFIG_DIR / config_name

    if not config_file.exists():
        return {}

    with open(config_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


class AppSettings(BaseSettings):
    """Application Settings"""
    APP_NAME: str = Field(default="Yu AI Agent")
    APP_VERSION: str = Field(default="0.1.0")
    DEBUG: bool = Field(default=False)
    APP_ENV: str = Field(default="dev")
    APP_HOST: str = Field(default="0.0.0.0")
    APP_PORT: int = Field(default=8000)

    class Config:
        env_prefix = ""
        env_file = ".env"
        env_file_encoding = "utf-8"


class ServerSettings(BaseSettings):
    """Server Settings"""
    SERVER_IP: str = Field(default="106.53.178.125")

    class Config:
        env_prefix = "SERVER_"
        env_file = ".env"
        env_file_encoding = "utf-8"


class DatabaseSettings(BaseSettings):
    """Database Settings (MySQL)"""
    DB_HOST: str = Field(default="106.53.178.125")
    DB_PORT: int = Field(default=13306)
    DB_USER: str = Field(default="root")
    DB_PASSWORD: str = Field(default="123456")
    DB_NAME: str = Field(default="yu_agent")

    # Pool settings
    DB_POOL_SIZE: int = Field(default=10)
    DB_MAX_OVERFLOW: int = Field(default=20)
    DB_POOL_TIMEOUT: int = Field(default=30)

    @property
    def DATABASE_URL(self) -> str:
        """Async MySQL URL (aiomysql)"""
        return f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def DATABASE_URL_SYNC(self) -> str:
        """Sync MySQL URL"""
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        env_prefix = "DB_"
        env_file = ".env"
        env_file_encoding = "utf-8"


class PgVectorSettings(BaseSettings):
    """PgVector Settings (PostgreSQL)"""
    PGVECTOR_HOST: str = Field(default="106.53.178.125")
    PGVECTOR_PORT: int = Field(default=5432)
    PGVECTOR_USER: str = Field(default="postgres")
    PGVECTOR_PASSWORD: str = Field(default="")
    PGVECTOR_DATABASE: str = Field(default="yu_agent")
    PGVECTOR_COLLECTION: str = Field(default="embeddings")
    PGVECTOR_DIMENSION: int = Field(default=1536)

    @property
    def connection_string(self) -> str:
        return f"postgresql+asyncpg://{self.PGVECTOR_USER}:{self.PGVECTOR_PASSWORD}@{self.PGVECTOR_HOST}:{self.PGVECTOR_PORT}/{self.PGVECTOR_DATABASE}"

    class Config:
        env_prefix = "PGVECTOR_"
        env_file = ".env"
        env_file_encoding = "utf-8"


class RedisSettings(BaseSettings):
    """Redis Settings"""
    REDIS_HOST: str = Field(default="106.53.178.125")
    REDIS_PORT: int = Field(default=16379)
    REDIS_DB: int = Field(default=0)
    REDIS_PASSWORD: str = Field(default="")

    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    class Config:
        env_prefix = "REDIS_"
        env_file = ".env"
        env_file_encoding = "utf-8"


class DashScopeSettings(BaseSettings):
    """DashScope API Settings"""
    DASHSCOPE_API_KEY: str = Field(default="")
    DASHSCOPE_MODEL: str = Field(default="qwen-turbo")
    DASHSCOPE_EMBEDDING_MODEL: str = Field(default="text-embedding-v2")
    DASHSCOPE_BASE_URL: str = Field(default="https://dashscope.aliyuncs.com/api/v1")

    class Config:
        env_prefix = "DASHSCOPE_"
        env_file = ".env"
        env_file_encoding = "utf-8"


class OpenAISettings(BaseSettings):
    """OpenAI API Settings"""
    OPENAI_API_KEY: str = Field(default="")
    OPENAI_API_BASE: str = Field(default="https://api.openai.com/v1")
    OPENAI_MODEL: str = Field(default="gpt-4")
    OPENAI_TEMPERATURE: float = Field(default=0.7)
    OPENAI_MAX_TOKENS: int = Field(default=2000)

    class Config:
        env_prefix = "OPENAI_"
        env_file = ".env"
        env_file_encoding = "utf-8"


class AuthSettings(BaseSettings):
    """Internal Authentication Settings"""
    INTERNAL_TOKEN: str = Field(default="")
    TOKEN_EXPIRE_MINUTES: int = Field(default=60)

    class Config:
        env_prefix = "AUTH_"
        env_file = ".env"
        env_file_encoding = "utf-8"


class RAGSettings(BaseSettings):
    """RAG Settings"""
    RAG_CHUNK_SIZE: int = Field(default=500)
    RAG_CHUNK_OVERLAP: int = Field(default=50)
    RAG_TOP_K: int = Field(default=5)
    RAG_SIMILARITY_THRESHOLD: float = Field(default=0.7)

    class Config:
        env_prefix = "RAG_"
        env_file = ".env"
        env_file_encoding = "utf-8"


class Settings:
    """
    Main Settings Manager
    Combines all settings with hybrid configuration approach
    """
    def __init__(self):
        self.app = AppSettings()
        self.server = ServerSettings()
        self.database = DatabaseSettings()
        self.pgvector = PgVectorSettings()
        self.redis = RedisSettings()
        self.dashscope = DashScopeSettings()
        self.openai = OpenAISettings()
        self.auth = AuthSettings()
        self.rag = RAGSettings()

        # Load and apply YAML overrides
        self._apply_yaml_overrides()

    def _apply_yaml_overrides(self):
        """Apply YAML config file overrides where env vars are not set"""
        yaml_config = load_yaml_config()

        if not yaml_config:
            return

        # Server overrides
        if yaml_config.get("server"):
            server_config = yaml_config["server"]
            if not os.getenv("SERVER_IP") and "ip" in server_config:
                self.server.SERVER_IP = server_config["ip"]

        # Database overrides
        if yaml_config.get("database"):
            db_config = yaml_config["database"]
            if not os.getenv("DB_HOST") and "host" in db_config:
                self.database.DB_HOST = db_config["host"]
            if not os.getenv("DB_PORT") and "port" in db_config:
                self.database.DB_PORT = db_config["port"]
            if not os.getenv("DB_USER") and "user" in db_config:
                self.database.DB_USER = db_config["user"]
            if not os.getenv("DB_PASSWORD") and "password" in db_config:
                self.database.DB_PASSWORD = db_config["password"]
            if not os.getenv("DB_NAME") and "name" in db_config:
                self.database.DB_NAME = db_config["name"]

        # PgVector overrides
        if yaml_config.get("pgvector"):
            pv_config = yaml_config["pgvector"]
            if not os.getenv("PGVECTOR_HOST") and "host" in pv_config:
                self.pgvector.PGVECTOR_HOST = pv_config["host"]
            if not os.getenv("PGVECTOR_PORT") and "port" in pv_config:
                self.pgvector.PGVECTOR_PORT = pv_config["port"]
            if not os.getenv("PGVECTOR_USER") and "user" in pv_config:
                self.pgvector.PGVECTOR_USER = pv_config["user"]
            if not os.getenv("PGVECTOR_PASSWORD") and "password" in pv_config:
                self.pgvector.PGVECTOR_PASSWORD = pv_config["password"]
            if not os.getenv("PGVECTOR_DATABASE") and "database" in pv_config:
                self.pgvector.PGVECTOR_DATABASE = pv_config["database"]
            if not os.getenv("PGVECTOR_COLLECTION") and "collection" in pv_config:
                self.pgvector.PGVECTOR_COLLECTION = pv_config["collection"]
            if not os.getenv("PGVECTOR_DIMENSION") and "dimension" in pv_config:
                self.pgvector.PGVECTOR_DIMENSION = pv_config["dimension"]

        # Redis overrides
        if yaml_config.get("redis"):
            redis_config = yaml_config["redis"]
            if not os.getenv("REDIS_HOST") and "host" in redis_config:
                self.redis.REDIS_HOST = redis_config["host"]
            if not os.getenv("REDIS_PORT") and "port" in redis_config:
                self.redis.REDIS_PORT = redis_config["port"]
            if not os.getenv("REDIS_DB") and "db" in redis_config:
                self.redis.REDIS_DB = redis_config["db"]
            if not os.getenv("REDIS_PASSWORD") and "password" in redis_config:
                self.redis.REDIS_PASSWORD = redis_config["password"]

        # DashScope overrides
        if yaml_config.get("dashscope"):
            ds_config = yaml_config["dashscope"]
            if not os.getenv("DASHSCOPE_MODEL") and "model" in ds_config:
                self.dashscope.DASHSCOPE_MODEL = ds_config["model"]
            if not os.getenv("DASHSCOPE_EMBEDDING_MODEL") and "embedding_model" in ds_config:
                self.dashscope.DASHSCOPE_EMBEDDING_MODEL = ds_config["embedding_model"]

        # RAG overrides
        if yaml_config.get("rag"):
            rag_config = yaml_config["rag"]
            if not os.getenv("RAG_CHUNK_SIZE") and "chunk_size" in rag_config:
                self.rag.RAG_CHUNK_SIZE = rag_config["chunk_size"]
            if not os.getenv("RAG_CHUNK_OVERLAP") and "chunk_overlap" in rag_config:
                self.rag.RAG_CHUNK_OVERLAP = rag_config["chunk_overlap"]
            if not os.getenv("RAG_TOP_K") and "top_k" in rag_config:
                self.rag.RAG_TOP_K = rag_config["top_k"]

    def get_db_url(self, async_mode: bool = True) -> str:
        """Get database URL"""
        if async_mode:
            return self.database.DATABASE_URL
        return self.database.DATABASE_URL_SYNC


# Global settings instance
settings = Settings()
