# 模块说明书：LangGraph 工作流 (graph)

## 所属层级
Agent 工作流层

## 目标目录
`adaptive_crag/graph/`

生成文件：
```
adaptive_crag/graph/
    __init__.py             # 导出 build_workflow, run_workflow
    state.py                # GraphState 扩展和 schema 绑定
    workflow.py             # LangGraph 主工作流构建
    conditions.py           # 条件边判断函数
    nodes/
        __init__.py
        route_node.py         # Router 节点
        retrieve_node.py      # 混合检索节点
        grade_node.py         # 证据评级节点
        web_search_node.py    # 联网搜索节点
        analyze_node.py       # 分析规划节点
        code_write_node.py    # 代码生成节点
        execute_node.py       # 沙箱执行节点
        repair_node.py        # 修复节点
        report_node.py        # 报告生成节点
        validate_node.py      # 引用校验节点
```

## 依赖模块

- **必须先生成**：`01_schema`（使用 GraphState）
- **必须先生成**：`02_config`（使用 SelfCorrectionConfig）
- **必须先生成**：`04_retrieval`（检索节点调用）
- **必须先生成**：`05_tools`（各工具函数）
- **必须先生成**：`06_sandbox`（沙箱执行器）
- **必须先生成**：`08_agents`（Agent 的 LLM 调用逻辑）
- **必须先生成**：`10_reporting`（报告生成）

## 职责边界

**做：**
- 用 LangGraph 的 StateGraph 构建有向状态机
- 注册节点（Node）和条件边（ConditionalEdge）
- 管理 GraphState 在节点间的传递与更新
- 控制重试逻辑：执行失败时路由到 repair 节点
- 控制降级逻辑：重试次数超限时直接路由到 report 节点
- 事件回调：通过 callback 向外部发送执行事件

**不做：**
- 不直接调用 LLM（agents 模块做）
- 不直接执行代码（sandbox 模块做）
- 不直接生成报告（reporting 模块做）

## 工作流图定义

### 状态翻转主流程

```python
# adaptive_crag/graph/workflow.py

from langgraph.graph import StateGraph, END
from .state import create_initial_state

def build_workflow() -> StateGraph:
    """
    构建 LangGraph 状态机。

    节点:
    - "route"         -> Router Agent
    - "retrieve"      -> 混合检索
    - "grade"         -> 证据评级
    - "web_search"    -> 联网搜索
    - "analyze"       -> 分析规划
    - "code_write"    -> 代码生成
    - "execute"       -> 沙箱执行
    - "repair"        -> 修复方案
    - "report"        -> 报告生成
    - "validate"      -> 引用校验

    条件边:
    - after_grade: 足够 -> analyze | 不足 -> web_search
    - after_analyze: 需要代码 -> code_write | 不需要 -> report
    - after_execute: 成功 -> report | 失败且未超限 -> repair | 失败且超限 -> report
    """

    workflow = StateGraph(GraphState)

    # 注册节点
    workflow.add_node("route", route_node)
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("grade", grade_node)
    workflow.add_node("web_search", web_search_node)
    workflow.add_node("analyze", analyze_node)
    workflow.add_node("code_write", code_write_node)
    workflow.add_node("execute", execute_node)
    workflow.add_node("repair", repair_node)
    workflow.add_node("report", report_node)
    workflow.add_node("validate", validate_node)

    # 设置入口
    workflow.set_entry_point("route")

    # 有向边
    workflow.add_edge("route", "retrieve")
    workflow.add_edge("retrieve", "grade")
    workflow.add_conditional_edges("grade", after_grade, {
        "sufficient": "analyze",
        "insufficient": "web_search"
    })
    workflow.add_edge("web_search", "grade")         # 联网后回到 grade 再判断
    workflow.add_conditional_edges("analyze", after_analyze, {
        "need_code": "code_write",
        "no_code": "report"
    })
    workflow.add_edge("code_write", "execute")
    workflow.add_conditional_edges("execute", after_execute, {
        "success": "report",
        "retry": "repair",
        "give_up": "report"
    })
    workflow.add_edge("repair", "execute")            # 修复后重新执行
    workflow.add_edge("report", "validate")
    workflow.add_edge("validate", END)

    return workflow
```

### conditions.py

```python
def after_grade(state: GraphState) -> str:
    """
    根据证据是否足够选择路径。

    读取:
        state.evidence_ready (bool)
        state.evidence_gap (str | None)

    返回:
        "sufficient" - 证据足够，进入分析规划
        "insufficient" - 证据不足，进入联网搜索
    """

def after_analyze(state: GraphState) -> str:
    """
    根据是否需要生成代码选择路径。

    读取:
        state.plan.requires_code (bool)
        state.code (str | None)

    返回:
        "need_code" - 需要数据分析，进入代码生成
        "no_code" - 纯文献分析，直接生成报告
    """

def after_execute(state: GraphState) -> str:
    """
    根据执行结果选择路径。

    读取:
        state.execution_result.success (bool)
        state.retry_count (int)
        state.max_retries (int)
        state.execution_error (str | None)

    返回:
        "success" - 执行成功
        "retry" - 失败且重试次数未超限
        "give_up" - 失败且重试次数超限
    """
```

## 节点通用签名

每个节点是一个函数：

```python
def node_name(state: GraphState) -> dict:
    """
    输入: 当前 GraphState
    输出: dict 形式的增量更新（只会更新 dict 中的字段）
    """
    # ... 调用对应的 agent 或工具
    return {
        "field_name": new_value,   # 只更新这些字段
        "current_step": "xxx",     # 更新步骤名
        "errors": [...]            # 如果出错
    }
```

## 执行事件回调

工作流应支持可选的 callback 函数，在以下时机触发：

```python
def on_step_change(step_name: str, status: str, message: str, timestamp: str):
    """每一步开始时触发"""

def on_tool_call(tool_name: str, params: dict, result: dict):
    """工具调用后触发"""
```

这两个 callback 将事件传递给 application 层的 TaskOrchestrator，再传给前端展示。

## 实现约束

1. **同步执行**：MVP 使用 `graph.invoke(initial_state)` 同步执行，不启用 streaming
2. **状态不可变性**：每个节点不修改原始 state，返回 dict 增量更新
3. **重试上限**：`max_retries` 在 config 中配置，默认 3 次
4. **降级策略**：超限后进入 report 节点，报告中注明失败步骤和可用证据
5. **错误不传播**：节点内部异常被 catch 后写入 state.errors，节点返回不报错

## 与上下游模块的对接

- **上游调用方**：application 层的 TaskOrchestrator
- **下游消费方**：调用 agents 模块进行 LLM 判断，调用 tools 模块执行具体能力
- **数据流向**：`TaskOrchestrator -> Graph.invoke(state) -> [节点链] -> 最终 state`

## 核心安装依赖

- `langgraph` (>=0.0.30)
- `langchain-core`（用于状态定义）

## 测试要点

- 构建的工作流能通过 `graph.get_graph().print_ascii()` 正确展示
- 证据足够时路径：route -> retrieve -> grade -> analyze -> (no_code) -> report -> validate -> END
- 需要代码且执行成功时：route -> retrieve -> grade -> analyze -> code_write -> execute -> report -> validate
- 执行失败且重试未超限时：... -> execute -> repair -> execute -> ...
- 重试超限时：... -> execute -> report (跳过 repair)
- callback 能在每步被正确触发