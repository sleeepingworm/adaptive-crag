# 模块说明书：配置层 (config)

## 所属层级
跨模块基础层

## 目标目录
`adaptive_crag/config/`

生成文件：
```
adaptive_crag/config/
    __init__.py            # 导出配置工厂函数
    settings.py            # 全局配置类
    llm_config.py          # LLM 供应商配置
```

## 依赖模块

- **必须先生成**：`01_schema`（虽然 config 不直接 import schema，但配置项的 key 必须与 schema 的预期一致）

## 职责边界

**做：**
- 集中管理所有可配置项：路径、API Key、模型名、超时、阈值
- 提供统一的配置加载方式
- 支持环境变量覆盖
- 为每个工具/Agent 提供默认参数

**不做：**
- 不做任何业务逻辑
- 不处理文件读写（只存路径）
- 不导入 schema 以外的模块

## 核心文件与职责

### settings.py - 全局配置

```python
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class PathsConfig:
    project_root: str              # 项目根目录
    upload_dir: str                # 上传文件目录（默认 data/uploads）
    index_dir: str                 # 索引目录（默认 data/indexes）
    artifact_dir: str              # 产物目录（默认 data/artifacts）
    chroma_persist_dir: str        # ChromaDB 持久化目录

@dataclass
class RetrievalConfig:
    top_k: int = 10                # 召回 top-k
    bm25_weight: float = 0.3      # BM25 融合权重
    vector_weight: float = 0.7    # 向量检索融合权重
    rerank_top_k: int = 5         # Rerank 后保留条数
    chunk_max_tokens: int = 512   # 切片最大 token
    chunk_overlap_tokens: int = 64  # 切片重叠 token
    min_score_threshold: float = 0.3  # 最低召回分数

@dataclass
class SandboxConfig:
    timeout_seconds: int = 60     # 代码执行超时
    max_output_chars: int = 10000 # 最大输出字符
    allowed_packages: list[str] = field(default_factory=lambda: [
        "pandas", "numpy", "matplotlib", "seaborn",
        "scipy", "statsmodels", "sklearn", "json",
        "csv", "datetime", "math", "collections",
        "itertools", "re", "typing"
    ])
    restricted_modules: list[str] = field(default_factory=lambda: [
        "os", "subprocess", "sys", "shutil", "glob",
        "pathlib", "importlib", "builtins.eval",
        "builtins.exec", "ctypes", "socket", "requests"
    ])

@dataclass
class SelfCorrectionConfig:
    max_retries: int = 3           # 最大修复次数
    min_retry_interval_ms: int = 500   # 重试间隔
    enable_traceback_parsing: bool = True

@dataclass
class WebSearchConfig:
    enabled: bool = False           # 默认关闭，需要 API Key
    provider: str = "tavily"        # tavily 或 serper
    max_results: int = 5
    api_key: str = ""               # 从环境变量读取

@dataclass
class AppConfig:
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
        ...
```

### llm_config.py - LLM 供应商配置

```python
from dataclasses import dataclass

class LLMProvider(str, Enum):
    OPENAI = "openai"
    OLLAMA = "ollama"
    AZURE = "azure"
    OPENSOURCE = "opensource"  # 兼容 openai 协议的其他模型

@dataclass
class LLMConfig:
    provider: LLMProvider
    model_name: str                      # 如 gpt-4o, qwen2.5:7b
    api_base: str | None = None          # 自定义 endpoint
    api_key: str | None = None           # 从环境变量读取
    temperature: float = 0.1
    max_tokens: int = 4096
    timeout_seconds: int = 60

@dataclass
class EmbeddingConfig:
    model_name: str = "BAAI/bge-small-zh-v1.5"
    device: str = "cpu"                  # cpu 或 cuda
    batch_size: int = 32
    normalize: bool = True
```

## 配置加载方式

```python
def load_config() -> AppConfig:
    """加载全局配置，支持环境变量覆盖"""
    ...

def load_llm_config() -> LLMConfig:
    """加载 LLM 配置"""
    ...

def load_embedding_config() -> EmbeddingConfig:
    """加载 Embedding 配置"""
    ...
```

环境变量映射规则（示例）：
```
CRAG_API_KEY -> LLMConfig.api_key
CRAG_WEB_SEARCH_KEY -> WebSearchConfig.api_key
CRAG_LLM_MODEL -> LLMConfig.model_name
CRAG_LLM_PROVIDER -> LLMConfig.provider
```

## 实现约束

1. `from_env()` 方法优先读环境变量，不存在用默认值
2. 路径配置在加载后自动 `os.makedirs(exist_ok=True)` 确保目录存在
3. 所有配置为纯数据类，可 JSON dump 做日志
4. 配置文件本身不引入 `dotenv`（由入口脚本决定）

## 与上下游模块的对接

- **消费方**：所有模块通过 `from adaptive_crag.config import load_config` 获取配置
- **对接方式**：`config = load_config()` 后直接取字段 `config.retrieval.top_k`

## 测试要点

- 所有配置有合理的默认值
- 环境变量能正确覆盖默认值
- 不存在的环境变量不会报错
- 路径配置能自动创建目录
- 沙箱黑名单和白名单设置正确