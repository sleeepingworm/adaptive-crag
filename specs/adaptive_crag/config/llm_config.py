"""
LLM 供应商配置，支持 OpenAI 和 Ollama 两种模式。
"""

import os
from dataclasses import dataclass
from enum import Enum


class LLMProvider(str, Enum):
    OPENAI = "openai"
    OLLAMA = "ollama"
    AZURE = "azure"
    OPENSOURCE = "opensource"


@dataclass
class LLMConfig:
    """LLM 调用配置"""
    provider: LLMProvider = LLMProvider.OPENAI
    model_name: str = "gpt-4o"
    api_base: str | None = None
    api_key: str | None = None
    temperature: float = 0.1
    max_tokens: int = 4096
    timeout_seconds: int = 60

    @classmethod
    def from_env(cls) -> "LLMConfig":
        """从环境变量加载 LLM 配置"""
        provider_name = os.environ.get("CRAG_LLM_PROVIDER", "openai").lower()
        try:
            provider = LLMProvider(provider_name)
        except ValueError:
            provider = LLMProvider.OPENAI

        return cls(
            provider=provider,
            model_name=os.environ.get("CRAG_LLM_MODEL", "gpt-4o"),
            api_base=os.environ.get("CRAG_LLM_API_BASE"),
            api_key=os.environ.get("CRAG_API_KEY") or os.environ.get("OPENAI_API_KEY"),
            temperature=float(os.environ.get("CRAG_LLM_TEMPERATURE", "0.1")),
            max_tokens=int(os.environ.get("CRAG_LLM_MAX_TOKENS", "4096")),
            timeout_seconds=int(os.environ.get("CRAG_LLM_TIMEOUT", "60")),
        )


@dataclass
class EmbeddingConfig:
    """Embedding 模型配置"""
    model_name: str = "BAAI/bge-small-zh-v1.5"
    device: str = "cpu"
    batch_size: int = 32
    normalize: bool = True

    @classmethod
    def from_env(cls) -> "EmbeddingConfig":
        return cls(
            model_name=os.environ.get("CRAG_EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5"),
            device=os.environ.get("CRAG_EMBEDDING_DEVICE", "cpu"),
            batch_size=int(os.environ.get("CRAG_EMBEDDING_BATCH_SIZE", "32")),
            normalize=os.environ.get("CRAG_EMBEDDING_NORMALIZE", "true").lower() in ("true", "1"),
        )


def load_llm_config() -> LLMConfig:
    """加载 LLM 配置的便捷函数"""
    return LLMConfig.from_env()


def load_embedding_config() -> EmbeddingConfig:
    """加载 Embedding 配置的便捷函数"""
    return EmbeddingConfig.from_env()
