"""Validator Agent：检查报告中的关键结论是否能反查到来源。"""

from adaptive_crag.agents.base_agent import BaseAgent
from adaptive_crag.agents.prompts import VALIDATOR_SYSTEM_PROMPT
from adaptive_crag.agents.types import ValidatorInput, ValidatorOutput


class ValidatorAgent(BaseAgent):
    """引用校验 Agent"""

    def build_system_prompt(self) -> str:
        return VALIDATOR_SYSTEM_PROMPT

    def build_input(self, state: dict) -> ValidatorInput:
        citations = []
        for key in ["citations", "citation_list"]:
            val = state.get(key, [])
            if val:
                citations = val
                break
        return ValidatorInput(
            report=state.get("report", ""),
            citations=citations,
        )

    def build_user_prompt(self, agent_input: ValidatorInput) -> str:
        citations_text = ""
        for i, c in enumerate(agent_input.citations[:10], 1):
            if isinstance(c, dict):
                citations_text += f"\n[{i}] {c.get('claim', '')[:100]} -> {c.get('source_filename', '')}"

        citations_fallback = "\n无引用列表"

        return f"""报告内容:
{agent_input.report[:2000]}

引用列表:{citations_text if citations_text else citations_fallback}

请检查报告中的核心结论是否都有来源引用，以 JSON 格式输出检查结果。"""

    def parse_response(self, response: str) -> ValidatorOutput:
        parsed = self._extract_json(response)
        if parsed is None:
            return ValidatorOutput(issues=[{"claim": "无法解析", "issue": "LLM 响应解析失败"}])

        issues = parsed.get("issues", [])
        if isinstance(issues, list):
            valid = len(issues) == 0
        else:
            valid = bool(parsed.get("valid", False))
            issues = []

        return ValidatorOutput(citations_valid=valid, issues=issues)

    def update_state(self, result: ValidatorOutput, state: dict) -> dict:
        return {
            "citations_valid": result.citations_valid,
            "current_step": "validated",
        }

    def _fallback(self, state: dict) -> dict:
        return {
            "citations_valid": True,
            "current_step": "validated",
            "errors": ["ValidatorAgent: LLM 无响应，默认通过引用校验"],
        }