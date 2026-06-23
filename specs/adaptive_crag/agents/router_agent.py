"""
Router Agent：将用户模糊的长指令拆解为结构化子任务。
"""

import json
from adaptive_crag.agents.base_agent import BaseAgent
from adaptive_crag.agents.prompts import ROUTER_SYSTEM_PROMPT


class RouterAgent(BaseAgent):
    """任务规划路由 Agent"""

    def build_system_prompt(self) -> str:
        return ROUTER_SYSTEM_PROMPT

    def build_user_prompt(self, state: dict) -> str:
        query = state.get("query", "")
        files = state.get("uploaded_files", [])

        files_str = "\n".join([f"  - {f}" for f in files]) if files else "  无"
        return f"""用户问题: {query}

已上传文件:
{files_str}

请分析任务类型并输出 JSON 格式的任务计划。"""

    def parse_response(self, response: str) -> dict:
        parsed = self._extract_json(response)
        if parsed is None:
            return {
                "plan": {
                    "original_query": "",
                    "sub_tasks": [{"type": "literature_search", "description": "文献检索", "files": []}],
                    "requires_code": False,
                    "requires_web_search": False,
                    "output_format": "markdown",
                }
            }

        return {
            "plan": {
                "original_query": parsed.get("original_query", ""),
                "sub_tasks": parsed.get("sub_tasks", []),
                "requires_code": parsed.get("requires_code", False),
                "requires_web_search": parsed.get("requires_web_search", False),
                "output_format": parsed.get("output_format", "markdown"),
            }
        }

    def update_state(self, result: dict, state: dict) -> dict:
        return {
            "plan": result.get("plan"),
            "current_step": "routed",
        }

    def _fallback(self, state: dict) -> dict:
        """降级：将整个任务视为 LITERATURE_SEARCH"""
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
