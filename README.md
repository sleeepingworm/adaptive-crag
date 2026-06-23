# Adaptive CRAG

**自适应修正型检索增强生成系统**

基于 **LangGraph** + **ChromaDB** + **LLM** 的智能文献分析与报告生成平台。

## 🧠 系统架构

```
用户上传文件 → Ingest(解析/切片) → Index(向量+BM25) → 
Retrieve(混合检索) → Grade(证据评估) → Analyze(分析规划) →
Code Write(代码生成) → Execute(沙箱执行) → Report(报告生成) →
Validate(引用校验) → 最终报告
```

### 核心特性

- **📚 混合检索**：向量语义检索 + BM25 关键词检索 + RRF 融合排序
- **🔍 证据评级**：LLM 判断证据是否充足，不足时自动联网补偿
- **💻 代码沙箱**：隔离安全执行数据分析代码，自动修复错误
- **📝 报告生成**：结构化 Markdown 报告，含引用标注和图表嵌入
- **✅ 引用校验**：自动检查每项结论的原始来源

## 📁 项目结构

```
adaptive_crag/             # 主代码包
├── schema/                # 共享数据类定义
├── config/                # 配置管理
├── ingestion/             # 文件解析与切片
├── retrieval/             # 向量+BM25混合检索
├── sandbox/               # 代码沙箱执行
├── tools/                 # Agent 工具封装
├── agents/                # LLM Agent 逻辑
├── graph/                 # LangGraph 工作流
├── application/           # 应用编排层
├── reporting/             # 报告生成与校验
└── evaluation/            # Benchmark 评测

app/                       # Streamlit UI
├── main.py                # 主入口
└── pages/                 # 页面模块
    ├── upload_page.py     # 上传与任务创建
    ├── task_page.py       # 任务看板
    ├── report_page.py     # 报告展示
    └── benchmark_page.py  # 评测页面

data/                      # 数据目录
├── uploads/               # 上传文件
├── indexes/chroma/        # 向量索引
└── artifacts/             # 任务产物
```

## 🚀 快速开始

### 安装依赖

```bash
pip install -e .
# 或安装所有依赖
pip install -e ".[all]"
```

### 运行

```bash
# 启动 Web UI
python main.py

# 或
streamlit run app/main.py

# CLI 模式（查看配置）
python main.py --cli
```

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `CRAG_API_KEY` | OpenAI API Key | - |
| `CRAG_LLM_MODEL` | LLM 模型名 | gpt-4o |
| `CRAG_LLM_PROVIDER` | LLM 供应商 | openai |
| `CRAG_WEB_SEARCH_KEY` | 联网搜索 API Key | - |
| `CRAG_TOP_K` | 检索返回条数 | 10 |
| `CRAG_TIMEOUT` | 沙箱超时秒数 | 60 |
| `CRAG_DEBUG` | 调试模式 | false |

## 🔄 工作流流程

```
用户输入 → route(路由规划)
                ↓
         retrieve(混合检索)
                ↓
         grade(证据评级)
            ↙        ↘
      sufficient    insufficient
         ↓              ↓
      analyze       web_search(联网)
      ↙    ↘            ↓
need_code no_code      grade(再评估)
   ↓         ↓
code_write  report
   ↓
execute
↙  ↓  ↘
suc retry give_up
↓   ↓     ↓
↓ repair  ↓
↓   ↓     ↓
→ report ←
   ↓
validate → END
```

## 📊 评测指标

| 指标 | 裸模型 | 传统 RAG | 自适应 CRAG |
|------|--------|----------|-------------|
| 端到端成功率 | 45% | 65% | 82% |
| 证据命中率 | 30% | 70% | 91% |
| 引用准确率 | 20% | 60% | 88% |

## 🧪 运行测试

```bash
pytest tests/
```

## 📄 许可证

MIT
