"""
Analyzer Agent：将证据和数据摘要转为分析方案。
"""

from adaptive_crag.agents.base_agent import BaseAgent
from adaptive_crag.agents.prompts import ANALYZER_SYSTEM_PROMPT


class AnalyzerAgent(BaseAgent):
    """分析规划 Agent"""

    def build_system_prompt(self) -> str:
        return ANALYZER_SYSTEM_PROMPT

    def build_user_prompt(self, state: dict) -> str:
        query = state.get("query", "")
        plan = state.get("plan", {})
        chunks = state.get("retrieved_chunks", [])

        plan_desc = ""
        if isinstance(plan, dict):
            plan_desc = plan.get("original_query", query)

        evidence_text = ""
        for i, c in enumerate(chunks[:5], 1):
            text = c.get("text", "") if isinstance(c, dict) else str(c)
            evidence_text += f"\n### 文献证据 {i}\n{text[:300]}\n"

        return f"""用户问题: {query}

任务计划: {plan_desc}

可用文献证据:{evidence_text}

请制定分析方案，如果涉及代码请描述代码思路，以 JSON 格式输出。"""

    def parse_response(self, response: str) -> dict:
        parsed = self._extract_json(response)
        if parsed is None:
            return {
                "plan_description": "基于检索到的文献进行分析",
                "code_plan": "",
                "variables": [],
            }

        return {
            "plan_description": parsed.get("plan_description", ""),
            "code_plan": parsed.get("code_plan", ""),
            "variables": parsed.get("variables", []),
        }

    def update_state(self, result: dict, state: dict) -> dict:
        return {
            "code_plan": result.get("code_plan", ""),
            "current_step": "analyzed",
        }

    def _fallback(self, state: dict) -> dict:
        return {
            "code_plan": "",
            "current_step": "analyzed",
            "errors": ["AnalyzerAgent: LLM 无响应"],
        }
