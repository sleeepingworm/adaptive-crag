"""
全局配置类，集中管理所有可配置项。
支持环境变量覆盖，路径自动创建。
"""

import os
from dataclasses import dataclass, field


@dataclass
class PathsConfig:
    """路径相关配置"""
    project_root: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    upload_dir: str = ""
    index_dir: str = ""
    artifact_dir: str = ""
    chroma_persist_dir: str = ""

    def __post_init__(self):
        if not self.upload_dir:
            self.upload_dir = os.path.join(self.project_root, "data", "uploads")
        if not self.index_dir:
            self.index_dir = os.path.join(self.project_root, "data", "indexes")
        if not self.artifact_dir:
            self.artifact_dir = os.path.join(self.project_root, "data", "artifacts")
        if not self.chroma_persist_dir:
            self.chroma_persist_dir = os.path.join(self.index_dir, "chroma")


@dataclass
class RetrievalConfig:
    """检索相关配置"""
    top_k: int = 10
    bm25_weight: float = 0.3
    vector_weight: float = 0.7
    rerank_top_k: int = 5
    chunk_max_tokens: int = 512
    chunk_overlap_tokens: int = 64
    min_score_threshold: float = 0.3


@dataclass
class SandboxConfig:
    """沙箱执行配置"""
    timeout_seconds: int = 60
    max_output_chars: int = 10000
    allowed_packages: list[str] = field(default_factory=lambda: [
        "pandas", "numpy", "matplotlib", "seaborn",
        "scipy", "statsmodels", "sklearn", "json",
        "csv", "datetime", "math", "collections",
        "itertools", "re", "typing", "random",
        "decimal", "fractions", "statistics",
    ])
    restricted_modules: list[str] = field(default_factory=lambda: [
        "os", "subprocess", "sys", "shutil", "glob",
        "pathlib", "importlib", "ctypes", "socket", "requests",
        "multiprocessing", "threading", "signal", "fcntl",
        "ptty", "tty", "termios",
    ])


@dataclass
class SelfCorrectionConfig:
    """自修复配置"""
    max_retries: int = 3
    min_retry_interval_ms: int = 500
    enable_traceback_parsing: bool = True


@dataclass
class WebSearchConfig:
    """联网搜索配置"""
    enabled: bool = False
    provider: str = "tavily"
    max_results: int = 5
    api_key: str = ""


@dataclass
class AppConfig:
    """全局应用配置"""
    paths: PathsConfig = field(default_factory=PathsConfig)
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)
    sandbox: SandboxConfig = field(default_factory=SandboxConfig)
    self_correction: SelfCorrectionConfig = field(default_factory=SelfCorrectionConfig)
    web_search: WebSearchConfig = field(default_factory=WebSearchConfig)
    debug: bool = False
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "AppConfig":
        """从环境变量和默认值加载配置"""
        config = cls()

        # 环境变量覆盖
        env_map = {
            "CRAG_DEBUG": ("debug", lambda v: v.lower() in ("true", "1", "yes")),
            "CRAG_LOG_LEVEL": ("log_level", lambda v: v.upper()),
            "CRAG_TOP_K": ("retrieval", "top_k", int),
            "CRAG_BM25_WEIGHT": ("retrieval", "bm25_weight", float),
            "CRAG_VECTOR_WEIGHT": ("retrieval", "vector_weight", float),
            "CRAG_TIMEOUT": ("sandbox", "timeout_seconds", int),
            "CRAG_MAX_RETRIES": ("self_correction", "max_retries", int),
            "CRAG_WEB_SEARCH_ENABLED": ("web_search", "enabled", lambda v: v.lower() in ("true", "1", "yes")),
            "CRAG_WEB_SEARCH_KEY": ("web_search", "api_key", str),
        }

        for env_key, mapping in env_map.items():
            value = os.environ.get(env_key)
            if value is not None:
                try:
                    if len(mapping) == 2:
                        attr, transform = mapping
                        setattr(config, attr, transform(value))
                    elif len(mapping) == 3:
                        section, attr, transform = mapping
                        section_obj = getattr(config, section)
                        setattr(section_obj, attr, transform(value))
                except (ValueError, TypeError):
                    pass  # 环境变量值不合法时忽略

        # 确保目录存在
        for dir_path in [
            config.paths.upload_dir,
            config.paths.index_dir,
            config.paths.artifact_dir,
            config.paths.chroma_persist_dir,
        ]:
            os.makedirs(dir_path, exist_ok=True)

        return config


def load_config() -> AppConfig:
    """加载全局配置的便捷函数"""
    return AppConfig.from_env()
