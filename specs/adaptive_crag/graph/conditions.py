"""
条件边判断函数：根据当前状态决定下一步走向。
"""


def after_grade(state: dict) -> str:
    """
    根据证据是否足够选择路径。

    返回:
        "sufficient" - 证据足够，进入分析规划
        "insufficient" - 证据不足，进入联网搜索
    """
    evidence_ready = state.get("evidence_ready", False)
    return "sufficient" if evidence_ready else "insufficient"


def after_analyze(state: dict) -> str:
    """
    根据是否需要生成代码选择路径。

    返回:
        "need_code" - 需要数据分析，进入代码生成
        "no_code" - 纯文献分析，直接生成报告
    """
    plan = state.get("plan", {})
    if isinstance(plan, dict):
        requires_code = plan.get("requires_code", False)
    else:
        requires_code = False

    return "need_code" if requires_code else "no_code"


def after_execute(state: dict) -> str:
    """
    根据执行结果选择路径。

    返回:
        "success" - 执行成功
        "retry" - 失败且重试次数未超限
        "give_up" - 失败且重试次数超限
    """
    execution_result = state.get("execution_result")
    if execution_result and isinstance(execution_result, dict):
        success = execution_result.get("success", False)
    else:
        success = False

    if success:
        return "success"

    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 3)

    if retry_count < max_retries:
        return "retry"

    return "give_up"
