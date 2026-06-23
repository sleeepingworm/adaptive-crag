# 模块说明书：工具能力层 (tools)

## 所属层级
能力工具层

## 目标目录
`adaptive_crag/tools/`

生成文件：
```
adaptive_crag/tools/
    __init__.py             # 导出所有工具
    vector_search.py        # 向量检索工具
    bm25_search.py          # BM25 检索工具
    hybrid_search.py        # 混合检索入口
    web_search.py           # 联网搜索工具
    sandbox_executor.py     # 沙箱执行工具
    citation_lookup.py      # 引用反查工具
    artifact_reader.py      # 产物读取工具
```

## 依赖模块

- **必须先生成**：`01_schema`、`02_config`、`03_ingestion`、`04_retrieval`
- **必须先生成**：`09_sandbox`（sandbox_executor.py 依赖）
- **必须先生成**：`10_reporting`（citation_lookup.py 依赖）

## 职责边界

**做：**
- 把底层能力（检索、搜索、执行、查询）封装成 Agent 可调用的工具函数
- 统一输入/输出为 dict 格式（LLM 友好）
- 所有工具返回结构化的结果，包含成功/失败状态
- 错误信息友好，方便 Agent 理解

**不做：**
- 不包含 LLM 调用逻辑
- 不做业务流程判断
- 不维护长期状态（每次调用独立）

## 核心接口

所有工具函数的签名遵循以下模式：

```python
def tool_name(params: dict) -> dict:
    """
    统一的工具调用接口。

    输入 params 结构:
        {"param1": value1, "param2": value2}

    输出 dict 结构:
        {
            "success": bool,
            "result": any,        # 工具执行结果
            "error": str | None,  # 错误信息
        }
    """
```

### hybrid_search.py

```python
def hybrid_search(params: dict) -> dict:
    """
    混合检索工具。供 Retriever Agent 调用。

    params:
        query: str              # 用户问题
        top_k: int = 10         # 召回数
        use_vector: bool = True
        use_bm25: bool = True

    返回:
        {
            "success": True,
            "result": {
                "query": str,
                "results": [{"chunk_id", "text", "score", "rerank_score", "page_num", "doc_id", "filename", "hit_reason"}],
                "total_found": int
            }
        }
    或:
        {
            "success": False,
            "error": "索引为空，请先上传文档",
            "result": None
        }
    """
```

### vector_search.py

```python
def vector_search(params: dict) -> dict:
    """
    纯向量检索工具。

    params:
        query: str
        top_k: int = 10

    返回同 hybrid_search.result 结构。
    """
```

### bm25_search.py

```python
def bm25_search(params: dict) -> dict:
    """
    纯 BM25 关键字检索工具。

    params:
        query: str
        top_k: int = 10

    返回同 hybrid_search.result 结构。
    """
```

### web_search.py

```python
def web_search(params: dict) -> dict:
    """
    联网搜索补偿工具。

    params:
        query: str
        max_results: int = 5

    返回:
        {
            "success": True,
            "result": {
                "query": str,
                "results": [
                    {
                        "title": str,
                        "url": str,
                        "snippet": str,
                        "content": str   # 页面摘要内容
                    }
                ],
                "source": "tavily" | "serper"
            }
        }

    如果未配置 API Key，返回 success=False, error="未配置联网搜索 API Key"
    """
```

### sandbox_executor.py

```python
def sandbox_executor(params: dict) -> dict:
    """
    代码沙箱执行工具。供 Code Execution Agent 调用。

    params:
        code: str                       # Python 代码
        data_files: list[str] = []      # 数据文件路径列表
        output_dir: str                 # 产物输出目录
        timeout: int = 60               # 超时秒数

    返回:
        {
            "success": True,
            "result": {
                "stdout": str,
                "stderr": str,
                "exit_code": 0,
                "generated_files": ["path/to/chart1.png", ...],
                "execution_time_ms": 1234
            }
        }
    或:
        {
            "success": False,
            "error": str,
            "result": {
                "stdout": str,
                "stderr": str,
                "traceback": str,       # 完整异常回溯
                "exit_code": 1,
                "generated_files": []
            }
        }
    """
```

### citation_lookup.py

```python
def citation_lookup(params: dict) -> dict:
    """
    引用反查工具。供 Report Agent 和 Citation Validator 调用。

    params:
        chunk_id: str
        doc_id: str | None = None

    返回:
        {
            "success": True,
            "result": {
                "chunk_id": str,
                "doc_id": str,
                "filename": str,
                "page_num": int | None,
                "text_snippet": str,     # chunk 原文片段
                "file_path": str
            }
        }
    """
```

### artifact_reader.py

```python
def artifact_reader(params: dict) -> dict:
    """
    产物读取工具。供 Report Agent 调用。

    params:
        task_id: str
        artifact_type: str   # "chart" | "log" | "report" | "data"
        path: str            # 产物路径

    返回:
        {
            "success": True,
            "result": {
                "type": str,
                "content": str,      # 文本内容 或 base64 图片
                "path": str
            }
        }
    """
```

## 工具注册表（用于 Agent 系统提示词）

所有工具统一注册，每个工具包含：
- `name`：工具名
- `description`：简短的功能描述
- `parameters`：参数 JSON Schema

示例注册表结构（在 `__init__.py` 中）：

```python
TOOL_REGISTRY = {
    "hybrid_search": {
        "name": "hybrid_search",
        "description": "从本地知识库同时使用向量检索和关键词检索召回相关文献片段。适合需要快速找到相关文献段落的问题。",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键词或问题"},
                "top_k": {"type": "integer", "description": "返回结果数量", "default": 10}
            },
            "required": ["query"]
        }
    },
    "web_search": {
        "name": "web_search",
        "description": "当本地知识库找不到足够信息时，从互联网搜索最新信息。适合当前事件、新技术、本地材料缺失的场景。",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键词"},
                "max_results": {"type": "integer", "description": "返回结果数量", "default": 5}
            },
            "required": ["query"]
        }
    },
    "sandbox_executor": {
        "name": "sandbox_executor",
        "description": "在隔离沙箱中执行 Python 数据分析代码。支持 pandas、numpy、matplotlib、seaborn 等库。代码运行有 60 秒超时限制。",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "要执行的 Python 代码"},
                "data_files": {"type": "array", "items": {"type": "string"}, "description": "数据文件路径"},
                "output_dir": {"type": "string", "description": "输出目录"}
            },
            "required": ["code", "output_dir"]
        }
    },
    # ... 其余工具同上
}
```

## 实现约束

1. **纯函数**：每个工具内部不维护状态，每次调用从存储层重新获取
2. **错误不抛异常**：所有异常在工具内部 catch，转为 `{"success": False, "error": "..."}`
3. **参数校验**：对必填参数做显式检查，返回友好错误
4. **LLM 友好**：`description` 用中文写，格式自然，让 LangGraph Agent 能理解什么场景调用
5. **工具之间不互相调用**：每个工具独立，复杂逻辑由 LangGraph 编排

## 与上下游模块的对接

- **上游调用方**：`LangGraph` 工作流中的各 Agent 节点
- **下游依赖方**：各底层封装模块（retrieval, sandbox, reporting）
- **数据流向**：`Agent -> tools/{工具} -> 底层模块 -> Agent`

## 测试要点

- 每个工具在有参数、缺参数、错误参数时行为正确
- hybrid_search 在索引为空时返回 success=False
- web_search 在没有 API Key 时返回 success=False
- sandbox_executor 能正确捕获 traceback
- 所有工具返回值结构一致（包含 success/result/error）