"""Repair Agent：根据 traceback 修复失败的代码方案。"""

from adaptive_crag.agents.base_agent import BaseAgent
from adaptive_crag.agents.prompts import REPAIR_SYSTEM_PROMPT
from adaptive_crag.agents.types import RepairInput, RepairOutput
from adaptive_crag.sandbox.error_parser import parse_traceback


class RepairAgent(BaseAgent):
    """代码修复 Agent"""

    def build_system_prompt(self) -> str:
        return REPAIR_SYSTEM_PROMPT

    def build_input(self, state: dict) -> RepairInput:
        return RepairInput(
            code=state.get("code", ""),
            code_plan=state.get("code_plan", ""),
            execution_error=state.get("execution_error", ""),
        )

    def build_user_prompt(self, agent_input: RepairInput) -> str:
        parsed = parse_traceback(agent_input.execution_error, agent_input.code)
        error_detail = ""
        if parsed:
            error_detail = f"""
错误类型: {parsed.error_type}
错误信息: {parsed.error_message}
出错行号: {parsed.line_number}
相关代码: {parsed.relevant_line}
可能原因: {parsed.likely_cause}
"""

        return f"""代码计划: {agent_input.code_plan}

原始代码:
```python
{agent_input.code}
```

执行错误:{error_detail}

完整错误信息:
```
{agent_input.execution_error[:1000]}
```

请修复代码中的错误，只返回修复后的 Python 代码。"""

    def parse_response(self, response: str) -> RepairOutput:
        import re
        code_match = re.search(r"```(?:python)?\n?([\s\S]*?)\n?```", response)
        fixed_code = code_match.group(1).strip() if code_match else response.strip()
        return RepairOutput(code=fixed_code)

    def update_state(self, result: RepairOutput, state: dict) -> dict:
        retry_count = state.get("retry_count", 0) + 1
        return {
            "code": result.code,
            "retry_count": retry_count,
            "current_step": f"repaired ({retry_count})",
        }

    def _fallback(self, state: dict) -> dict:
        retry_count = state.get("retry_count", 0) + 1
        return {
            "code": state.get("code", ""),
            "retry_count": retry_count,
            "current_step": f"repaired_fallback ({retry_count})",
            "errors": ["RepairAgent: LLM 无响应，保留原代码"],
        }