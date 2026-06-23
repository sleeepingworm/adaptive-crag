"""
Report Agent：整合所有证据、执行结果、图表为完整 Markdown 报告。
"""

from adaptive_crag.agents.base_agent import BaseAgent
from adaptive_crag.agents.prompts import REPORT_SYSTEM_PROMPT


class ReportAgent(BaseAgent):
    """报告生成 Agent"""

    def build_system_prompt(self) -> str:
        return REPORT_SYSTEM_PROMPT

    def build_user_prompt(self, state: dict) -> str:
        query = state.get("query", "")
        plan = state.get("plan", {})
        chunks = state.get("retrieved_chunks", [])
        execution_result = state.get("execution_result")
        web_results = state.get("web_search_results", [])

        plan_desc = ""
        if isinstance(plan, dict):
            plan_desc = plan.get("original_query", query)

        # 文献证据摘要
        evidence_text = ""
        for i, c in enumerate(chunks[:3], 1):
            if isinstance(c, dict):
                text = c.get("text", "")
                filename = c.get("filename", c.get("doc_id", ""))
                page = c.get("page_num")
                page_str = f" (第{page}页)" if page else ""
                evidence_text += f"\n#### 文献{i}{page_str} - {filename}\n{text[:500]}\n"

        # 执行结果
        exec_text = ""
        if execution_result:
            success = execution_result.get("success", False)
            stdout = execution_result.get("stdout", "")[:500]
            files = execution_result.get("generated_files", [])
            exec_text = f"""
数据分析结果:
- 执行{'成功' if success else '失败'}
- 输出: {stdout}
- 生成文件: {', '.join(files) if files else '无'}
"""

        # 联网搜索结果
        web_text = ""
        if web_results:
            web_text = "\n联网搜索结果:\n"
            for i, r in enumerate(web_results[:3], 1):
                if isinstance(r, dict):
                    web_text += f"\n#### 结果{i}: {r.get('title', '')}\n{r.get('snippet', '')[:300]}\n"

        return f"""用户问题: {query}

任务描述: {plan_desc}

文献证据:{evidence_text}

{exec_text}

{web_text}

请生成完整的 Markdown 格式研究报告。"""

    def parse_response(self, response: str) -> dict:
        return {"report": response.strip()}

    def update_state(self, result: dict, state: dict) -> dict:
        return {
            "report": result.get("report", ""),
            "report_ready": bool(result.get("report")),
            "current_step": "report_generated",
        }

    def _fallback(self, state: dict) -> dict:
        query = state.get("query", "")
        return {
            "report": f"# {query}\n\n## 摘要\n\n系统无法生成报告（LLM 无响应）。\n\n请检查 LLM 配置后重试。\n",
            "report_ready": True,
            "current_step": "report_generated",
            "errors": ["ReportAgent: LLM 无响应，生成占位报告"],
        }
