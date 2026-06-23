"""Router Agent：将用户模糊的长指令拆解为结构化子任务。"""

from adaptive_crag.agents.base_agent import BaseAgent
from adaptive_crag.agents.prompts import ROUTER_SYSTEM_PROMPT
from adaptive_crag.agents.types import RouterInput, RouterOutput


class RouterAgent(BaseAgent):
    """任务规划路由 Agent"""

    def build_system_prompt(self) -> str:
        return ROUTER_SYSTEM_PROMPT

    def build_input(self, state: dict) -> RouterInput:
        return RouterInput(
            query=state.get("query", ""),
            uploaded_files=state.get("uploaded_files", []),
        )

    def build_user_prompt(self, agent_input: RouterInput) -> str:
        files_str = "\n".join([f"  - {f}" for f in agent_input.uploaded_files]) if agent_input.uploaded_files else "  无"
        return f"""用户问题: {agent_input.query}

已上传文件:
{files_str}

请分析任务类型并输出 JSON 格式的任务计划。"""

    def parse_response(self, response: str) -> RouterOutput:
        parsed = self._extract_json(response)
        if parsed is None:
            return RouterOutput()

        return RouterOutput(
            plan={
                "original_query": parsed.get("original_query", ""),
                "sub_tasks": parsed.get("sub_tasks", []),
                "requires_code": parsed.get("requires_code", False),
                "requires_web_search": parsed.get("requires_web_search", False),
                "output_format": parsed.get("output_format", "markdown"),
            },
            requires_code=parsed.get("requires_code", False),
            requires_web_search=parsed.get("requires_web_search", False),
        )

    def update_state(self, result: RouterOutput, state: dict) -> dict:
        return {
            "plan": result.plan,
            "current_step": "routed",
        }

    def _fallback(self, state: dict) -> dict:
        return {
            "plan": {
                "original_query": state.get("query", ""),
                "sub_tasks": [{"type": "literature_search", "description": state.get("query", ""), "files": state.get("uploaded_files", [])}],
                "requires_code": False,
                "requires_web_search": False,
                "output_format": "markdown",
            },
            "current_step": "routed",
            "errors": ["RouterAgent: LLM 无响应，使用默认路由"],
        }