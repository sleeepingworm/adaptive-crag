# Adaptive CRAG 🧠

**自适应修正型检索增强生成系统** (Adaptive Corrective Retrieval-Augmented Generation)

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    页面交互层 (Streamlit)                     │
│  上传页面 | 任务看板 | 报告页面 | Benchmark 页面              │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                   应用编排层 (application)                    │
│  会话管理 | 任务编排 | 产物管理                              │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                  Agent 工作流层 (LangGraph)                   │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌───────────────┐ │
│  │ Router  │→│Retrieve │→│  Grade  │→│  Analyze      │ │
│  └─────────┘  └─────────┘  └────┬────┘  └───────┬───────┘ │
│                                  │               │         │
│  ┌─────────┐  ┌─────────┐  ┌───▼────┐  ┌───────▼───────┐ │
│  │Validate │←│ Report  │←│Execute │←│Code Write    │ │
│  └─────────┘  └─────────┘  └───┬────┘  └───────────────┘ │
│                                │                          │
│                          ┌─────▼─────┐                    │
│                          │  Repair   │                    │
│                          └───────────┘                    │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    能力工具层 (tools)                         │
│  向量检索 | BM25检索 | 联网搜索 | 沙箱执行 | 引用查询        │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                   数据与产物层                                 │
│  文件解析(Ingestion) | 混合检索(Retrieval)                    │
│  沙箱执行(Sandbox) | 报告构建(Reporting)                     │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                 跨模块基础层                                   │
│  共享数据结构(Schema) | 配置管理(Config)                     │
└─────────────────────────────────────────────────────────────┘
```

## 核心模块

| 模块 | 目录 | 职责 |
|------|------|------|
| **Schema** | `adaptive_crag/schema/` | 所有数据类定义（Document, Chunk, GraphState 等） |
| **Config** | `adaptive_crag/config/` | 配置管理，支持环境变量覆盖 |
| **Ingestion** | `adaptive_crag/ingestion/` | 文件解析（PDF/TXT/MD/CSV/Excel），文本清洗，切片 |
| **Retrieval** | `adaptive_crag/retrieval/` | 向量检索(ChromaDB) + BM25 + RRF融合 + Rerank |
| **Sandbox** | `adaptive_crag/sandbox/` | 代码沙箱执行，安全检查，错误解析 |
| **Tools** | `adaptive_crag/tools/` | 工具函数封装（检索、搜索、执行、查询） |
| **Agents** | `adaptive_crag/agents/` | LLM Agent 封装（Router/Grader/Analyzer/Repair等） |
| **Graph** | `adaptive_crag/graph/` | LangGraph 工作流状态机 |
| **Application** | `adaptive_crag/application/` | 会话管理、任务编排、产物管理 |
| **Reporting** | `adaptive_crag/reporting/` | 报告构建、引用校验、Markdown 格式化 |
| **Evaluation** | `adaptive_crag/evaluation/` | Benchmark 评测（测试集、跑分引擎、评分器） |
| **UI** | `app/` | Streamlit 前端页面 |

## 安装

```bash
# 克隆项目
git clone https://github.com/example/adaptive-crag.git
cd adaptive-crag

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 安装依赖
pip install -e .
pip install -e ".[dev]"   # 包含开发工具
```

## 配置

通过环境变量配置：

```bash
# LLM 配置
export CRAG_API_KEY="your-api-key"
export CRAG_LLM_MODEL="gpt-4o"
export CRAG_LLM_PROVIDER="openai"  # 或 "ollama"

# Ollama 配置
export CRAG_LLM_PROVIDER="ollama"
export CRAG_LLM_API_BASE="http://localhost:11434"
export CRAG_LLM_MODEL="qwen2.5:7b"

# 检索配置
export CRAG_TOP_K=10
export CRAG_BM25_WEIGHT=0.3
export CRAG_VECTOR_WEIGHT=0.7

# 联网搜索
export CRAG_WEB_SEARCH_KEY="your-tavily-key"
export CRAG_WEB_SEARCH_ENABLED=true

# 调试
export CRAG_DEBUG=true
```

## 启动

```bash
# Web UI 模式（推荐）
python main.py

# 或直接启动 Streamlit
streamlit run app/main.py

# CLI 模式（查看配置）
python main.py --cli
```

## 工作流

1. **上传文件**：支持 PDF、TXT、Markdown、CSV、Excel
2. **输入问题**：用户输入研究问题或分析需求
3. **任务路由**：Router Agent 拆解任务
4. **混合检索**：向量 + BM25 + Rerank
5. **证据评估**：Grader Agent 判断证据是否充足
6. **联网补偿**：不足时自动联网搜索
7. **代码执行**：沙箱执行数据分析代码
8. **自修复**：代码失败自动修复重试
9. **报告生成**：整合所有结果生成 Markdown 报告
10. **引用校验**：检查结论是否有源可循

## 项目结构

```
adaptive-crag/
├── adaptive_crag/           # 核心 Python 包
│   ├── schema/              # 共享数据结构
│   ├── config/              # 配置管理
│   ├── ingestion/           # 文件解析与索引
│   ├── retrieval/           # 混合检索
│   ├── tools/               # 工具能力层
│   ├── sandbox/             # 沙箱执行层
│   ├── agents/              # Agent 能力封装
│   ├── graph/               # LangGraph 工作流
│   │   └── nodes/           # 工作流节点
│   ├── application/         # 应用编排层
│   ├── reporting/           # 报告与引用层
│   └── evaluation/          # Benchmark 评测
├── app/                     # Streamlit 前端
│   ├── main.py              # 主入口
│   └── pages/               # 页面模块
├── data/                    # 数据目录
│   ├── uploads/             # 上传文件
│   ├── indexes/             # 检索索引
│   └── artifacts/           # 任务产物
├── tests/                   # 测试
│   └── test_all.py
├── main.py                  # 系统入口
├── pyproject.toml           # 项目配置
└── README.md                # 本文件
```
