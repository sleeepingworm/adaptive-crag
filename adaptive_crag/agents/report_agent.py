"""Report Agent：整合所有证据、执行结果、图表为完整 Markdown 报告。"""

from adaptive_crag.agents.base_agent import BaseAgent
from adaptive_crag.agents.prompts import REPORT_SYSTEM_PROMPT
from adaptive_crag.agents.types import ReportInput, ReportOutput


class ReportAgent(BaseAgent):
    """报告生成 Agent"""

    def build_system_prompt(self) -> str:
        return REPORT_SYSTEM_PROMPT

    def build_input(self, state: dict) -> ReportInput:
        return ReportInput(
            query=state.get("query", ""),
            plan=state.get("plan", {}),
            retrieved_chunks=state.get("retrieved_chunks", []),
            execution_result=state.get("execution_result"),
            web_search_results=state.get("web_search_results", []),
        )

    def build_user_prompt(self, agent_input: ReportInput) -> str:
        plan_desc = agent_input.plan.get("original_query", agent_input.query)

        evidence_text = ""
        for i, c in enumerate(agent_input.retrieved_chunks[:8], 1):
            if isinstance(c, dict):
                text = c.get("text", "")
                source = c.get("source_label", c.get("filename", c.get("doc_id", "")))
                evidence_text += f"\n#### 文献{i} [{source}]\n{text[:400]}\n"

        exec_text = ""
        if agent_input.execution_result:
            success = agent_input.execution_result.get("success", False)
            stdout = agent_input.execution_result.get("stdout", "")[:500]
            files = agent_input.execution_result.get("generated_files", [])
            exec_text = f"""
数据分析结果:
- 执行{'成功' if success else '失败'}
- 输出: {stdout}
- 生成文件: {', '.join(files) if files else '无'}
"""

        web_text = ""
        if agent_input.web_search_results:
            web_text = "\n联网搜索结果:\n"
            for i, r in enumerate(agent_input.web_search_results[:3], 1):
                if isinstance(r, dict):
                    web_text += f"\n#### 结果{i}: {r.get('title', '')}\n{r.get('snippet', '')[:300]}\n"

        return f"""用户问题: {agent_input.query}

任务描述: {plan_desc}

文献证据:{evidence_text}

{exec_text}

{web_text}

重要提示:
- 每条文献证据上方标注了来源文件和页码(如 [CRAG_paper.pdf，第 3 页])，请在报告中按来源引用。
- 如果文献证据来自学术论文 PDF，PDF 中的图表和表格可能未被文本解析，报告中说"图表/图片内容未解析"即可，不要编造定量数据。
- 只使用上面提供的文献证据，不要编造任何数据、统计数字、人名、文献引用。

请生成完整的 Markdown 格式研究报告。"""

    def parse_response(self, response: str) -> ReportOutput:
        return ReportOutput(report=response.strip(), report_ready=bool(response.strip()))

    def update_state(self, result: ReportOutput, state: dict) -> dict:
        return {
            "report": result.report,
            "report_ready": result.report_ready,
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