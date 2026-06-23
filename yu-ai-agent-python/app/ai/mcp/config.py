"""
MCP Configuration - MCP 服务配置加载

支持从 YAML 配置文件加载 MCP 服务器配置
"""
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field

from app.core.logging import get_logger

logger = get_logger(__name__)

# 配置文件目录
# __file__ = .../yu-ai-agent-python/app/ai/mcp/config.py
# 需要向上 4 级到达 yu-ai-agent-python，然后进入 config
CONFIG_DIR = Path(__file__).resolve().parent.parent.parent.parent / "config"


class MCPServerConfig(BaseModel):
    """MCP 服务器配置"""
    name: str = Field(description="服务名称")
    transport: str = Field(default="sse", description="连接方式: sse 或 stdio")

    # SSE 模式配置
    url: str = Field(default="", description="SSE 端点 URL")

    # Stdio 模式配置
    command: str = Field(default="", description="可执行命令（stdio 模式）")
    args: list[str] = Field(default_factory=list, description="命令参数（stdio 模式）")
    env: dict[str, str] = Field(default_factory=dict, description="环境变量")

    # 通用配置
    enabled: bool = Field(default=True, description="是否启用")
    timeout: int = Field(default=30, description="连接超时（秒）")


class MCPConfig(BaseModel):
    """MCP 配置"""
    enabled: bool = Field(default=True, description="是否启用 MCP")
    servers: list[MCPServerConfig] = Field(default_factory=list, description="MCP 服务器列表")


def load_mcp_config(config_file: str = "mcp.yaml") -> MCPConfig:
    """
    加载 MCP 配置

    优先级: 环境变量 MCP_ENABLED > 配置文件 > 默认值

    Args:
        config_file: 配置文件名

    Returns:
        MCPConfig: MCP 配置对象
    """
    import os

    config_path = CONFIG_DIR / config_file

    # 默认配置
    config_data = {"enabled": True, "servers": []}

    # 从 YAML 文件加载
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                yaml_data = yaml.safe_load(f) or {}

            # 提取 mcp 配置节
            if "mcp" in yaml_data:
                mcp_section = yaml_data["mcp"]
                if isinstance(mcp_section, dict):
                    config_data.update(mcp_section)

            logger.info(f"Loaded MCP config from: {config_path}")
        except Exception as e:
            logger.warning(f"Failed to load MCP config from {config_path}: {e}")
    else:
        logger.info(f"MCP config file not found: {config_path}, using defaults")

    # 环境变量覆盖
    env_enabled = os.getenv("MCP_ENABLED")
    if env_enabled is not None:
        config_data["enabled"] = env_enabled.lower() in ("true", "1", "yes")

    # 解析服务器配置
    servers = []
    for server_data in config_data.get("servers", []):
        if isinstance(server_data, dict):
            # 从环境变量读取 API Key
            env_vars = server_data.get("env", {})
            if isinstance(env_vars, dict):
                for key, value in list(env_vars.items()):
                    # 支持 ${ENV_VAR} 语法从环境变量读取
                    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                        env_name = value[2:-1]
                        env_value = os.getenv(env_name, "")
                        env_vars[key] = env_value

            server_config = MCPServerConfig(**server_data)
            servers.append(server_config)

    config = MCPConfig(enabled=config_data.get("enabled", True), servers=servers)

    logger.info(f"MCP config loaded: enabled={config.enabled}, servers={len(config.servers)}")
    for server in config.servers:
        logger.info(f"  - {server.name} ({server.transport}): {'enabled' if server.enabled else 'disabled'}")

    return config
