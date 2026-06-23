"""
Validator Agent：检查报告中的关键结论是否能反查到来源。
"""

from adaptive_crag.agents.base_agent import BaseAgent
from adaptive_crag.agents.prompts import VALIDATOR_SYSTEM_PROMPT


class ValidatorAgent(BaseAgent):
    """引用校验 Agent"""

    def build_system_prompt(self) -> str:
        return VALIDATOR_SYSTEM_PROMPT

    def build_user_prompt(self, state: dict) -> str:
        report = state.get("report", "")
        citations = []

        # 从 state 中尝试提取引用
        for key in ["citations", "citation_list"]:
            val = state.get(key, [])
            if val:
                citations = val
                break

        citations_text = ""
        for i, c in enumerate(citations[:10], 1):
            if isinstance(c, dict):
                citations_text += f"\n[{i}] {c.get('claim', '')[:100]} -> {c.get('source_filename', '')}"

        no_citation_msg = "\n无引用列表"
        return f"""报告内容:
{report[:2000]}

引用列表:{citations_text if citations_text else no_citation_msg}

请检查报告中的核心结论是否都有来源引用，以 JSON 格式输出检查结果。"""

    def parse_response(self, response: str) -> dict:
        parsed = self._extract_json(response)
        if parsed is None:
            return {"valid": False, "issues": [{"claim": "无法解析", "issue": "LLM 响应解析失败"}]}

        issues = parsed.get("issues", [])
        if isinstance(issues, list):
            valid = len(issues) == 0
        else:
            valid = bool(parsed.get("valid", False))
            issues = []

        return {"valid": valid, "issues": issues}

    def update_state(self, result: dict, state: dict) -> dict:
        return {
            "citations_valid": result.get("valid", False),
            "current_step": "validated",
        }

    def _fallback(self, state: dict) -> dict:
        return {
            "citations_valid": True,  # 降级：默认通过
            "current_step": "validated",
            "errors": ["ValidatorAgent: LLM 无响应，默认通过引用校验"],
        }
