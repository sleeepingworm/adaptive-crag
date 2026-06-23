# 模块说明书：Agent 能力封装 (agents)

## 所属层级
Agent 工作流层

## 目标目录
`adaptive_crag/agents/`

生成文件：
```
adaptive_crag/agents/
    __init__.py             # 导出所有 Agent
    base_agent.py           # 基础 Agent 类（共享 LLM 调用逻辑）
    router_agent.py         # 任务规划路由 Agent
    grader_agent.py         # 证据评级 Agent
    analyzer_agent.py       # 分析规划 Agent
    repair_agent.py         # 代码修复 Agent
    report_agent.py         # 报告生成 Agent
    validator_agent.py      # 引用校验 Agent
    prompts.py              # 所有 Agent 的 system prompt 模板
```

## 依赖模块

- **必须先生成**：`01_schema`（使用 GraphState, TaskPlan, etc.）
- **必须先生成**：`02_config`（使用 LLMConfig）
- **必须先生成**：`05_tools`（Agent 调用工具的注册表描述）

## 职责边界

**做：**
- 封装每个 Agent 的 LLM 调用逻辑
- 构造 system prompt 和 user prompt
- 解析 LLM 的结构化响应（JSON 或 markdown）
- 处理 LLM 调用失败（重试、降级）
- 返回增量状态更新

**不做：**
- 不做检索、搜索、执行等具体能力（由 tools 模块做）
- 不做 LangGraph 条件判断（由 graph/conditions.py 做）
- 不做最终报告落地（由 reporting 模块做）

## 基础 Agent 类

### base_agent.py

```python
from abc import ABC, abstractmethod
from adaptive_crag.config import LLMConfig

class BaseAgent(ABC):
    """
    所有 Agent 的基类。封装共享的 LLM 调用逻辑。

    所有 Agent 遵循相同的调用模式:
    1. build_system_prompt() -> 构造系统提示
    2. build_user_prompt(state) -> 从当前状态构造用户提示
    3. call_llm(prompt) -> 调用 LLM
    4. parse_response(response) -> 解析响应为结构化结果
    5. update_state(result, state) -> 返回状态增量
    """

    def __init__(self, llm_config: LLMConfig):
        self.llm_config = llm_config
        self.model_name = llm_config.model_name

    @abstractmethod
    def build_system_prompt(self) -> str:
        """构建 system prompt"""

    @abstractmethod
    def build_user_prompt(self, state: dict) -> str:
        """从当前状态构建 user prompt"""

    def call_llm(self, system: str, user: str) -> str:
        """
        调用 LLM。

        实现:
        - 根据 llm_config.provider 选择调用方式
        - OpenAI-compatible API: openai.ChatCompletion.create()
        - Ollama: requests.post('http://localhost:11434/api/chat')
        - 支持 temperature、max_tokens 参数
        - 调用失败时重试 1 次
        - 两次都失败时返回空字符串
        """

    @abstractmethod
    def parse_response(self, response: str) -> dict:
        """
        解析 LLM 响应为结构化 dict。
        失败时返回包含 error 字段的 dict。
        """

    @abstractmethod
    def update_state(self, result: dict, state: dict) -> dict:
        """
        将解析结果映射为 GraphState 的增量更新。
        """

    def run(self, state: dict) -> dict:
        """
        完整执行流程:
        1. system = self.build_system_prompt()
        2. user = self.build_user_prompt(state)
        3. response = self.call_llm(system, user)
        4. result = self.parse_response(response)
        5. return self.update_state(result, state)

        如果 call_llm 返回空，构造降级响应。
        """
```

## Agent 细分职责

### router_agent.py

**职责**：将用户模糊的长指令拆解为结构化子任务。

- `build_system_prompt()`：告知角色是"任务规划师"，输出格式要求 JSON
- `build_user_prompt(state)`：展示用户原始 query 和上传文件列表
- `parse_response(response)`：提取 JSON 中的 TaskPlan 字段
- **降级策略**：无法解析时将整个任务视为 LITERATURE_SEARCH

输出格式：
```json
{
    "sub_tasks": [
        {"type": "literature_search", "description": "查找...", "files": ["file1.pdf"]},
        {"type": "data_analysis", "description": "分析...", "files": ["data.csv"]}
    ],
    "requires_code": true,
    "requires_web_search": false,
    "output_format": "markdown"
}
```

### grader_agent.py

**职责**：判断当前检索到的证据是否足够回答问题。

- `build_user_prompt(state)`：展示用户 query、retrieved_chunks（top 5）、evidence_gap
- 要求 LLM 输出：`{"evidence_ready": bool, "evidence_gap": str | null, "confidence": float}`
- **关键判断标准**：
  - 证据是否覆盖了问题的核心实体/概念？
  - 证据数量是否 >= 2 条（避免单条偏差）？
  - 是否有明显的信息缺失？
- **降级策略**：LLM 无响应时默认 evidence_ready=False

### analyzer_agent.py

**职责**：将证据和数据摘要转为分析方案。

- 输入：用户 query、EvidenceSet、DatasetProfile
- 输出分析方案 description 和代码思路 code_plan
- 不直接生成可执行代码（code_write 再做）
- 输出：`{"plan_description": "...", "code_plan": "...", "variables": [{"name": "df", "source": "data.csv"}]}`

### repair_agent.py

**职责**：根据 traceback 修复失败的代码方案。

- 输入：原代码、traceback、execution_error、code_plan、数据摘要
- 输出：修复后的代码
- **修复边界**：
  - 变量名错误：修正拼写或添加正确赋值
  - 字段不存在：检查 DatasetProfile 的 columns，改成正确的列名
  - 类型错误：添加类型转换
  - import 缺失：添加 import 语句
  - 绘图保存问题：检查输出目录存在性
- **不可修复**：数据文件不存在、依赖缺失（如当前环境无 matplotlib）

### report_agent.py

**职责**：整合所有证据、执行结果、图表为完整 Markdown 报告。

- 输入：全部 GraphState（query, plan, retrieved_chunks, web_search_results, execution_result, citations）
- 报告结构：
  ```markdown
  # 标题：{query}

  ## 摘要
  ...

  ## 数据与文献来源
  ...

  ## 核心结论（附引用）
  - ...
  - ...

  ## 数据分析（如有）
  - 图表说明
  - 统计结果

  ## 局限性
  - 本次未覆盖的部分

  ## 引用列表
  - [1] {filename}, 第 X 页
  ```

### validator_agent.py

**职责**：检查报告中的关键结论是否能反查到来源。

- 输入：报告文本、Citation 列表
- 检查每个结论对应的 citation_id 是否存在于引用映射中
- 输出：`{"valid": bool, "issues": [{"claim": "xxx", "issue": "无对应来源"}]}`
- **降级策略**：check_failures > 0 时标记 citations_valid=False

## 提示词模板 (prompts.py)

```python
ROUTER_SYSTEM_PROMPT = """你是一个研究任务规划师...

- 如果用户要求从文献中找信息，拆为 literature_search
- 如果用户要求分析数据，拆为 data_analysis
- 如果两者都有，拆为 hybrid

请以 JSON 格式输出...
"""

GRADER_SYSTEM_PROMPT = """你是一个证据评估专家...

请基于以下标准判断证据是否足够回答用户问题：
1. 证据是否覆盖了问题的核心实体
2. 至少有 2-3 条相关证据
3. 证据之间没有明显矛盾
...
"""

ANALYZER_SYSTEM_PROMPT = """你是一个数据分析师...

请根据以下文献证据和数据文件，制定分析方案。
如果涉及代码，请描述代码思路而不直接编写完整代码。
...
"""

REPAIR_SYSTEM_PROMPT = """你是一个代码调试专家...

请根据以下错误信息修复代码。注意：
- 不要添加不存在的字段
- 确保 import 完整
- 检查输出路径存在
- 只修复问题不改变分析逻辑
...
"""

REPORT_SYSTEM_PROMPT = """你是一个研究报告撰写专家...

请整合所有信息生成标准研究报告。格式要求：
- 每个关键结论必须附引用编号
- 数据分析部分展示图表解读
- 标注局限性
...
"""
```

## 实现约束

1. **LLM 调用封装**：`call_llm` 方法内部封装 OpenAI-compatible 和 Ollama 两种适配，Agent 本身不感知供应商差异
2. **重试机制**：LLM 调用失败时自动重试 1 次，两次失败用降级策略
3. **JSON 解析**：LLM 输出的 JSON 可能包含 markdown 代码块包裹，`parse_response` 需处理这种情况
4. **超时控制**：LLM 调用设置 60 秒超时
5. **Token 限制**：给每个 Agent 的 max_tokens 不同（Router 少、Report 多）
6. **降级不崩**：任何 Agent 失败后都不能抛异常，必须返回最小可用结果

## 与上下游模块的对接

- **上游调用方**：LangGraph 的各节点函数（调用 agent.run(state)）
- **下游消费方**：graph 节点拿到 agent 返回的增量更新，合并到 GraphState
- **数据流向**：`graph node -> agent.run(state) -> LLM response -> parsed result -> state update`

## 测试要点

- Router 能正确将混合任务拆为多个子任务
- Grader 在证据足够时返回 evidence_ready=True
- 每个 Agent 在 LLM 无响应时能返回降级结果
- repair_agent 能修复典型的 NameError 和 KeyError
- report_agent 生成的 Markdown 包含 # 标题