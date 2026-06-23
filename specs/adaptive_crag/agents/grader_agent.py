"""
Grader Agent：判断当前检索到的证据是否足够回答问题。
"""

from adaptive_crag.agents.base_agent import BaseAgent
from adaptive_crag.agents.prompts import GRADER_SYSTEM_PROMPT


class GraderAgent(BaseAgent):
    """证据评级 Agent"""

    def build_system_prompt(self) -> str:
        return GRADER_SYSTEM_PROMPT

    def build_user_prompt(self, state: dict) -> str:
        query = state.get("query", "")
        chunks = state.get("retrieved_chunks", [])
        gap = state.get("evidence_gap")

        # 展示前 5 条证据
        evidence_text = ""
        for i, c in enumerate(chunks[:5], 1):
            text = c.get("text", "") if isinstance(c, dict) else str(c)
            evidence_text += f"\n### 证据 {i}\n{text[:300]}\n"

        gap_text = f"\n之前发现的证据缺口: {gap}" if gap else "\n暂无证据缺口记录"

        return f"""用户问题: {query}

检索到的证据:{evidence_text}{gap_text}

请判断当前证据是否足够回答用户问题，以 JSON 格式输出。"""

    def parse_response(self, response: str) -> dict:
        parsed = self._extract_json(response)
        if parsed is None:
            return {"evidence_ready": False, "evidence_gap": "无法解析 LLM 响应", "confidence": 0.0}

        return {
            "evidence_ready": bool(parsed.get("evidence_ready", False)),
            "evidence_gap": parsed.get("evidence_gap"),
            "confidence": float(parsed.get("confidence", 0.0)),
        }

    def update_state(self, result: dict, state: dict) -> dict:
        return {
            "evidence_ready": result["evidence_ready"],
            "evidence_gap": result.get("evidence_gap"),
            "current_step": "graded",
        }

    def _fallback(self, state: dict) -> dict:
        """降级：默认证据不足"""
        return {
            "evidence_ready": False,
            "evidence_gap": "GraderAgent: LLM 无响应，默认证据不足",
            "current_step": "graded",
            "errors": ["GraderAgent: LLM 无响应"],
        }
