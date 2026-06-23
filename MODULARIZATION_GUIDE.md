# 模块化改造指导文档

> 本文档用你当前项目的具体代码做例子，讲清楚：模块化到底是什么、你现在哪里没模块化、目标长什么样、分几步走。

---

## 一、模块化的三个核心标准

目录分得细不等于模块化。模块化的判定标准只有三条：

### 标准 1：接口明确

一个模块对外暴露什么、接收什么、返回什么，必须一眼看清。

**反面例子**（你的代码）：
`GraderAgent.build_user_prompt(self, state: dict) -> str` —— 参数是 `dict`，你不知道这个 dict 里有什么字段，全靠 `state.get("xxx", [])` 猜。

**正面例子**：
`GraderAgent.build_user_prompt(self, input: GradeInput) -> str` —— `GradeInput` 是一个 dataclass，包含 `query: str`、`chunks: list[Chunk]`、`web_results: list[WebResult]`。看到这个签名就知道 Grader 需要什么。

---

### 标准 2：无全局依赖

一个模块 import 进来就能用，不需要外面先 "set 好什么"。

**反面例子**（你的代码）：
`tools/hybrid_search.py` 里的 `_hybrid_retriever` 是模块级全局变量，靠外部 `set_hybrid_retriever()` 注入。你 import 这个模块后不能直接调用 `hybrid_search()`，必须先等 TaskOrchestrator 初始化完。

**正面例子**：
`hybrid_search(retriever: HybridRetriever, params: dict) -> dict` —— retriever 作为参数传入，tools 模块不依赖任何模块级状态。

---

### 标准 3：可独立替换

一个模块换掉实现，只要新实现遵守同样的接口，下游不用改任何代码。

**反面例子**（你的代码）：
`build_workflow()` 硬编码了 route → retrieve → grade → web_search → analyze → code_write → execute → repair → report → validate 的顺序。想加一步"数据预清洗"？改 `build_workflow()`。

**正面例子**：
步骤列表 `[route_step, retrieve_step, grade_step, ...]` 驱动图构建。加一个 `clean_step` 只需在列表里插入一行，`build_workflow()` 不用动。

---

## 二、当前耦合病灶：四个具体位置

### 病灶 A：tools 模块被全局变量绑死

涉及文件：
- `adaptive_crag/tools/hybrid_search.py` — 模块级 `_hybrid_retriever`，由外部 `set_hybrid_retriever()` 注入
- `adaptive_crag/tools/citation_lookup.py` — 模块级 `_citation_mappings`，由外部 `set_citation_mappings()` 注入
- `adaptive_crag/tools/bm25_search.py` — 从 `hybrid_search` 导入 `_hybrid_retriever`
- `adaptive_crag/tools/vector_search.py` — 同上

耦合链路：`TaskOrchestrator.start_task()` → `set_hybrid_retriever()` 设置全局 → 后续 Agent 调用 `hybrid_search()` 时从全局读取。tools 模块**不能独立存在**，必须挂在 TaskOrchestrator 的上下文中。

---

### 病灶 B：10 个 graph node 复制粘贴

涉及文件：`adaptive_crag/graph/nodes/` 下的 `route_node.py`、`retrieve_node.py`、`grade_node.py`、`web_search_node.py`、`analyze_node.py`、`code_write_node.py`、`execute_node.py`、`repair_node.py`、`report_node.py`、`validate_node.py`

每个 node 都包含完全相同的样板：`check_abort()` 调用、`try/except` 包裹、`_emit_event()` 调用、手动透传 `query`/`uploaded_files`/`_workflow_step_count`。核心逻辑只占每个 node 的三分之一。

这不是 10 个独立的模块，是同一个模式抄了 10 遍。改一个模式（比如加日志）要改 10 个文件。

---

### 病灶 C：Agent 之间用裸 dict 通信

涉及文件：`adaptive_crag/agents/` 下的 6 个 Agent，以及调用它们的 graph node。

数据流：node 把 `state` dict 传给 `Agent.build_user_prompt(state)` → Agent 从 dict 中 `get()` 字段 → LLM 返回字符串 → `Agent.parse_response(str) -> dict` → node 把 dict 合并回 state。

问题：没有任何一个地方定义了 "state 里应该有什么"、"Agent 返回的 dict 结构是什么"。字段名拼写错误不会报错，只会静默返回 `[]` 或 `""`。

---

### 病灶 D：Pipeline 步骤硬编码

涉及文件：`adaptive_crag/graph/workflow.py` 的 `build_workflow()` 函数

`build_workflow()` 直接 `.add_node("route", route_node)` → `.add_edge(START, "route")` → `.add_conditional_edges(...)` — 步骤顺序写在函数体内。每增删一个步骤就要改这个函数。

---

## 三、目标架构

改造后的数据流（每个箭头是一个**类型化的接口**）：

```
上传文件
  ↓
[Ingestion 模块]  →  Chunk[]
  ↓
[IndexBuilder 模块]  →  写入 ChromaDB + BM25
  ↓
用户问题
  ↓
[Retriever 模块]  →  SearchResult[]
  ↓
[Grader 模块]  →  EvidenceAssessment
  ↓                  ↓ (不足时)
  ↓              [WebSearch 模块]  →  WebResult[]
  ↓                  ↓
[Analyzer 模块]  →  AnalysisPlan
  ↓
[CodeWriter 模块]  →  CodeArtifact
  ↓
[Sandbox 模块]  →  ExecutionResult
  ↓
[Reporter 模块]  →  Markdown 报告
  ↓
[Validator 模块]  →  ValidationResult
```

关键差异：
- 每个模块之间传的是**明确类型**（`Chunk[]`、`SearchResult[]`、`EvidenceAssessment`...），不是裸 `dict`
- 每个模块**不依赖全局变量**，需要的依赖通过参数传入
- 步骤顺序由**配置列表**驱动，不是写死在函数里

---

## 四、改造路线（4 关）

按依赖顺序排，每关解决一个耦合类型。前一个通关后一个才有基础。

| 关卡 | 解决的问题 | 涉及文件数 | 难度 |
|------|-----------|-----------|------|
| 第 1 关 | 消灭 tools 全局变量（病灶 A） | 5 | 低 |
| 第 2 关 | 统一 graph node 样板（病灶 B） | 11 | 中 |
| 第 3 关 | Agent 接口类型化（病灶 C） | 8 | 中 |
| 第 4 关 | Pipeline 步骤可插拔（病灶 D） | 1 | 低 |

---

## 五、教学约定

1. 每关由我先讲解当前耦合的具体表现和问题
2. 我来做代码改造
3. 改造完成后我讲解：改了什么、为什么这样改、模块边界在哪里、怎么验证改对了
4. 你确认理解后进入下一关
5. 过程中有任何概念不清楚的随时打断提问

---

*下一关入口：回复"开始第 1 关"*