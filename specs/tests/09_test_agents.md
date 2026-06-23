# 单元测试说明书：Agent 能力封装 (agents)

## 对应模块
`09_agents.md`

## 目标测试文件
```
tests/
    test_agents/
        __init__.py
        conftest.py              # mock LLM 的 fixture
        test_base_agent.py       # 基础 Agent 类
        test_router_agent.py     # 路由 Agent
        test_grader_agent.py     # 证据评级 Agent
        test_analyzer_agent.py   # 分析规划 Agent
        test_repair_agent.py     # 代码修复 Agent
        test_report_agent.py     # 报告生成 Agent
        test_validator_agent.py  # 引用校验 Agent
        test_prompts.py          # 提示词模板
```

## 运行方式
```bash
pytest tests/test_agents/ -v
```

## 测试策略
- **不调用真实 LLM**：使用 unittest.mock 模拟 LLM 响应
- 测试每个 Agent 的：prompt 构造、响应解析、降级逻辑、增量状态更新
- LLM 返回固定 JSON 字符串，测试解析和状态映射

## conftest.py mock 策略

```python
@pytest.fixture
def mock_llm_response(monkeypatch):
    """mock BaseAgent.call_llm 返回固定字符串"""

@pytest.fixture
def mock_llm_empty(monkeypatch):
    """mock BaseAgent.call_llm 返回空字符串（模拟 LLM 失败）"""

@pytest.fixture
def mock_llm_invalid_json(monkeypatch):
    """mock BaseAgent.call_llm 返回非 JSON 字符串"""

@pytest.fixture
def router_agent(test_llm_config):
    return RouterAgent(test_llm_config)

@pytest.fixture
def grader_agent(test_llm_config):
    return GraderAgent(test_llm_config)

@pytest.fixture
def test_llm_config():
    return LLMConfig(provider="openai", model_name="gpt-4o-mini")

@pytest.fixture
def sample_graph_state():
    """包含 query 和 uploaded_files 的 GraphState dict"""
```

## 测试用例清单

### test_base_agent.py

```python
def test_base_agent_has_run_method(base_agent):
    """BaseAgent 有 run(state) 方法"""

def test_run_returns_dict(base_agent, sample_state, mock_llm_response):
    """run 返回 dict"""

def test_run_llm_failure_returns_graceful(base_agent, sample_state, mock_llm_empty):
    """LLM 失败时返回降级结果，不抛异常"""

def test_run_invalid_response(base_agent, sample_state, mock_llm_invalid_json):
    """LLM 返回不可解析内容时返回降级结果"""
```

### test_router_agent.py

```python
def test_router_prompt_contains_query(router_agent, sample_state):
    """build_user_prompt 包含用户 query"""

def test_router_prompt_contains_files(router_agent, sample_state_with_files):
    """有上传文件时 prompt 包含文件名"""

def test_router_parse_json_response(router_agent):
    """能解析 LLM 返回的 JSON"""

def test_router_parse_response_with_markdown_codeblock(router_agent):
    """能处理 LLM 响应带 ```json ``` 包裹的情况"""

def test_router_parse_empty_response(router_agent):
    """空响应返回降级 TaskPlan（纯 literature_search）"""

def test_router_state_update(router_agent, mock_llm_response):
    """update_state 返回的 dict 包含 plan 字段"""

def test_router_hybrid_task(router_agent, mock_llm_response_hybrid):
    """混合任务在 plan.sub_tasks 中包含两个子任务"""

def test_router_determines_code_required(router_agent, mock_llm_response_code):
    """需要数据分析的任务 requires_code=True"""
```

### test_grader_agent.py

```python
def test_grader_prompt_contains_evidence(grader_agent, state_with_evidence):
    """prompt 包含检索到的证据"""

def test_grader_parse_sufficient(grader_agent):
    """解析 evidence_ready=True"""

def test_grader_parse_insufficient(grader_agent):
    """解析 evidence_ready=False + evidence_gap"""

def test_grader_parse_no_json(grader_agent):
    """非 JSON 响应默认 evidence_ready=False"""

def test_grader_state_update(grader_agent, mock_llm_response_sufficient):
    """更新后 state.evidence_ready==True"""

def test_grader_empty_evidence(grader_agent, state_no_evidence):
    """无证据时默认 evidence_ready=False"""
```

### test_repair_agent.py

```python
def test_repair_prompt_contains_traceback(repair_agent, state_with_error):
    """prompt 包含 traceback"""

def test_repair_prompt_contains_original_code(repair_agent, state_with_error):
    """prompt 包含失败的原代码"""

def test_repair_parse_code(repair_agent):
    """解析 LLM 返回的修复代码"""

def test_repair_state_update(repair_agent, mock_llm_response_fix):
    """update_state 返回的 dict 包含修复后的 code"""

def test_repair_increments_retry(repair_agent, mock_llm_response_fix):
    """update_state 自动 retry_count + 1"""

def test_repair_no_code_in_response(repair_agent, mock_llm_empty):
    """LLM 没返回代码时使用原代码（不恶化）"""
```

### test_report_agent.py

```python
def test_report_prompt_contains_plan(report_agent, state_with_analysis):
    """prompt 包含分析计划"""

def test_report_prompt_contains_charts(report_agent, state_with_charts):
    """prompt 包含图表路径"""

def test_report_parse_markdown(report_agent):
    """解析 LLM 返回的 Markdown 报告"""

def test_report_state_update(report_agent, mock_llm_response_report):
    """update_state 返回的 dict 包含 report 和 report_ready=True"""

def test_report_no_llm_response(report_agent, mock_llm_empty):
    """LLM 无响应时返回"报告生成失败"的占位报告"""

def test_report_contains_sections(report_agent, mock_llm_response_report):
    """生成的报告包含 ## 标题格式的章节"""
```

### test_validator_agent.py

```python
def test_validator_check_valid(validator_agent, state_with_valid_citations):
    """所有引用有效时 citations_valid=True"""

def test_validator_check_invalid(validator_agent, state_with_invalid_citations):
    """有无效引用时 citations_valid=False, issues 不为空"""

def test_validator_no_citations(validator_agent, state_no_citations):
    """无引用时返回 valid=True（没有引用就没有错误）"""

def test_validator_state_update(validator_agent, mock_llm_response_valid):
    """update_state 设置 citations_valid"""
```

### test_prompts.py

```python
def test_all_prompts_are_strings():
    """所有提示词模板是非空字符串"""

def test_prompts_have_no_placeholders():
    """提示词模板中不应有未替换的 {placeholder}"""

def test_router_prompt_structure():
    """ROUTER_SYSTEM_PROMPT 包含 sub_tasks 和 requires_code"""

def test_grader_prompt_structure():
    """GRADER_SYSTEM_PROMPT 包含 evidence_ready"""
```