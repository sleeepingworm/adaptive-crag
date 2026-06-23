"""Analyzer Agent：将证据和数据摘要转为分析方案。"""

from adaptive_crag.agents.base_agent import BaseAgent
from adaptive_crag.agents.prompts import ANALYZER_SYSTEM_PROMPT
from adaptive_crag.agents.types import AnalyzerInput, AnalyzerOutput


class AnalyzerAgent(BaseAgent):
    """分析规划 Agent"""

    def build_system_prompt(self) -> str:
        return ANALYZER_SYSTEM_PROMPT

    def build_input(self, state: dict) -> AnalyzerInput:
        return AnalyzerInput(
            query=state.get("query", ""),
            plan=state.get("plan", {}),
            retrieved_chunks=state.get("retrieved_chunks", []),
        )

    def build_user_prompt(self, agent_input: AnalyzerInput) -> str:
        plan_desc = agent_input.plan.get("original_query", agent_input.query)

        evidence_text = ""
        for i, c in enumerate(agent_input.retrieved_chunks[:8], 1):
            if isinstance(c, dict):
                text = c.get("text", "")
                source = c.get("source_label", "")
                prefix = f" [{source}]" if source else ""
                evidence_text += f"\n### 文献证据 {i}{prefix}\n{text[:300]}\n"

        return f"""用户问题: {agent_input.query}

任务计划: {plan_desc}

可用文献证据:{evidence_text}

请制定分析方案，如果涉及代码请描述代码思路，以 JSON 格式输出。"""

    def parse_response(self, response: str) -> AnalyzerOutput:
        parsed = self._extract_json(response)
        if parsed is None:
            return AnalyzerOutput(plan_description="基于检索到的文献进行分析")

        return AnalyzerOutput(
            plan_description=parsed.get("plan_description", ""),
            code_plan=parsed.get("code_plan", ""),
            variables=parsed.get("variables", []),
        )

    def update_state(self, result: AnalyzerOutput, state: dict) -> dict:
        return {
            "code_plan": result.code_plan,
            "current_step": "analyzed",
        }

    def _fallback(self, state: dict) -> dict:
        return {
            "code_plan": "",
            "current_step": "analyzed",
            "errors": ["AnalyzerAgent: LLM 无响应"],
        }