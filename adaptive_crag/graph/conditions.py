"""
条件边判断函数：根据当前状态决定下一步走向。
"""

from langgraph.graph import END


def after_grade(state: dict) -> str:
    """
    根据证据是否足够选择路径。

    返回:
        "sufficient" - 证据足够，进入分析规划
        "insufficient" - 证据不足，进入联网搜索
    """
    if state.get("completed", False):
        return END
    evidence_ready = state.get("evidence_ready", False)
    if evidence_ready:
        print(f"[LOG] [Condition] after_grade → sufficient (evidence_ready=True)")
        return "sufficient"

    print(f"[LOG] [Condition] after_grade → insufficient (evidence_ready=False)")
    return "insufficient"


def after_analyze(state: dict) -> str:
    """
    根据 AnalyzerAgent 产出的 code_plan 判断是否需要代码生成。

    返回:
        "need_code" - code_plan 有内容，进入代码生成
        "no_code" - code_plan 为空，跳过代码执行
    """
    if state.get("completed", False):
        return END
    code_plan = state.get("code_plan", "")
    has_code = bool(code_plan and code_plan.strip())
    decision = "need_code" if has_code else "no_code"
    print(f"[LOG] [Condition] after_analyze → {decision} (code_plan={'有内容' if has_code else '空'})")
    return decision


def after_execute(state: dict) -> str:
    """
    根据执行结果选择路径。

    返回:
        "success" - 执行成功
        "retry" - 失败且重试次数未超限
        "give_up" - 失败且重试次数超限
    """
    if state.get("completed", False):
        return END
    execution_result = state.get("execution_result")
    if execution_result and isinstance(execution_result, dict):
        success = execution_result.get("success", False)
    else:
        success = False

    if success:
        print(f"[LOG] [Condition] after_execute → success")
        return "success"

    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 3)

    if retry_count < max_retries:
        print(f"[LOG] [Condition] after_execute → retry ({retry_count + 1}/{max_retries})")
        return "retry"

    print(f"[LOG] [Condition] after_execute → give_up (已重试 {retry_count} 次)")
    return "give_up"
