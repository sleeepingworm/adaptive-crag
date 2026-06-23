"""Grader Agent：判断当前检索到的证据是否足够回答问题。"""

from adaptive_crag.agents.base_agent import BaseAgent
from adaptive_crag.agents.prompts import GRADER_SYSTEM_PROMPT
from adaptive_crag.agents.types import GraderInput, GraderOutput


class GraderAgent(BaseAgent):
    """证据评级 Agent"""

    def build_system_prompt(self) -> str:
        return GRADER_SYSTEM_PROMPT

    def build_input(self, state: dict) -> GraderInput:
        return GraderInput(
            query=state.get("query", ""),
            retrieved_chunks=state.get("retrieved_chunks", []),
            web_search_results=state.get("web_search_results", []),
            evidence_gap=state.get("evidence_gap"),
        )

    def build_user_prompt(self, agent_input: GraderInput) -> str:
        evidence_text = ""
        for i, c in enumerate(agent_input.retrieved_chunks[:8], 1):
            if isinstance(c, dict):
                text = c.get("text", "")
                source = c.get("source_label", "")
                prefix = f" [{source}]" if source else ""
                evidence_text += f"\n### 本地证据 {i}{prefix}\n{text[:300]}\n"

        web_text = ""
        if agent_input.web_search_results:
            for i, wr in enumerate(agent_input.web_search_results[:3], 1):
                title = wr.get("title", "") if isinstance(wr, dict) else ""
                snippet = wr.get("snippet", "") if isinstance(wr, dict) else str(wr)
                web_text += f"\n### 联网结果 {i}: {title}\n{snippet[:300]}\n"

        gap_text = f"\n之前发现的证据缺口: {agent_input.evidence_gap}" if agent_input.evidence_gap else "\n暂无证据缺口记录"
        web_fallback = "\n（无联网搜索结果）"

        return f"""用户问题: {agent_input.query}

检索到的本地证据:{evidence_text}
联网搜索补充结果:{web_text if web_text else web_fallback}{gap_text}

请判断当前证据（含本地检索和联网搜索）是否足够回答用户问题，以 JSON 格式输出。"""

    def parse_response(self, response: str) -> GraderOutput:
        parsed = self._extract_json(response)
        if parsed is None:
            return GraderOutput(evidence_gap="无法解析 LLM 响应")

        return GraderOutput(
            evidence_ready=bool(parsed.get("evidence_ready", False)),
            evidence_gap=parsed.get("evidence_gap"),
            confidence=float(parsed.get("confidence", 0.0)),
        )

    def update_state(self, result: GraderOutput, state: dict) -> dict:
        return {
            "evidence_ready": result.evidence_ready,
            "evidence_gap": result.evidence_gap,
            "current_step": "graded",
        }

    def _fallback(self, state: dict) -> dict:
        return {
            "evidence_ready": False,
            "evidence_gap": "GraderAgent: LLM 无响应，默认证据不足",
            "current_step": "graded",
            "errors": ["GraderAgent: LLM 无响应"],
        }